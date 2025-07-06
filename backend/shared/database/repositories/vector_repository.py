import functools
import uuid
from datetime import datetime
from typing import Any

import psycopg
import sqlalchemy
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.orm import Session

from services.transcriber.core.chunker import Chunker
from services.transcriber.core.embedder import Embedder
from shared.config.config import Settings, get_settings
from shared.database.repositories import TranscriptionRepository
from shared.logging.logger import get_logger
from shared.utils import normalize_json

logger = get_logger(__name__)
settings = get_settings()

# Application namespace for deterministic UUIDs
TRANSCRIPTION_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "openfing.transcription")


def generate_chunk_uuid(transcription_id: int, chunk_index: int) -> str:
    """
    Generate a deterministic UUID for a transcription chunk.

    This ensures:
    - Same transcription + chunk always gets same UUID
    - Clean upserts when re-transcribing
    - Easy calculation for deletion/updates
    """
    seed = f"transcription_{transcription_id}_chunk_{chunk_index}"
    return str(uuid.uuid5(TRANSCRIPTION_NAMESPACE, seed))


## TODO: should i call it ChunkRepository?
class VectorRepository:
    """
    Repository for vector store operations using deterministic UUIDs.
    """

    def __init__(
        self,
        config: Settings,
        db: Session,
        chunker: Chunker | None = None,
        embedder: Embedder | None = None,
    ):
        self.config = config
        self.db = db
        self.transcription_repo = TranscriptionRepository(db)

        self._embedder = embedder or Embedder()  # TODO: the service should inject these params?
        self._chunker = chunker or Chunker()

        logger.info("Vector repository initialized successfully")

    @functools.cached_property
    def _engine(self):
        return PGEngine.from_connection_string(url=self.config.DATABASE.URL)

    @functools.cached_property
    def _vector_store(self) -> PGVectorStore:
        table_name = self.config.DATABASE.VECTOR_STORE_COLLECTION

        try:
            self._engine.init_vectorstore_table(
                table_name=table_name,
                vector_size=self.config.EMBEDDINGS.DIMENSION,
                schema_name="rag",
                id_column="uuid",
                metadata_json_column="metadata",
            )
            logger.info(f"Created new vector store table: {table_name}")
        except sqlalchemy.exc.ProgrammingError as e:
            if isinstance(e.orig, psycopg.errors.DuplicateTable):
                logger.debug(
                    f"Skipping init_vectorstore_table {table_name=} already exists",
                )
            else:
                raise

        vector_store = PGVectorStore.create_sync(
            engine=self._engine,
            table_name=table_name,
            embedding_service=self._embedder.model,
            schema_name="rag",
            id_column="uuid",
            metadata_json_column="metadata",
        )

        logger.info(f"Initialized PGVectorStore with {table_name=}")
        return vector_store

    def upsert_transcription(self, transcription_id: int) -> list[str]:
        """
        Re-transcribing the same lesson will replace existing chunks.
        """
        transcription = self.transcription_repo.get_by_id_with_course_and_lesson(
            transcription_id,
        )
        if not transcription:
            raise ValueError(f"Transcription {transcription_id} not found")

        chunks = self._chunker.chunk(
            content=transcription.content,
            # TODO:
            # - start timestamp in lesson audio (should be calculated after chunking
            #  using transcription object metadata)
            # - end timestamp in lesson audio
            transcription_metadata=transcription.transcription_metadata
            | {
                "transcription_id": transcription.id,
                "course_code": transcription.lesson.course.code,
                "lesson_id": transcription.lesson.id,
            },
        )

        documents, ids = [], []

        for chunk in chunks:
            chunk_uuid = generate_chunk_uuid(
                transcription_id,
                chunk["metadata"]["chunk_index"],
            )

            documents.append(
                Document(page_content=chunk["text"], metadata=chunk["metadata"]),
            )
            ids.append(chunk_uuid)

        # Add to vector store (will upsert if UUIDs already exist)
        added_ids = self._vector_store.add_documents(documents, ids=ids)

        self.transcription_repo.update_metadata(
            transcription_id,
            {
                "vectorized": True,
                "vectorized_at": datetime.now().isoformat(),
                **normalize_json(self._embedder._model_info(), prefix="embedder"),
            },
        )

        logger.info(f"Ingested {transcription_id=} as {len(added_ids)} chunks")
        return added_ids

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
        course_codes: list[str] | None = None,
        lesson_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform similarity search with optional filters."""

        search_filter = filter or {}
        if course_codes:
            search_filter["course_code"] = {"$in": course_codes}
        if lesson_ids:
            search_filter["lesson_id"] = {"$in": lesson_ids}

        docs_with_scores = self._vector_store.similarity_search_with_score(
            query,
            k=k,
            filter=search_filter if search_filter else None,
        )

        results = []
        for doc, score in docs_with_scores:
            results.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "lesson_id": doc.metadata.get("lesson_id"),
                    "course_code": doc.metadata.get("course_code"),
                    "chunk_index": doc.metadata.get("chunk_index"),
                    "vector_uuid": doc.metadata.get("vector_uuid"),
                },
            )

        return results

    def get_retriever(
        self,
        k: int = 4,
        search_type: str = "similarity",
        filter: dict[str, Any] | None = None,
    ) -> BaseRetriever:
        search_kwargs: dict[str, Any] = {"k": k}
        if filter:
            search_kwargs["filter"] = filter

        return self._vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    def get_collection_info(self) -> dict[str, Any]:
        """Get information about the vector store collection."""
        conn_parts = self.config.DATABASE.URL.split("@")
        host_info = conn_parts[1].split("/")[0] if len(conn_parts) > 1 else "unknown"

        return {
            "collection_name": self.config.VECTOR_STORE_COLLECTION,
            "connection_host": host_info,
            "engine_type": type(self._vector_store).__name__,
            "uuid_strategy": f"{__name__}.generate_chunk_uuid",
        }

    def delete_by_transcription(self, transcription_id: int) -> bool:
        """Delete all chunks for a transcription"""
        try:
            transcription = self.transcription_repo.get_by_id(transcription_id)
            if not transcription:
                logger.debug(f"Transcription {transcription_id} not found")
                return True

            # TODO: improve this, dont guess, query DB. probably storing the transcription id in the chunk metadata
            # Calculate all possible chunk UUIDs for this transcription
            # We need to estimate max chunks or query the vector store
            max_chunks = 100  # Reasonable upper bound
            uuids_to_delete = []

            for chunk_index in range(max_chunks):
                chunk_uuid = generate_chunk_uuid(transcription_id, chunk_index)
                uuids_to_delete.append(chunk_uuid)

            # Delete from vector store (non-existent UUIDs are ignored)
            self._vector_store.delete(ids=uuids_to_delete)
            self.transcription_repo.mark_as_not_vectorized(transcription_id)

            logger.info(f"Deleted vectors for transcription {transcription_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error deleting vectors for transcription {transcription_id}: {e}",
            )
            return False

    def delete_by_lesson(self, lesson_id: int) -> bool:
        """Delete all vectors for a lesson."""
        try:
            transcriptions = self.transcription_repo.get_by_lesson(lesson_id)

            for transcription in transcriptions:
                self.delete_by_transcription(transcription.id)

            logger.info(f"Deleted vectors for lesson {lesson_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting vectors for lesson {lesson_id}: {e}")
            return False

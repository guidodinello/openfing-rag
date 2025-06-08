import os
import uuid
from datetime import datetime
from typing import Any

import psycopg
import sqlalchemy
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.orm import Session

from shared.database.repositories.transcription_repository import TranscriptionRepository
from shared.logging.logger import get_logger

logger = get_logger(__name__)

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


class VectorRepository:
    """
    Repository for vector store operations using deterministic UUIDs.
    """

    def __init__(self, config, db: Session):
        self.config = config
        self.db = db
        self.transcription_repo = TranscriptionRepository(db)

        self.__embeddings = None
        self.__engine = None
        self.__vector_store = None

        logger.info("Vector repository initialized successfully")

    @property
    def _embeddings(self):
        """Lazy load embeddings model."""
        if self.__embeddings is None:
            self.__embeddings = self._create_embeddings()
        return self.__embeddings

    @property
    def _engine(self):
        """Lazy load PG engine."""
        if self.__engine is None:
            self.__engine = PGEngine.from_connection_string(url=self.config.DATABASE.URL)
        return self.__engine

    @property
    def _vector_store(self):
        """Lazy load vector store."""
        if self.__vector_store is None:
            self.__vector_store = self._create_vector_store()
        return self.__vector_store

    def _create_embeddings(self):
        """Create and configure embeddings model."""
        cache_folder = self.config.EMBEDDINGS.CACHE_DIR
        os.makedirs(cache_folder, exist_ok=True)

        logger.debug("VectorRepository._create_embeddings")
        return HuggingFaceEmbeddings(
            model_name=self.config.EMBEDDINGS.MODEL,
            model_kwargs={"device": self.config.EMBEDDINGS.DEVICE},
            cache_folder=cache_folder,
            encode_kwargs={"normalize_embeddings": True},
        )

    def _create_vector_store(self) -> PGVectorStore:
        """Create the new PGVectorStore."""
        table_name = self.config.VECTOR_STORE_COLLECTION

        # Handle error if table already exists
        try:
            self._engine.init_vectorstore_table(
                table_name=table_name,
                vector_size=self.config.EMBEDDINGS.DIMENSION,
            )
            logger.info(f"Created new vector store table: {table_name}")
        except (sqlalchemy.exc.ProgrammingError, psycopg.errors.DuplicateTable):
            logger.debug(f"Skipping init_vectorstore_table {table_name=} already exists")
        except Exception as e:
            raise logger.error(f"{e=}") from e

        vector_store = PGVectorStore.create_sync(
            engine=self._engine,
            table_name=table_name,
            embedding_service=self._embeddings,
        )

        logger.info(f"Initialized PGVectorStore with table: {table_name}")
        return vector_store

    def ingest_transcription(self, transcription_id: int) -> list[str]:
        """
        Ingest a transcription using deterministic UUIDs.

        Re-transcribing the same lesson will cleanly replace existing chunks.
        """
        # Get transcription from database
        transcription = self.transcription_repo.get_by_id(transcription_id)
        if not transcription:
            raise ValueError(f"Transcription {transcription_id} not found")

        # Chunk the content
        chunks = self._chunk_content(
            content=transcription.content,
            transcription_id=transcription.id,
            # TODO: pensar mejor esto, la metadata del chunk deberia tener:
            # MINIMO
            # - start
            # -  end
            # - transcription_id
            # CAPAZ (parametros de la chunking strategy)
            # - chunking_strategy
            # - chunk_size
            # - overlap
            metadata=transcription.transcription_metadata or {},
        )

        documents, ids = [], []

        for chunk in chunks:
            chunk_uuid = generate_chunk_uuid(transcription_id, chunk["metadata"]["chunk_index"])

            documents.append(Document(page_content=chunk["text"], metadata=chunk["metadata"]))
            ids.append(chunk_uuid)

        # Add to vector store (will upsert if UUIDs already exist)
        added_ids = self._vector_store.add_documents(documents, ids=ids)

        embedding_metadata = {
            "vectorized": True,
            "embedding_model": self.__embeddings.model_name,
            "vectorized_at": datetime.now().isoformat(),
        }

        self.transcription_repo.update_vectorization_metadata(transcription_id, embedding_metadata)

        logger.info(f"Ingested transcription {transcription_id} as {len(added_ids)} chunks with deterministic UUIDs")
        return added_ids

    def delete_by_transcription(self, transcription_id: int) -> bool:
        """Delete all chunks for a transcription using calculated UUIDs."""
        try:
            # Get transcription to know how many chunks it had
            transcription = self.transcription_repo.get_by_id(transcription_id)
            if not transcription:
                logger.warning(f"Transcription {transcription_id} not found")
                return True

            # TODO: improve this, dont guess, query DB
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
            logger.error(f"Error deleting vectors for transcription {transcription_id}: {e}")
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

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
        course_codes: list[str] | None = None,
        lesson_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform similarity search with optional filters."""
        # Build filter from parameters
        search_filter = filter or {}

        if course_codes:
            search_filter["course_code"] = {"$in": course_codes}

        if lesson_ids:
            search_filter["lesson_id"] = {"$in": lesson_ids}

        # Perform search
        docs_with_scores = self._vector_store.similarity_search_with_score(
            query,
            k=k,
            filter=search_filter if search_filter else None,
        )

        # Convert to our format
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
        """Get a retriever for RAG applications."""
        search_kwargs = {"k": k}
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
            "embedding_model": self.config.EMBEDDINGS.MODEL,
            "embedding_device": self.config.EMBEDDINGS.DEVICE,
            "vector_dimension": self.config.EMBEDDINGS.DIMENSION,
            "engine_type": type(self._vector_store).__name__,
            "uuid_strategy": "deterministic",
        }

    def _chunk_content(
        self,
        content: str,
        transcription_id: int,
        metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Chunk transcription content for vector storage."""
        chunk_size = 1000
        overlap = 200
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]

            # Ensure we don't cut off mid-word
            if end < len(content):
                last_space = chunk_text.rfind(" ")
                if last_space > chunk_size - 100:
                    end = start + last_space
                    chunk_text = content[start:end]

            chunk_metadata = {
                **metadata,
                "transcription_id": transcription_id,
                "chunk_index": chunk_index,
                "start_pos": start,
                "end_pos": end,
                "chunk_strategy": "simple_overlap",
                "chunk_size": chunk_size,
                "overlap": overlap,
            }

            chunks.append(
                {
                    "text": chunk_text.strip(),
                    "metadata": chunk_metadata,
                },
            )

            start = end - overlap
            chunk_index += 1

        return chunks

import functools
from datetime import datetime
from enum import StrEnum
from typing import Any

import psycopg
import sqlalchemy
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.orm import Session

from shared.config import get_settings
from shared.database.repositories import TranscriptionRepository
from shared.enums import WhisperModelSize
from shared.file_utils import TranscriptionFileUtils
from shared.logging import get_logger
from shared.utils import normalize_json
from shared.vectors import ChunkId
from shared.vectors.chunking import generate_chunk_uuid
from shared.vectors.chunking.protocol import ChunkerProtocol
from shared.vectors.embedding.protocol import EmbedderProtocol

logger = get_logger(__name__)
settings = get_settings()


class MetadataColumn(StrEnum):
    """Enum for metadata column names to ensure type safety."""

    LESSON_ID = "lesson_id"
    COURSE_ID = "course_id"
    TRANSCRIPTION_ID = "transcription_id"


class VectorRepository:
    """
    Repository for vector store operations using deterministic UUIDs.
    """

    def __init__(
        self,
        db: Session,
        chunker: ChunkerProtocol,
        embedder: EmbedderProtocol,
        transcription_repo: TranscriptionRepository,
    ):
        self.db = db
        self.transcription_repo = transcription_repo
        self._embedder = embedder
        self._chunker = chunker

        logger.info("Vector repository initialized successfully")

    @functools.cached_property
    def _engine(self):
        return PGEngine.from_connection_string(url=settings.DATABASE.URL)

    @functools.cached_property
    def _vector_store(self) -> PGVectorStore:
        table_name = settings.DATABASE.VECTOR_STORE_COLLECTION

        try:
            self._engine.init_vectorstore_table(
                table_name=table_name,
                vector_size=settings.EMBEDDINGS.DIMENSION,
                schema_name="rag",
                id_column="uuid",
                metadata_columns=[
                    {"name": MetadataColumn.LESSON_ID.value, "data_type": "INTEGER", "nullable": False},
                    {"name": MetadataColumn.COURSE_ID.value, "data_type": "INTEGER", "nullable": False},
                    {"name": MetadataColumn.TRANSCRIPTION_ID.value, "data_type": "INTEGER", "nullable": False},
                ],
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
            metadata_columns=[
                MetadataColumn.LESSON_ID.value,
                MetadataColumn.COURSE_ID.value,
                MetadataColumn.TRANSCRIPTION_ID.value,
            ],
            metadata_json_column="metadata",
        )

        logger.info(f"Initialized PGVectorStore with {table_name=}")
        return vector_store

    def upsert_transcription(self, transcription_id: int) -> list[ChunkId]:
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
            ## agrega los segments que dsps son usados por el chunker
            transcription_metadata=self._get_enhanced_transcription_metadata(transcription),
        )

        documents, ids = [], []

        for chunk in chunks:
            chunk_uuid = generate_chunk_uuid(
                transcription_id,
                chunk.metadata["chunk_index"],
            )

            del chunk.metadata["segments"]

            documents.append(
                Document(
                    page_content=chunk.text,
                    metadata={
                        **chunk.metadata,
                        MetadataColumn.TRANSCRIPTION_ID.value: transcription.id,
                        MetadataColumn.LESSON_ID.value: transcription.lesson.id,
                        MetadataColumn.COURSE_ID.value: transcription.lesson.course.id,
                    },
                ),
            )
            ids.append(chunk_uuid)

        # Add to vector store (will upsert if UUIDs already exist)
        added_ids = self._vector_store.add_documents(documents, ids=ids)

        self.transcription_repo.update_metadata(
            transcription_id,
            {
                "vectorized": True,
                "vectorized_at": datetime.now().isoformat(),
                **normalize_json(self._embedder.model_info(), prefix="embedder"),
            },
        )

        timing_accuracy = chunks[0].metadata["timing_accuracy"] if chunks else "unknown"
        logger.info(
            f"Ingested {transcription_id=} as {len(added_ids)} chunks with {timing_accuracy} timing",
        )
        return added_ids

    def _get_enhanced_transcription_metadata(self, transcription) -> dict[str, Any]:
        """
        Get transcription metadata enhanced with segments from original file.

        This provides the best of both worlds:
        - Database metadata for basic info
        - Original file segments for accurate timestamps
        """
        base_metadata = transcription.transcription_metadata

        # Try to load segments from the original transcription file
        segments = self._load_segments_from_file(transcription)

        if segments:
            base_metadata["segments"] = segments
            logger.debug(
                f"Loaded {len(segments)} segments from original file for transcription {transcription.id}",
            )
        else:
            logger.warning(
                f"No segments found for transcription {transcription.id} - will use proportional timing",
            )

        return base_metadata

    def _load_segments_from_file(self, transcription) -> list[dict] | None:
        """
        Load segments from the original transcription JSON file.

        This allows us to get precise timing without storing large segment data in the database.
        """
        try:
            model_size_str = transcription.transcription_metadata.get(
                "transcriber_model_size",
            )
            if not model_size_str:
                logger.warning(
                    f"No model size found in transcription {transcription.id} metadata",
                )
                return None
            model_size = WhisperModelSize(model_size_str)

            course_code = transcription.lesson.course.code
            lesson_number = transcription.lesson.number

            transcription_data = TranscriptionFileUtils.load_transcription(
                course_code,
                lesson_number,
                model_size,
                ## TODO: pass suffix?
            )

            if transcription_data and "segments" in transcription_data:
                return transcription_data["segments"]

            logger.debug(
                f"No segments in original file for {course_code} lesson {lesson_number}",
            )
            return None

        except Exception as e:
            logger.error(
                f"Error loading segments from file for transcription {transcription.id}: {e}",
            )
            return None

    def similarity_search(
        self,
        query: str,
        courses_ids: list[int],
        lessons_ids: list[int],
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform similarity search with optional filters."""
        search_filter = filter or {}
        if courses_ids:
            search_filter[MetadataColumn.COURSE_ID.value] = {"$in": courses_ids}
        if lessons_ids:
            search_filter[MetadataColumn.LESSON_ID.value] = {"$in": lessons_ids}

        logger.debug(f"Similarity Search {search_filter=}")

        docs_with_scores = self._vector_store.similarity_search_with_score(
            query,
            k=k,
            filter=search_filter if search_filter else None,
        )

        results = []
        for doc, score in docs_with_scores:
            results.append(
                {
                    "id": doc.id,
                    "content": doc.page_content,
                    "score": float(score),
                    "metadata": doc.metadata,
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
        conn_parts = settings.DATABASE.URL.split("@")
        host_info = conn_parts[1].split("/")[0] if len(conn_parts) > 1 else "unknown"

        return {
            "collection_name": settings.VECTOR_STORE_COLLECTION,
            "connection_host": host_info,
            "engine_type": type(self._vector_store).__name__,
            "uuid_strategy": f"{__name__}.{generate_chunk_uuid.__name__}",
        }

    def delete_by_transcription(self, transcription_id: int) -> int:
        """Delete all chunks for a transcription"""
        transcription = self.transcription_repo.get_by_id(transcription_id)
        if not transcription:
            logger.warning(f"Transcription {transcription_id=} not found")
            return 0

        deleted_count = self._vector_store.delete(filter={MetadataColumn.TRANSCRIPTION_ID.value: transcription_id})
        self.transcription_repo.mark_as_not_vectorized([transcription_id])

        logger.info(f"Deleted vectors for transcription {transcription_id}")
        return deleted_count

    def delete_by_lesson(self, lesson_id: int) -> int:
        """Delete all vectors for a lesson."""
        transcriptions = self.transcription_repo.get_by_lesson_id(lesson_id)
        if not transcriptions:
            logger.warning(f"Transcriptions not found for {lesson_id=}")
            return 0

        deleted_count = self._vector_store.delete(filter={MetadataColumn.LESSON_ID.value: lesson_id})
        self.transcription_repo.mark_as_not_vectorized(tr.id for tr in transcriptions)

        logger.info(f"Deleted vectors for lesson {lesson_id}")
        return deleted_count

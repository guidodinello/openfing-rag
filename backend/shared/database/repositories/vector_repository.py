from typing import Any

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.orm import Session

from shared.database.repositories.transcription_repository import TranscriptionRepository
from shared.logging.logger import get_logger

logger = get_logger(__name__)


class VectorRepository:
    """
    Repository for vector store operations.
    Uses the new PGVectorStore instead of deprecated PGVector.
    https://github.com/langchain-ai/langchain-postgres/blob/main/README.md#vectorstore
    """

    def __init__(self, config, db: Session):
        self.config = config
        self.db = db
        self.transcription_repo = TranscriptionRepository(db)

        # Initialize embeddings and vector store
        self._embeddings = self._create_embeddings()
        self._engine = self._create_pg_engine()
        self._vector_store = self._create_vector_store()

        logger.info("Vector repository initialized successfully")

    def _create_embeddings(self):
        """Create and configure embeddings model."""
        cache_folder = self.config.EMBEDDINGS.CACHE_DIR
        if cache_folder:
            import os

            os.makedirs(cache_folder, exist_ok=True)

        return HuggingFaceEmbeddings(
            model_name=self.config.EMBEDDINGS.MODEL,
            model_kwargs={"device": self.config.EMBEDDINGS.DEVICE},
            cache_folder=cache_folder,
            encode_kwargs={"normalize_embeddings": True},
        )

    def _create_pg_engine(self) -> PGEngine:
        """Create PGEngine for the new PGVectorStore."""
        # Convert connection string for PGVectorStore
        conn_string = self.config.DATABASE.URL
        if "postgresql+psycopg://" in conn_string:
            # PGVectorStore prefers psycopg3 format
            conn_string = conn_string.replace("postgresql+psycopg://", "postgresql+psycopg://")
        elif "postgresql+asyncpg://" in conn_string:
            conn_string = conn_string.replace("postgresql+asyncpg://", "postgresql+psycopg://")

        return PGEngine.from_connection_string(url=conn_string)

    def _create_vector_store(self) -> PGVectorStore:
        """Create the new PGVectorStore."""
        # Initialize the table for vector storage
        table_name = self.config.VECTOR_STORE_COLLECTION

        # Create table if it doesn't exist
        self._engine.init_vectorstore_table(
            table_name=table_name,
            vector_size=self.config.EMBEDDINGS.DIMENSION,
        )

        # Create vector store instance
        vector_store = PGVectorStore.create_sync(
            engine=self._engine,
            table_name=table_name,
            embedding_service=self._embeddings,
        )

        logger.info(f"Initialized PGVectorStore with table: {table_name}")
        return vector_store

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
            "engine_type": "PGVectorStore",
        }

    def ingest_transcription(self, transcription_id: int) -> list[str]:
        """
        Ingest a transcription from the database into the vector store.

        Args:
            transcription_id: ID of the transcription to ingest

        Returns:
            List of added document IDs
        """
        # Get transcription from database using repository
        transcription = self.transcription_repo.get_by_id(transcription_id)
        if not transcription:
            raise ValueError(f"Transcription {transcription_id} not found")

        # Chunk the transcription content
        chunks = self._chunk_content(
            content=transcription.content,
            lesson_id=transcription.lesson_id,
            transcription_id=transcription.id,
            metadata=transcription.transcription_metadata or {},
        )

        # Convert to LangChain documents
        documents = [Document(page_content=chunk["text"], metadata=chunk["metadata"]) for chunk in chunks]

        # Generate IDs for documents
        ids = [chunk["metadata"]["id"] for chunk in chunks]

        # Add to vector store
        added_ids = self._vector_store.add_documents(documents, ids=ids)

        # Mark transcription as vectorized in database
        self.transcription_repo.mark_as_vectorized(transcription_id)

        logger.info(f"Ingested transcription {transcription_id} as {len(added_ids)} chunks")
        return added_ids

    def ingest_lesson_transcriptions(self, lesson_id: int) -> list[str]:
        """
        Ingest all transcriptions for a lesson.

        Args:
            lesson_id: ID of the lesson

        Returns:
            List of all added document IDs
        """
        transcriptions = self.transcription_repo.get_by_lesson_id(lesson_id)
        all_ids = []

        for transcription in transcriptions:
            if not transcription.is_vectorized:
                ids = self.ingest_transcription(transcription.id)
                all_ids.extend(ids)

        return all_ids

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
        course_codes: list[str] | None = None,
        lesson_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform similarity search with optional filters.

        Args:
            query: Search query
            k: Number of results
            filter: Custom filter dict
            course_codes: Filter by course codes
            lesson_ids: Filter by specific lesson IDs

        Returns:
            List of search results with documents and scores
        """
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

    def delete_by_lesson(self, lesson_id: int) -> bool:
        """
        Delete all vector chunks for a specific lesson.

        Args:
            lesson_id: ID of the lesson

        Returns:
            True if deletion was successful
        """
        try:
            # Delete from vector store
            filter_criteria = {"lesson_id": {"$eq": lesson_id}}
            self._vector_store.delete(filter=filter_criteria)

            # Mark transcriptions as not vectorized
            transcriptions = self.transcription_repo.get_by_lesson_id(lesson_id)
            for transcription in transcriptions:
                self.transcription_repo.mark_as_not_vectorized(transcription.id)

            logger.info(f"Deleted vectors for lesson {lesson_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting vectors for lesson {lesson_id}: {e}")
            return False

    def delete_by_transcription(self, transcription_id: int) -> bool:
        """Delete all chunks for a specific transcription."""
        try:
            filter_criteria = {"transcription_id": {"$eq": transcription_id}}
            self._vector_store.delete(filter=filter_criteria)

            # Mark as not vectorized
            self.transcription_repo.mark_as_not_vectorized(transcription_id)

            logger.info(f"Deleted vectors for transcription {transcription_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting vectors for transcription {transcription_id}: {e}")
            return False

    def _chunk_content(
        self,
        content: str,
        lesson_id: int,
        transcription_id: int,
        metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Chunk transcription content for vector storage.

        Args:
            content: Text content to chunk
            lesson_id: ID of the lesson
            transcription_id: ID of the transcription
            metadata: Additional metadata

        Returns:
            List of chunks with text and metadata
        """
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

            # Get course code from lesson (through repository)
            from shared.database.repositories.lesson_repository import LessonRepository

            lesson_repo = LessonRepository(self.db)
            lesson = lesson_repo.get_by_id(lesson_id)
            course_code = lesson.course.code if lesson and lesson.course else "unknown"

            chunk_metadata = {
                **metadata,
                "lesson_id": lesson_id,
                "transcription_id": transcription_id,
                "course_code": course_code,
                "chunk_index": chunk_index,
                "start_pos": start,
                "end_pos": end,
                "id": f"transcription_{transcription_id}_chunk_{chunk_index}",
                "vectorized_at": "now",  # Add timestamp
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

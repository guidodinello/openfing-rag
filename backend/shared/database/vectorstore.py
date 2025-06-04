import os
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

from shared.logging.logger import get_logger

from .data_models import SearchResult

logger = get_logger(__name__)


class VectorStore:
    def __init__(self, config):
        """
        Initialize the vector store with the provided configuration.

        Args:
            config: Configuration for the vector store
        """
        self.config = config
        self._embeddings = self._create_embeddings()
        self._vector_store = self._create_vector_store()
        logger.info("Vector store initialized successfully")

    def _create_embeddings(self) -> Embeddings:
        """Create and configure embeddings model."""
        cache_folder = self.config.EMBEDDINGS.CACHE_DIR
        if cache_folder:
            os.makedirs(cache_folder, exist_ok=True)

        return HuggingFaceEmbeddings(
            model_name=self.config.EMBEDDINGS.MODEL,
            model_kwargs={"device": self.config.EMBEDDINGS.DEVICE},
            cache_folder=cache_folder,
            encode_kwargs={"normalize_embeddings": True},
        )

    def _create_vector_store(self) -> PGVector:
        """Create the PGVector store using langchain-postgres."""
        # Ensure connection string uses the right driver for langchain-postgres
        conn_string = self.config.DATABASE.URL
        if "postgresql+psycopg2" in conn_string:
            conn_string = conn_string.replace(
                "postgresql+psycopg2",
                "postgresql+psycopg",
            )
        elif "postgresql+asyncpg" in conn_string:
            conn_string = conn_string.replace(
                "postgresql+asyncpg",
                "postgresql+psycopg",
            )

        vector_store = PGVector(
            embeddings=self._embeddings,
            collection_name=self.config.VECTOR_STORE_COLLECTION,
            connection=conn_string,
            use_jsonb=True,
        )

        logger.info(f"Initialized PGVector store with collection: {self.config.VECTOR_STORE_COLLECTION}")
        return vector_store

    def get_collection_info(self) -> dict[str, Any]:
        """
        Get information about the vector store collection.

        Returns:
            Dictionary with collection information
        """
        # Extract host from connection string for safe display (no credentials)
        conn_parts = self.config.DATABASE.URL.split("@")
        host_info = conn_parts[1].split("/")[0] if len(conn_parts) > 1 else "unknown"

        return {
            "collection_name": self.config.VECTOR_STORE_COLLECTION,
            "connection_host": host_info,
            "embedding_model": self.config.EMBEDDINGS.MODEL,
            "embedding_device": self.config.EMBEDDINGS.DEVICE,
            "use_jsonb": True,
        }

    def ingest_chunks(self, chunks: list[dict[str, Any]]) -> list[str]:
        """
        Ingest text chunks into the vector store.

        Args:
            chunks: List of dictionaries, each with "text" and "metadata" keys

        Returns:
            List of added document IDs
        """
        # Convert chunks to Documents
        documents = [
            Document(
                page_content=chunk["text"],
                metadata=chunk["metadata"],
            )
            for chunk in chunks
        ]

        # Generate IDs if not provided in metadata
        ids = []
        for i, chunk in enumerate(chunks):
            if "id" in chunk["metadata"]:
                ids.append(str(chunk["metadata"]["id"]))
            else:
                # Generate ID based on lesson_id and chunk index
                lesson_id = chunk["metadata"].get("lesson_id", "unknown")
                ids.append(f"lesson_{lesson_id}_chunk_{i}")

        # Add documents to vector store
        added_ids = self._vector_store.add_documents(documents, ids=ids)
        logger.info(f"Added {len(added_ids)} documents to vector store")

        return added_ids

    def get_retriever(
        self,
        k: int = 4,
        search_type: str = "similarity",
        filter: dict[str, Any] | None = None,
    ) -> BaseRetriever:
        """
        Get a retriever for searching the vector store.

        Args:
            k: Number of results to return
            search_type: Type of search to perform (similarity, mmr, similarity_score_threshold)
            filter: Optional filter criteria using PGVector filter syntax

        Returns:
            A retriever for searching the vector store
        """
        search_kwargs = {"k": k}
        if filter:
            search_kwargs["filter"] = filter

        return self._vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Perform similarity search on the vector store.

        Args:
            query: Query string to search for
            k: Number of results to return
            filter: Optional filter criteria using PGVector filter syntax
                   Examples:
                   - {"lesson_id": {"$eq": 123}}
                   - {"course_code": {"$in": ["PROG101", "MATH202"]}}
                   - {"$and": [{"lesson_id": {"$gt": 10}}, {"topic": {"$eq": "functions"}}]}

        Returns:
            List of search results with documents and scores
        """
        docs_with_scores = self._vector_store.similarity_search_with_score(
            query,
            k=k,
            filter=filter,
        )

        # Convert to SearchResult objects
        results = [SearchResult(document=doc, score=float(score)) for doc, score in docs_with_scores]

        return results

    def delete_by_ids(self, ids: list[str]) -> bool:
        """
        Delete documents by their IDs.

        Args:
            ids: List of document IDs to delete

        Returns:
            True if deletion was successful
        """
        try:
            self._vector_store.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from vector store")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False

    def delete_by_filter(self, filter: dict[str, Any]) -> bool:
        """
        Delete documents matching a filter.

        Args:
            filter: Filter criteria to match documents for deletion

        Returns:
            True if deletion was successful
        """
        try:
            # First find matching documents to get their IDs
            docs = self._vector_store.similarity_search(
                query="",  # Empty query to get all matching filter
                k=10000,  # Large number to get all matches
                filter=filter,
            )

            if docs:
                # Extract IDs from metadata if available
                ids_to_delete = []
                for doc in docs:
                    if "id" in doc.metadata:
                        ids_to_delete.append(str(doc.metadata["id"]))

                if ids_to_delete:
                    self._vector_store.delete(ids=ids_to_delete)
                    logger.info(f"Deleted {len(ids_to_delete)} documents matching filter")
                    return True

            return True  # No documents matched, consider this success
        except Exception as e:
            logger.error(f"Error deleting documents by filter: {str(e)}")
            return False

    def process_transcription(
        self,
        lesson_id: int,
        content: str,
        metadata: dict[str, Any],
    ) -> list[str]:
        """
        Process a transcription by chunking it and adding to vector store.

        Args:
            lesson_id: ID of the lesson
            content: Transcription content
            metadata: Additional metadata

        Returns:
            List of added document IDs
        """
        # Simple chunking strategy - you might want to use more sophisticated chunking
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
                if last_space > chunk_size - 100:  # Only adjust if space is near the end
                    end = start + last_space
                    chunk_text = content[start:end]

            chunk_metadata = {
                **metadata,
                "lesson_id": lesson_id,
                "chunk_index": chunk_index,
                "start_pos": start,
                "end_pos": end,
                "id": f"lesson_{lesson_id}_chunk_{chunk_index}",
            }

            chunks.append(
                {
                    "text": chunk_text.strip(),
                    "metadata": chunk_metadata,
                },
            )

            start = end - overlap
            chunk_index += 1

        # Add chunks to vector store
        return self.ingest_chunks(chunks)

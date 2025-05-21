from __future__ import annotations

import logging
import os

from data_models import VectorStoreConfig
from vectorstore import VectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_database_url() -> str:
    """Create PostgreSQL connection URL from environment variables."""
    user = os.getenv("DATABASE_USER", "psql_usr")
    password = os.getenv("DATABASE_PASSWORD", "psql_pass")
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    database = os.getenv("DATABASE_DB", "psql_db")

    # Use the newer psycopg driver for better performance
    # Convert from psycopg to psycopg2 for compatibility with langchain-postgres
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def create_manager_from_env() -> VectorStore:
    """Create manager instance from environment variables with validation."""
    database_url = create_database_url()

    config = VectorStoreConfig(
        connection_string=database_url,
        collection_name=os.getenv("VECTOR_STORE_COLLECTION", "rag_chunks"),
        embedding_model=os.getenv(
            "EMBEDDINGS_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        embedding_device=os.getenv("EMBEDDING_DEVICE", "cpu"),
        cache_folder=os.getenv("CACHE_FOLDER", ".cache/embeddings"),
    )

    return VectorStore(config)


def example_usage():
    manager = create_manager_from_env()

    chunks = [
        {
            "text": "Introduction to machine learning concepts and basic principles",
            "metadata": {
                "lesson_id": 1,
                "start_time": 0,
                "end_time": 300,
                "topic": "introduction",
                "difficulty": "beginner",
            },
        },
        {
            "text": "Deep learning and neural networks architecture overview",
            "metadata": {
                "lesson_id": 1,
                "start_time": 300,
                "end_time": 600,
                "topic": "deep_learning",
                "difficulty": "intermediate",
            },
        },
        {
            "text": "Advanced optimization techniques for neural networks",
            "metadata": {
                "lesson_id": 1,
                "start_time": 600,
                "end_time": 900,
                "topic": "optimization",
                "difficulty": "advanced",
            },
        },
    ]
    chunk_ids = manager.ingest_chunks(chunks)
    logger.info(f"Ingested {len(chunks)} chunks with IDs: {chunk_ids}")

    retriever = manager.get_retriever(k=2, search_type="similarity")

    results = retriever.invoke("Deep learning and neural")
    logger.info(f"Search results: {results}")

    logger.info(f"Collection info: {manager.get_collection_info()}")


if __name__ == "__main__":
    example_usage()

from datetime import datetime
from typing import Any

from app.core.config import Settings
from app.models.rag.chunk import Chunk
from app.utils.logger import get_logger
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

# TODO: update type hints
# TODO: clean vector store instantiation. i think im creating one for pgvector and one for whisper ingest
# TODO: clean embeddings instantiation
# TODO: clean async session and engines instantiation
# TODO; see differences between async version and sync of pgvector.


class ChunkMetadata(BaseModel):
    """Metadata for a chunk of text."""

    lesson_id: int
    start_time: int
    end_time: int
    created_at: datetime
    metadata: dict


class VectorStore:
    """Vector store for similarity search using PostgreSQL and sentence transformers."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        embedding_model: None | str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the vector store.

        Args:
            session: AsyncSession for database operations
            settings: Application settings
            embedding_model: Name of the sentence transformer model to use
        """
        self.session = session
        self.settings = settings
        # TODO: use dependency injection
        self._encoder = HuggingFaceEmbeddings(model_name=settings.EMBEDDINGS.MODEL)
        self._vector_store = self._create_vector_store()
        logger.info(f"Initialized VectorStore with model: {embedding_model}")

    def _create_vector_store(self) -> PGVector:
        """
        Initialize PGVector with configuration from settings.

        Returns:
            PGVector instance

        Raises:
            Exception: If initialization fails
        """
        try:
            return PGVector(
                collection_name=self.settings.VECTOR_STORE_COLLECTION,
                connection=self.settings.DATABASE.URL,
                embeddings=self._encoder,
                use_jsonb=True,
            )
        except Exception as e:
            logger.error(f"Failed to initialize PGVector: {str(e)}")
            raise

    async def similarity_search(
        self,
        query: str,
        k: int = 3,
        score_threshold: float = 0.7,
        filter_metadata: None | dict[str, Any] = None,
    ) -> list[Chunk]:
        """
        Perform similarity search with optional metadata filtering.

        Args:
            query: The search query
            k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            filter_metadata: Optional metadata filters

        Returns:
            list of Chunk objects ordered by relevance
        """
        try:
            # Construct metadata filters if provided
            filter_conditions = {}
            if filter_metadata:
                filter_conditions = {
                    f"metadata->>{key}": value for key, value in filter_metadata.items()
                }

            # Perform the search
            # TODO: shouldnt access _vector_store probably
            logger.info(
                f"Running similarity search for {query=} with {filter_conditions=}"
            )
            results: list[tuple[Any, float]] = (
                self._vector_store.similarity_search_with_score(
                    query,
                    k=k,
                    filter=filter_conditions if filter_conditions else None,
                )
            )

            # TODO: use a retriever
            score_threshold = 0
            chunks = [result[0] for result in results if result[1] >= score_threshold]

            logger.info(
                f"Found {len(chunks)} relevant chunks with threshold {score_threshold}"
            )
            return chunks

        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise

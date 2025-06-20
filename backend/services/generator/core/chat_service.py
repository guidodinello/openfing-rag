from sqlalchemy.orm import Session

from services.generator.core.llm_service import LLMService
from services.generator.schemas.domain import ChatResult, RetrievedChunk, SearchContext
from shared.database.repositories.vector_repository import VectorRepository
from shared.logging.logger import get_logger

logger = get_logger(__name__)


class ChatService:
    """Service for handling chat interactions with RAG functionality."""

    def __init__(
        self,
        db: Session,
        vector_repo: VectorRepository,
        llm_service: LLMService,
    ):
        self.db = db
        self.vector_repo = vector_repo
        self.llm_service = llm_service

    def process_message(self, search_context: SearchContext) -> ChatResult:
        """
        Process a chat message using RAG pipeline.

        Args:
            search_context: Search parameters including query and filters

        Returns:
            ChatResult with response or error information
        """
        try:
            # Step 1: Retrieve relevant chunks
            chunks = self._retrieve_relevant_chunks(search_context)

            if not chunks:
                return ChatResult.failure_result(
                    error="No relevant information found",
                    data={
                        "query": search_context.query,
                        "lesson_id": search_context.lesson_id,
                    },
                )

            # Step 2: Generate response using LLM
            llm_result = self.llm_service.generate_response(
                chunks=chunks,
                query=search_context.query,
            )

            if not llm_result.success:
                return ChatResult.failure_result(
                    error=f"LLM generation failed: {llm_result.error}",
                    data={"query": search_context.query},
                )

            # Step 3: Format sources
            sources = self._format_sources(chunks)

            return ChatResult.success_result(
                response=llm_result.response,
                sources=sources,
                model_used=llm_result.model_used,
                data={
                    "chunks_used": len(chunks),
                    "query": search_context.query,
                    "lesson_id": search_context.lesson_id,
                },
            )

        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            raise

    def _retrieve_relevant_chunks(self, context: SearchContext) -> list[RetrievedChunk]:
        """Retrieve relevant chunks from vector store."""
        try:
            course_codes = context.course_codes or []
            lesson_ids = [context.lesson_id] if context.lesson_id else None

            search_results = self.vector_repo.similarity_search(
                query=context.query,
                k=context.max_results,
                course_codes=course_codes,
                lesson_ids=lesson_ids,
            )
            logger.debug(f"Resultados de la busqueda vectorial {search_results}")

            return [
                RetrievedChunk.from_search_result(result) for result in search_results
            ]

        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            raise

    def _format_sources(self, chunks: list[RetrievedChunk]) -> list[str]:
        sources = []
        for chunk in chunks:
            if chunk.course_code and chunk.lesson_id:
                base_source = f"{chunk.course_code} - Lesson {chunk.lesson_id}"

                if chunk.chunk_index is not None:
                    part_info = f" (Part {chunk.chunk_index + 1})"
                else:
                    part_info = ""

                source = f"{base_source}{part_info}\n{chunk.content}"
                sources.append(source)
        return sources

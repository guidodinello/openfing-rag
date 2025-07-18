from collections.abc import Iterable

from sqlalchemy.orm import Session

from services.generator.core.llm_service import LLMService
from services.generator.schemas import (
    ChatResult,
    RetrievedChunk,
    SearchContext,
    Source,
    SourceTimestamp,
)
from shared.database.repositories import (
    CourseRepository,
    LessonRepository,
    VectorRepository,
)
from shared.logging import get_logger

logger = get_logger(__name__)


class ChatService:
    """Service for handling chat interactions with RAG functionality."""

    def __init__(
        self,
        db: Session,
        vector_repo: VectorRepository,
        lesson_repo: LessonRepository,
        course_repo: CourseRepository,
        llm_service: LLMService,
    ):
        self.db = db
        self.vector_repo = vector_repo
        self.lesson_repo = lesson_repo
        self.course_repo = course_repo
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
            chunks = self._retrieve_relevant_chunks(search_context)

            llm_result = self.llm_service.generate_response(
                chunks=chunks,
                query=search_context.query,
            )
            # llm_result = LLMResult.success_result(
            #     response="This is a mock response for testing purposes.",
            #     model_used="mistralai/Mistral-7B-Instruct-v0.3",
            # )
            if not llm_result.success:
                return ChatResult.failure_result(
                    error=f"LLM generation failed: {llm_result.error}",
                    data={"query": search_context.query},
                )

            return ChatResult.success_result(
                response=llm_result.response,
                sources=self._format_sources(chunks),
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
        search_results = self.vector_repo.similarity_search(
            query=context.query,
            k=context.max_results,
            course_codes=context.course_codes or [],
            lesson_ids=[context.lesson_id] if context.lesson_id else None,
        )
        logger.debug(f"Resultados de la busqueda vectorial {search_results}")

        return [RetrievedChunk.from_search_result(result) for result in search_results]

    def _format_sources(self, chunks: Iterable[RetrievedChunk]) -> list[Source]:
        lessons = self.lesson_repo.get_by_ids(chunk.lesson_id for chunk in chunks)
        courses = self.course_repo.get_by_codes(chunk.course_code for chunk in chunks if chunk.course_code)

        sources = []
        for chunk in chunks:
            lesson = lessons.get(chunk.lesson_id)
            course = courses.get(chunk.course_code)

            if not lesson or not course:
                logger.debug(f"Missing lesson or course for chunk: {chunk}")
                continue

            sources.append(
                Source(
                    id=chunk.id,
                    title=f"{course.name} - {course.subtitle} - {lesson.title}",
                    content=chunk.content,
                    confidence=chunk.score,
                    SourceTimestamp=SourceTimestamp(
                        start=chunk.metadata.get("start_pos"),
                        end=chunk.metadata.get("end_pos"),
                    ),
                    url=lesson.video_url,
                ),
            )

        sources.sort(key=lambda s: s.confidence, reverse=True)
        return sources

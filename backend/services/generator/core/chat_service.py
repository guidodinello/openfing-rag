from collections.abc import Iterable

from sqlalchemy.orm import Session

from services.generator.core.llm_service import LLMService
from services.generator.schemas import Chat, ChatResult, RetrievedChunk, SearchContext, Source, SourceTimestamp
from shared.database.repositories import CourseRepository, LessonRepository, VectorRepository
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
            sources = self._format_sources(chunks)

            llm_result = self.llm_service.generate_answer(
                sources=sources,
                query=search_context.query,
            )
            if not llm_result.success:
                return ChatResult.failure_result(message=f"LLM generation failed: {llm_result.error}")

            return ChatResult.success_result(
                message="Succesfully generated response message",
                item=Chat(result=llm_result.item, sources=sources),
            )

        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            raise

    def _retrieve_relevant_chunks(self, context: SearchContext) -> list[RetrievedChunk]:
        search_results = self.vector_repo.similarity_search(
            query=context.query,
            k=context.max_results,
            courses_ids=context.courses_ids,
            lessons_ids=context.lessons_ids,
        )
        logger.debug(f"Chunks Retrieved {search_results=}")

        return [RetrievedChunk.from_search_result(result) for result in search_results]

    def _format_sources(self, chunks: Iterable[RetrievedChunk]) -> list[Source]:
        lessons = self.lesson_repo.get_by_ids(chunk.lesson_id for chunk in chunks)
        courses = self.course_repo.get_by_ids(chunk.course_id for chunk in chunks)

        sources = []
        for chunk in chunks:
            lesson = lessons.get(chunk.lesson_id)
            course = courses.get(chunk.course_id)

            if not lesson or not course:
                logger.debug(f"Missing lesson or course for chunk: {chunk}")
                continue

            sources.append(
                Source(
                    id=chunk.id,
                    title=f"{course.name} - {course.subtitle} - {lesson.title}",
                    content=chunk.content,
                    confidence=chunk.score,
                    timestamp=SourceTimestamp(
                        start=chunk.metadata.get("start_pos"),
                        end=chunk.metadata.get("end_pos"),
                    ),
                    url=lesson.video_url,
                ),
            )

        sources.sort(key=lambda s: s.confidence, reverse=True)
        return sources

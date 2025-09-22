from collections.abc import Iterable

from sqlalchemy.orm import Session

from shared.config import get_settings
from shared.database.models import Message
from shared.database.repositories import (
    ConversationRepository,
    CourseRepository,
    LessonRepository,
    MessageRepository,
    VectorRepository,
)
from shared.logging import get_logger

from services.generator.core.ephemeral_conversation import EphemeralConversationHandler
from services.generator.core.llm_service import LLMService
from services.generator.schemas import Chat, ChatResult, RetrievedChunk, SearchContext, Source, SourceTimestamp

logger = get_logger(__name__)
settings = get_settings()


class ChatService:
    """Service for handling chat interactions with RAG functionality and memory."""

    def __init__(
        self,
        db: Session,
        vector_repo: VectorRepository,
        lesson_repo: LessonRepository,
        course_repo: CourseRepository,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        llm_service: LLMService,
    ):
        self.db = db
        self.vector_repo = vector_repo
        self.lesson_repo = lesson_repo
        self.course_repo = course_repo
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.llm_service = llm_service

        self.ephemeral_conversation_handler = EphemeralConversationHandler()

    async def process_message(
        self,
        search_context: SearchContext,
        session_id: str,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> ChatResult:
        """
        Process a chat message using RAG pipeline with optional conversation memory.
        Handles both authenticated (database) and anonymous (session cache) conversations.
        """
        try:
            if user_id is not None:
                return await self._process_authenticated_message(search_context, user_id, conversation_id)
            else:
                return await self._process_anonymous_message(search_context, session_id)
        except Exception as e:
            if user_id:
                self.db.rollback()
            logger.error(f"Error processing chat message: {e}", exc_info=True)
            raise

    async def _process_authenticated_message(
        self,
        search_context: SearchContext,
        user_id: int,
        conversation_id: int | None = None,
    ) -> ChatResult:
        """Process message for authenticated users with database persistence."""
        conversation = self._get_or_create_conversation(user_id, conversation_id)
        history = self._get_conversation_history(conversation.id)

        _ = self.message_repo.add_user_message(
            conversation_id=conversation.id,
            content=search_context.query,
        )

        skip_retrieval = self._is_follow_up_question(search_context.query, bool(history))
        if not settings.NEVER_SKIP_RETRIEVAL and skip_retrieval:
            sources = []
            logger.info(f"Follow-up detected, skipping retrieval: {search_context.query}")
        else:
            chunks = self._retrieve_relevant_chunks(search_context)
            sources = self._format_sources(chunks)
            logger.info(f"New question, retrieved {len(sources)} sources")

        llm_result = self.llm_service.generate_answer(
            sources=sources,
            query=search_context.query,
            conversation_history=history,
        )
        if not llm_result.success:
            self.db.rollback()
            logger.warning(f"LLM generation failed, rolling back transaction: {llm_result.message}")
            return ChatResult.failure_result(message=f"LLM generation failed: {llm_result.message}")

        assistant_message = self.message_repo.add_assistant_message(
            conversation_id=conversation.id,
            content=llm_result.item.answer,
            sources=[
                {
                    "chunk_id": source.id,
                    "confidence_score": source.confidence,
                }
                for source in sources
            ],
        )

        self.db.commit()

        return ChatResult.success_result(
            message="Successfully generated response message",
            item=Chat(
                id=assistant_message.id,
                answer=llm_result.item,
                sources=sources,
            ),
        )

    async def _process_anonymous_message(
        self,
        search_context: SearchContext,
        session_id: str,
    ) -> ChatResult:
        """Process message for anonymous users using session cache."""
        # Use async-safe method to get history
        history = await self.ephemeral_conversation_handler.get_session_history(session_id)

        skip_retrieval = self._is_follow_up_question(search_context.query, bool(history))
        if not settings.NEVER_SKIP_RETRIEVAL and skip_retrieval:
            sources = []
            logger.info(f"Anonymous follow-up detected, skipping retrieval: {search_context.query}")
        else:
            chunks = self._retrieve_relevant_chunks(search_context)
            sources = self._format_sources(chunks)
            logger.info(f"Anonymous new question, retrieved {len(sources)} sources")

        llm_result = self.llm_service.generate_answer(
            sources=sources,
            query=search_context.query,
            conversation_history=history,
        )

        if not llm_result.success:
            logger.warning(f"LLM generation failed for anonymous user: {llm_result.message}")
            return ChatResult.failure_result(message=f"LLM generation failed: {llm_result.message}")

        await self.ephemeral_conversation_handler.update_session_history(
            session_id=session_id,
            user_message=search_context.query,
            assistant_message=llm_result.item.answer,
        )

        return ChatResult.success_result(
            message="Successfully generated response message",
            item=Chat(
                id=self.ephemeral_conversation_handler.generate_anonymous_message_id(
                    search_context.query,
                    llm_result.item.answer,
                ),
                answer=llm_result.item,
                sources=sources,
            ),
        )

    def _get_or_create_conversation(self, user_id: int, conversation_id: int | None):
        """Get existing conversation or create a new one."""
        if conversation_id:
            conversation = self.conversation_repo.get_by_id(conversation_id)
            ## TODO: make a policy middleware or look for a more scalable approach
            if conversation and conversation.user_id == user_id:
                return conversation

        return self.conversation_repo.create_conversation(user_id, title="default convo title")

    def _get_conversation_history(self, conversation_id: int, limit: int = 10) -> list[Message]:
        """Get recent conversation history formatted for LLM."""
        return self.message_repo.get_recent_messages(conversation_id, limit)

    def _retrieve_relevant_chunks(self, context: SearchContext) -> list[RetrievedChunk]:
        """Retrieve relevant chunks using vector search."""
        search_results = self.vector_repo.similarity_search(
            query=context.query,
            k=context.max_results,
            courses_ids=context.courses_ids,
            lessons_ids=context.lessons_ids,
        )

        return [RetrievedChunk.from_search_result(result) for result in search_results]

    def _format_sources(self, chunks: Iterable[RetrievedChunk]) -> list[Source]:
        """Format chunks into sources with lesson and course information."""
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

        sources.sort(key=lambda s: s.confidence, reverse=False)
        return sources

    def _is_follow_up_question(self, query: str, has_history: bool) -> bool:
        """Simple heuristic to detect follow-up questions."""
        if not has_history:
            return False
        if len(query.split()) <= 3:
            return True

        return False

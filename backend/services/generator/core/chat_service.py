from collections.abc import Iterable

from sqlalchemy.orm import Session

from shared.database.models.rag.conversations.message import Message
from shared.database.repositories import (
    ConversationRepository,
    CourseRepository,
    LessonRepository,
    MessageRepository,
    VectorRepository,
)
from shared.logging import get_logger

from services.generator.core.llm_service import LLMService
from services.generator.schemas import Chat, ChatResult, RetrievedChunk, SearchContext, Source, SourceTimestamp

logger = get_logger(__name__)


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

    def process_message(
        self,
        search_context: SearchContext,
        user_id: int,
        conversation_id: int | None = None,
    ) -> ChatResult:
        """
        Process a chat message using RAG pipeline with optional conversation memory.
        """
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(user_id, conversation_id)
            history = self._get_conversation_history(conversation.id)

            # Add user message to conversation
            _ = self.message_repo.add_user_message(
                conversation_id=conversation.id,
                content=search_context.query,
            )

            skip_retrieval = self._is_follow_up_question(search_context.query, bool(history))
            if skip_retrieval:
                sources = []
                logger.info(f"Follow-up detected, skipping retrieval: {search_context.query}")
            else:
                # Normal retrieval
                chunks = self._retrieve_relevant_chunks(search_context)
                sources = self._format_sources(chunks)
                logger.info(f"New question, retrieved {len(sources)} sources")

            # Generate response with context and history
            llm_result = self.llm_service.generate_answer(
                sources=sources,
                query=search_context.query,
                conversation_history=history,
            )
            if not llm_result.success:
                self.db.rollback()
                logger.warning(f"LLM generation failed, rolling back transaction: {llm_result.message}")
                return ChatResult.failure_result(message=f"LLM generation failed: {llm_result.message}")

            # Add assistant message to conversation with sources
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
                    # conversation_id=conversation.id,
                    # message_id=assistant_message.id,
                ),
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing chat message: {e}")
            raise

    def get_conversation_messages(self, user_id: int, conversation_id: int) -> list[dict]:
        """Get formatted conversation history for a user."""
        conversation = self.conversation_repo.get_conversation_with_messages(conversation_id, user_id)
        if not conversation:
            return []

        ## TODO: define a Message Schema
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in conversation.messages
        ]

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

        sources.sort(key=lambda s: s.confidence, reverse=True)
        return sources

    def _is_follow_up_question(self, query: str, has_history: bool) -> bool:
        """
        Simple heuristic to detect follow-up questions.
        """
        if not has_history:
            return False

        query_lower = query.lower().strip()

        # Rule 1: Very short questions
        if len(query.split()) <= 3:
            return True

        # Rule 2: Contains follow-up indicators
        if any(
            indicator in query_lower
            for indicator in [
                "qué significa",
                "a qué te refieres",
                "puedes explicar",
                "explica",
                "cómo es",
                "por qué",
                "cuál es",
                "más detalles",
                "ejemplo",
                "diferencia",
                "parecido",
                "similar",
                "igual",
            ]
        ):
            return True

        return False

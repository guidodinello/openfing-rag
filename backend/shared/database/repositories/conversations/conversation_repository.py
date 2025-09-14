from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from shared.database.models import Chunk, Conversation, Message, MessageSource
from shared.database.repositories import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: Session):
        super().__init__(Conversation, db)

    def get_user_conversations(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Conversation]:
        """Get conversations for a user ordered by last update."""
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(desc(self.model.updated_at))
            .limit(limit)
            .offset(offset)
        )
        return self.db.execute(query).scalars().all()

    def get_conversation_with_messages(self, conversation_id: int) -> Conversation | None:
        """
        Get a conversation with all its messages and sources, including chunk, lesson, and course data.
        This optimizes the query to load all related data in a single database call.
        """
        query = (
            select(self.model)
            .options(
                joinedload(self.model.messages).joinedload(Message.sources).joinedload(MessageSource.chunk),
                joinedload(self.model.messages)
                .joinedload(Message.sources)
                .joinedload(MessageSource.chunk)
                .joinedload(Chunk.lesson),
                joinedload(self.model.messages)
                .joinedload(Message.sources)
                .joinedload(MessageSource.chunk)
                .joinedload(Chunk.course),
            )
            .where(self.model.id == conversation_id)
        )
        return self.db.execute(query).unique().scalar_one_or_none()

    def create_conversation(
        self,
        user_id: int,
        title: str,
    ) -> Conversation:
        """Create a new conversation for a user."""
        return self.create(user_id=user_id, title=title)

from collections.abc import Sequence
from typing import TYPE_CHECKING

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from shared.database.models import Message, MessageRole
from shared.database.repositories import BaseRepository

if TYPE_CHECKING:
    from shared.database.repositories import MessageSourceRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, db: Session, source_repo: "MessageSourceRepository"):
        self.source_repo = source_repo
        super().__init__(Message, db)

    def get_conversation_messages(
        self,
        conversation_id: int,
        limit: int | None = None,
    ) -> Sequence[Message]:
        """Get messages for a conversation ordered by message_order."""
        query = (
            select(self.model)
            .options(joinedload(self.model.sources))
            .where(self.model.conversation_id == conversation_id)
            .order_by(self.model.message_order)
        )
        if limit:
            query = query.limit(limit)
        return self.db.execute(query).scalars().all()

    def get_recent_messages(
        self,
        conversation_id: int,
        limit: int = 10,
    ) -> Sequence[Message]:
        # Subquery para obtener los IDs de los últimos N mensajes
        recent_ids_subquery = (
            select(self.model.id)
            .where(self.model.conversation_id == conversation_id)
            .order_by(desc(self.model.message_order))
            .limit(limit)
        ).subquery()

        query = (
            select(self.model)
            .where(self.model.id.in_(select(recent_ids_subquery.c.id)))
            .order_by(self.model.message_order)
        )

        return self.db.execute(query).scalars().all()

    def add_message(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
    ) -> Message:
        """Add a new message to a conversation."""
        last_message_query = (
            select(self.model.message_order)
            .where(self.model.conversation_id == conversation_id)
            .order_by(desc(self.model.message_order))
            .limit(1)
        )
        last_order = self.db.execute(last_message_query).scalar()
        next_order = (last_order or 0) + 1

        return self.create(
            conversation_id=conversation_id,
            role=role.value,
            content=content,
            message_order=next_order,
        )

    def add_user_message(
        self,
        conversation_id: int,
        content: str,
    ) -> Message:
        """Convenience method to add a user message."""
        return self.add_message(conversation_id, MessageRole.USER, content)

    def add_assistant_message(
        self,
        conversation_id: int,
        content: str,
        sources: list[dict] | None = None,
    ) -> Message:
        """Convenience method to add an assistant message with sources."""
        message = self.add_message(conversation_id, MessageRole.ASSISTANT, content)

        # Add sources if provided
        if sources:
            self._add_message_sources(message.id, sources)
            self.db.flush()

        return message

    def _add_message_sources(self, message_id: int, sources: list[dict]) -> None:
        """Add source chunk references to a message."""
        self.source_repo.add_sources_to_message(message_id, sources)

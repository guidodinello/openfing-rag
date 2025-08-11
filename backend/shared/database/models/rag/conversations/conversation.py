from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Identity, Index, Integer, String
from sqlalchemy.orm import Mapped, relationship

from shared.database.models import TimestampedModel

if TYPE_CHECKING:
    from shared.database.models import User
    from shared.database.models.rag.conversations.message import Message


class Conversation(TimestampedModel):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_user_created", "user_id", "created_at"),
        {
            "extend_existing": True,
            "comment": "User conversations for chat history",
        },
    )

    id: Mapped[int] = Column(
        Integer,
        Identity(always=True),
        primary_key=True,
        comment="Unique identifier for the conversation",
    )

    user_id: Mapped[int] = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="User who owns this conversation",
    )

    title: Mapped[str] = Column(
        String(255),
        nullable=True,
        comment="Optional conversation title (auto-generated or user-defined)",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.message_order",
        passive_deletes=True,
    )

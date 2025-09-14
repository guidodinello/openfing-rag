from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, ForeignKey, Identity, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from shared.database.models import TimestampedModel

if TYPE_CHECKING:
    from .conversation import Conversation
    from .message_source import MessageSource


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(TimestampedModel):
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_conversation_order", "conversation_id", "message_order"),
        Index("idx_messages_role", "role"),
        UniqueConstraint(
            "conversation_id",
            "message_order",
            name="uq_messages_order",
        ),
        CheckConstraint(
            f"role IN ('{"', '".join([role.value for role in MessageRole])}')",
            name="ck_messages_role",
        ),
        {
            "extend_existing": True,
            "comment": "Individual messages within conversations",
        },
    )

    id: Mapped[int] = Column(
        Integer,
        Identity(always=True),
        primary_key=True,
        comment="Unique identifier for the message",
    )

    conversation_id: Mapped[int] = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Conversation this message belongs to",
    )

    role: Mapped[str] = Column(
        String(20),
        nullable=False,
        comment=f"MessageRole enum values: {"', '".join([role.value for role in MessageRole])}",
    )

    content: Mapped[str] = Column(
        Text,
        nullable=False,
        comment="Message content",
    )

    message_order: Mapped[int] = Column(
        Integer,
        nullable=False,
        comment="Order of message in conversation (for proper sequencing)",
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )

    sources: Mapped[list["MessageSource"]] = relationship(
        "MessageSource",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="MessageSource.confidence_score",
        passive_deletes=True,
    )

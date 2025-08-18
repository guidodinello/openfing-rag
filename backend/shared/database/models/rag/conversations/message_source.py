from typing import TYPE_CHECKING

from sqlalchemy import UUID, Column, Float, ForeignKey, Identity, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from shared.database.models import TimestampedModel

if TYPE_CHECKING:
    from shared.database.models import Chunk, Message


class MessageSource(TimestampedModel):
    __tablename__ = "message_sources"
    __table_args__ = (
        Index("idx_message_sources_message_id", "message_id"),
        Index("idx_message_sources_chunk_id", "chunk_id"),
        Index("idx_message_sources_message_order", "message_id", "source_order"),
        Index("idx_message_sources_confidence", "confidence_score"),
        UniqueConstraint(
            "message_id",
            "source_order",
            name="uq_message_sources_order",
        ),
        {
            "extend_existing": True,
            "comment": "Relationship between messages and the chunks used as sources",
        },
    )

    id: Mapped[int] = Column(
        Integer,
        Identity(always=True),
        primary_key=True,
        comment="Unique identifier for the message source",
    )

    message_id: Mapped[int] = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        comment="Message that used this source",
    )

    chunk_id: Mapped[str] = Column(
        UUID,
        nullable=False,
        comment="ID of the chunk that was used as source",
    )

    confidence_score: Mapped[float] = Column(
        Float,
        nullable=False,
        comment="Similarity score for this chunk",
    )

    source_order: Mapped[int] = Column(
        Integer,
        nullable=False,
        comment="Order of this source in the response (for ranking)",
    )

    # Relationships
    message: Mapped["Message"] = relationship(
        "Message",
        back_populates="sources",
    )
    chunk: Mapped["Chunk"] = relationship(
        "Chunk",
        primaryjoin="foreign(MessageSource.chunk_id) == Chunk.uuid",
        viewonly=True,
        lazy="joined",  # eager load if you often need the metadata
    )

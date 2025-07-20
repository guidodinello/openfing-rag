from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Identity, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship

from shared.database.models import TimestampedModel

if TYPE_CHECKING:
    from shared.database.models import Lesson


class Transcription(TimestampedModel):
    __tablename__ = "transcriptions"
    __table_args__ = (
        Index("idx_transcriptions_lesson", "lesson_id"),
        Index(
            "idx_transcriptions_metadata",
            "transcription_metadata",
            postgresql_using="gin",
        ),
        {
            "schema": "rag",
            "extend_existing": True,
            "comment": "Transcriptions model",
        },
    )

    id: Mapped[int] = Column(
        Integer,
        Identity(always=True),
        primary_key=True,
        comment="Unique identifier for the transcription",
    )

    content: Mapped[str] = Column(
        Text,
        nullable=False,
        comment="Transcription text content",
    )
    transcription_metadata: Mapped[dict] = Column(
        JSONB,
        server_default="{}",
        nullable=False,
        comment="Additional transcription attributes stored as JSONB",
    )

    lesson_id: Mapped[int] = Column(
        Integer,
        ForeignKey("rag.lessons.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the parent lesson",
    )

    lesson: Mapped["Lesson"] = relationship(
        "Lesson",
        back_populates="transcriptions",
    )

    def __repr__(self) -> str:
        return f"Transcription({self.id=} {self.lesson_id=} content_length={len(self.content) if self.content else 0})"

    def __str__(self) -> str:
        return f"Transcription for Lesson {self.lesson_id}"

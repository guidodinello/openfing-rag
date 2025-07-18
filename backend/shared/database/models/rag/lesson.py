from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship

from shared.database.models import TimestampedModel

if TYPE_CHECKING:
    from shared.database.models import Course, Transcription


class Lesson(TimestampedModel):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "number",
            name="uq_course_lesson_number",
            comment="Ensure lesson numbers are unique within a course",
        ),
        Index("idx_lessons_course", "course_id"),
        Index("idx_lessons_metadata", "lesson_metadata", postgresql_using="gin"),
        {
            "schema": "rag",
            "extend_existing": True,
            "comment": "Lesson model",
        },
    )

    id: Mapped[int] = Column(
        Integer,
        Identity(always=True),
        primary_key=True,
        comment="Unique identifier for the lesson",
    )
    number: Mapped[int] = Column(
        Integer,
        nullable=False,
        comment="Lesson number within the course (unique per course)",
    )

    title: Mapped[str] = Column(
        String(255),
        nullable=False,
        comment="Title of the lesson",
    )
    video_url: Mapped[str] = Column(
        String(255),
        nullable=True,
        comment="URL to the video content (optional)",
    )
    lesson_metadata: Mapped[dict] = Column(
        JSONB,
        server_default="{}",
        nullable=False,
        comment="Additional lesson attributes stored as JSONB",
    )

    course_id: Mapped[int] = Column(
        Integer,
        ForeignKey("rag.courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the parent course",
    )

    course: Mapped["Course"] = relationship("Course", back_populates="lessons")
    transcriptions: Mapped[list["Transcription"]] = relationship(
        "Transcription",
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Transcription.created_at",
    )

    def __repr__(self) -> str:
        return f"""Lesson({self.id=} {self.number=} {self.title=} {self.course_id=})"""

    def __str__(self) -> str:
        return f"Lesson {self.number}: {self.title}"

    @property
    def has_transcription(self) -> bool:
        return bool(self.transcriptions)

from sqlalchemy import Column, ForeignKey, Identity, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from shared.database.models import TimestampedModel


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

    id: int = Column(
        Integer,
        Identity(always=True),
        primary_key=True,
        comment="Unique identifier for the lesson",
    )
    number: int = Column(
        Integer,
        nullable=False,
        comment="Lesson number within the course (unique per course)",
    )

    title: str = Column(String(255), nullable=False, comment="Title of the lesson")
    video_url: str = Column(
        String(255),
        nullable=True,
        comment="URL to the video content (optional)",
    )
    lesson_metadata: dict = Column(
        JSONB,
        server_default="{}",
        nullable=False,
        comment="Additional lesson attributes stored as JSONB",
    )

    course_id: int = Column(
        Integer,
        ForeignKey("rag.courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the parent course",
    )

    course = relationship("Course", back_populates="lessons")
    transcriptions = relationship(
        "Transcription",
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Transcription.created_at",
    )

    def __repr__(self) -> str:
        return f"""Lesson(id={self.id}, number={self.number},
            title='{self.title}', course_id={self.course_id})"""

    def __str__(self) -> str:
        return f"Lesson {self.number}: {self.title}"

    @property
    def has_transcription(self) -> bool:
        return bool(self.transcriptions)

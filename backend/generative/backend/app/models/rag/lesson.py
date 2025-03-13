from app.models import Base, Chunk
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Lesson(Base):
    """
    Represents a lesson within a course in the RAG system.

    A lesson contains educational content including video and transcriptions,
    which are further broken down into chunks for processing. Each lesson belongs
    to a course and can have multiple transcriptions and chunks.
    """

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
            "comment": "Educational lessons containing video content and transcriptions",
        },
    )

    # Primary Key
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

    # Core fields
    title: str = Column(String(255), nullable=False, comment="Title of the lesson")
    video_url: str = Column(
        String(255), nullable=True, comment="URL to the video content (optional)"
    )
    lesson_metadata: dict = Column(
        JSONB,
        server_default="{}",
        nullable=False,
        comment="Additional lesson attributes stored as JSONB",
    )
    created_at: DateTime = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Timestamp when the lesson was created",
    )

    # Foreign Keys
    course_id: int = Column(
        Integer,
        ForeignKey("rag.courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the parent course",
    )

    # Relationships
    course = relationship("Course", back_populates="lessons")
    raw_transcriptions = relationship(
        "RawTranscription",
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RawTranscription.created_at",
    )
    chunks = relationship(
        "Chunk",
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Chunk.start_time",
    )

    def __repr__(self) -> str:
        """Provide a useful string representation of the lesson."""
        return f"Lesson(id={self.id}, number={self.number}, title='{self.title}', course_id={self.course_id})"

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"Lesson {self.number}: {self.title}"

    @property
    def has_transcription(self) -> bool:
        """Check if the lesson has any transcriptions."""
        return bool(self.raw_transcriptions)

    @property
    def chunk_count(self) -> int:
        """Return the number of chunks in this lesson."""
        return len(self.chunks)

    def get_chunk_by_time(self, timestamp: float) -> Chunk | None:
        """
        Find the chunk that contains the given timestamp.

        Args:
            timestamp: Time in seconds

        Returns:
            Chunk if found, None otherwise
        """
        timestamp_ms = int(timestamp * 1000)  # Convert to milliseconds
        for chunk in self.chunks:
            if chunk.start_time <= timestamp_ms <= chunk.end_time:
                return chunk
        return None

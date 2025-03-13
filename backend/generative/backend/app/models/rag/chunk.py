from datetime import timedelta

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models import Base


class Chunk(Base):
    """
    Represents a chunk of text from a lesson's transcription.
    Each chunk includes embeddings for semantic search capabilities.
    """

    __tablename__ = "chunks"
    __table_args__ = (
        CheckConstraint("start_time < end_time"),
        Index("idx_chunks_lesson", "lesson_id"),
        Index("idx_chunks_metadata", "chunk_metadata", postgresql_using="gin"),
        Index(
            "idx_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        {"schema": "rag"},
    )

    # Primary Key
    id: int = Column(
        Integer,
        Identity(always=True),  # Modern approach instead of server_default
        primary_key=True,
    )

    # Core fields
    content: str = Column(Text, nullable=False)
    start_time: int = Column(Integer, nullable=False)
    end_time: int = Column(Integer, nullable=False)
    embedding = Column(Vector(384))
    chunk_metadata: dict = Column(
        JSONB,
        server_default="{}",
        nullable=False,
    )
    created_at: DateTime = Column(
        DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False
    )

    # Foreign Keys
    lesson_id: int = Column(Integer, ForeignKey("rag.lessons.id"), nullable=False)
    transcription_id: int = Column(
        Integer, ForeignKey("rag.raw_transcriptions.id"), nullable=False
    )

    # Relationships
    lesson = relationship("Lesson", back_populates="chunks")
    transcription = relationship("RawTranscription", back_populates="chunks")

    # TODO: new, ver si se queda
    def format_time(self, seconds: int) -> str:
        """Convert seconds to human-readable time format."""
        time = timedelta(seconds=seconds)
        hours = time.seconds // 3600
        minutes = (time.seconds % 3600) // 60
        seconds = time.seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def __str__(self) -> str:
        """Return a human-readable string representation of the chunk."""
        start_formatted = self.format_time(self.start_time)
        end_formatted = self.format_time(self.end_time)

        if hasattr(self, "lesson") and self.lesson:
            course_code = (
                self.lesson.course.code if hasattr(self.lesson, "course") else "Unknown"
            )
            lesson_number = (
                self.lesson.number if hasattr(self.lesson, "number") else self.lesson_id
            )
            return (
                f"📺 {course_code} - Lesson {lesson_number}\n"
                f"⏱️ {start_formatted} - {end_formatted}\n"
                f"💬 {self.content[:100]}..."
            )

        return (
            f"Chunk {self.id}\n"
            f"⏱️ {start_formatted} - {end_formatted}\n"
            f"💬 {self.content[:100]}..."
        )

    def get_video_url(self) -> str:
        """Generate video URL with timestamp."""
        if hasattr(self, "lesson") and self.lesson and self.lesson.video_url:
            return f"{self.lesson.video_url}&t={self.start_time}"
        return ""

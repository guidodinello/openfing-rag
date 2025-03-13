from app.models import Base, Chunk
from sqlalchemy import Column, DateTime, ForeignKey, Identity, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class RawTranscription(Base):
    """
    Represents the raw transcription of a lesson's content.

    This model stores the unprocessed transcription text along with metadata
    before it gets chunked for RAG processing. Each transcription is associated
    with a lesson and can be broken down into multiple chunks for processing.

    Attributes:
        content: The raw transcription text
        raw_transcription_metadata: Additional metadata about the transcription
        lesson: The lesson this transcription belongs to
        chunks: Processed chunks derived from this transcription
    """

    __tablename__ = "raw_transcriptions"
    __table_args__ = (
        Index("idx_raw_transcriptions_lesson", "lesson_id"),
        Index(
            "idx_raw_transcriptions_metadata",
            "raw_transcription_metadata",
            postgresql_using="gin",
        ),
        {
            "schema": "rag",
            "extend_existing": True,
            "comment": "Raw transcriptions of lesson content before chunking",
        },
    )

    # Primary Key
    id: int = Column(
        Integer,
        Identity(always=True),
        primary_key=True,
        comment="Unique identifier for the transcription",
    )

    # Core fields
    content: str = Column(
        Text, nullable=False, comment="Raw transcription text content"
    )
    raw_transcription_metadata: dict = Column(
        JSONB,
        server_default="{}",
        nullable=False,
        comment="Additional transcription attributes stored as JSONB",
    )
    created_at: DateTime = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Timestamp when the transcription was created",
    )

    # Foreign Keys
    lesson_id: int = Column(
        Integer,
        ForeignKey("rag.lessons.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the parent lesson",
    )

    # Relationships
    lesson = relationship(
        "Lesson",
        back_populates="raw_transcriptions",
    )
    chunks = relationship(
        "Chunk",
        back_populates="transcription",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Chunk.start_time",
    )

    def __repr__(self) -> str:
        """Provide a useful string representation of the transcription."""
        return (
            f"RawTranscription(id={self.id}, "
            f"lesson_id={self.lesson_id}, "
            f"content_length={len(self.content) if self.content else 0})"
        )

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"Transcription for Lesson {self.lesson_id}"

    @property
    def word_count(self) -> int:
        """Calculate the number of words in the transcription."""
        return len(self.content.split()) if self.content else 0

    @property
    def chunk_count(self) -> int:
        """Return the number of chunks created from this transcription."""
        return len(self.chunks)

    @property
    def average_chunk_size(self) -> float | None:
        """Calculate the average number of words per chunk."""
        if not self.chunks:
            return None
        return self.word_count / len(self.chunks)

    def get_chunks_in_range(self, start_time: int, end_time: int) -> list[Chunk]:
        """
        Get all chunks that fall within the specified time range.

        Args:
            start_time: Start time in milliseconds
            end_time: End time in milliseconds

        Returns:
            List of chunks that overlap with the specified time range
        """
        return [
            chunk
            for chunk in self.chunks
            if not (chunk.end_time < start_time or chunk.start_time > end_time)
        ]

    def get_text_segment(self, start_pos: int, end_pos: int) -> str:
        """
        Get a segment of the transcription text.

        Args:
            start_pos: Starting character position
            end_pos: Ending character position

        Returns:
            The text segment between the specified positions
        """
        if not self.content:
            return ""
        return self.content[start_pos:end_pos]

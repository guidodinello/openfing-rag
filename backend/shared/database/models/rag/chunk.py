from sqlalchemy import JSON, UUID, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database.models import Base
from shared.database.models.rag.course import Course
from shared.database.models.rag.lesson import Lesson
from shared.database.models.rag.transcription import Transcription


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        {
            "schema": "rag",
            "comment": "Chunks used for vector similarity search",
        },
    )

    uuid: Mapped[str] = mapped_column(UUID, primary_key=True, comment="Deterministic UUID used as chunk ID")

    content: Mapped[str] = mapped_column(Text, nullable=False, comment="Chunk text content")

    transcription_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rag.transcriptions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Transcription this chunk is derived from",
    )

    lesson_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rag.lessons.id", ondelete="CASCADE"),
        nullable=False,
        comment="Lesson associated with this chunk",
    )

    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rag.courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="Course associated with this chunk",
    )

    chunk_metadata: Mapped[dict] = mapped_column(
        JSON,
        name="metadata",
        nullable=True,
        comment="Additional metadata stored with the chunk",
    )

    # Relationships
    transcription: Mapped[Transcription] = relationship("Transcription", foreign_keys=[transcription_id], lazy="select")

    lesson: Mapped[Lesson] = relationship("Lesson", foreign_keys=[lesson_id], lazy="select")

    course: Mapped[Course] = relationship("Course", foreign_keys=[course_id], lazy="select")

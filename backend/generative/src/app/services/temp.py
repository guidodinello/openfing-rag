from datetime import timedelta

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.rag.chunk import Chunk


class SourceInfo(BaseModel):
    """Represents formatted source information for a chunk."""

    lesson_id: int
    course_code: str
    lesson_number: int
    lesson_title: str
    start_time: int
    end_time: int
    video_url: str
    formatted_start: str
    formatted_end: str

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
        """Return formatted string representation."""
        return (
            f"Lesson {self.lesson_number} ({self.course_code}): "
            f"{self.lesson_title} "
            f"({self.formatted_start} - {self.formatted_end})\n"
            f"🔗 {self.video_url}&t={self.start_time}"
        )


class ChunkSourceFormatter:
    """Handles formatting of chunk sources with video timestamps."""

    @staticmethod
    async def get_chunks_with_lessons(
        db: AsyncSession, chunks: list[Chunk]
    ) -> list[Chunk]:
        """
        Fetch chunks with their associated lesson information.

        Args:
            db: Database session
            chunks: list of chunks to fetch lesson data for

        Returns:
            list of chunks with lesson data eagerly loaded
        """
        chunk_ids = [chunk.id for chunk in chunks]
        query = (
            select("Chunk")
            .where(Chunk.id.in_(chunk_ids))
            .options(joinedload("Chunk.lesson").joinedload("Course"))
        )
        result = await db.execute(query)
        return result.unique().scalars().all()

    @classmethod
    async def format_sources(cls, db: AsyncSession, chunks: list[Chunk]) -> list[str]:
        """
        Format source information for each chunk with video timestamps.

        Args:
            db: Database session
            chunks: list of chunks to format

        Returns:
            list of formatted source strings
        """
        # Fetch chunks with lesson data
        chunks_with_lessons = await cls.get_chunks_with_lessons(db, chunks)

        sources = []
        for chunk in chunks_with_lessons:
            if not chunk.lesson or not chunk.lesson.video_url:
                continue

            source = SourceInfo(
                lesson_id=chunk.lesson.id,
                course_code=chunk.lesson.course.code,
                lesson_number=chunk.lesson.number,
                lesson_title=chunk.lesson.title,
                start_time=chunk.start_time,
                end_time=chunk.end_time,
                video_url=chunk.lesson.video_url,
                formatted_start=SourceInfo.format_time(chunk.start_time),
                formatted_end=SourceInfo.format_time(chunk.end_time),
            )
            sources.append(str(source))

        return sources

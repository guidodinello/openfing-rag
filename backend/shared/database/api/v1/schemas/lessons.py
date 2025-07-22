from typing import Self

from pydantic import BaseModel

from shared.api.v1.schemas.api import ApiListResponse
from shared.database.models import Lesson as LessonModel


class Lesson(BaseModel):
    """API response model for lesson data."""

    id: int
    number: int
    title: str
    video_url: str | None = None
    course_id: int
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, lesson: LessonModel) -> Self:
        return cls(
            id=lesson.id,
            number=lesson.number,
            title=lesson.title,
            video_url=lesson.video_url,
            course_id=lesson.course_id,
            created_at=lesson.created_at.isoformat(),
            updated_at=lesson.updated_at.isoformat(),
        )


ListLessonsResponse = ApiListResponse[Lesson]

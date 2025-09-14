from typing import Self

from pydantic import BaseModel

from shared.api.v1.schemas.api import ApiResponse

from services.scraper.schemas import SyncResult


class Sync(BaseModel):
    success: bool
    message: str
    courses_created: int = 0
    courses_updated: int = 0
    lessons_created: int = 0
    lessons_updated: int = 0
    total_courses: int = 0
    total_lessons: int = 0

    @classmethod
    def from_sync_result(cls, result: SyncResult) -> Self:
        return cls(
            success=result.success,
            message=result.message,
            courses_created=result.stats.courses_created,
            courses_updated=result.stats.courses_updated,
            lessons_created=result.stats.lessons_created,
            lessons_updated=result.stats.lessons_updated,
            total_courses=result.stats.total_courses,
            total_lessons=result.stats.total_lessons,
        )


SyncResponse = ApiResponse[Sync]

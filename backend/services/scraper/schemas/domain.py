from dataclasses import dataclass
from typing import Self


@dataclass(slots=True)
class SyncStats:
    courses_created: int
    courses_updated: int
    lessons_created: int
    lessons_updated: int
    total_courses: int
    total_lessons: int

    @property
    def total_courses_synced(self) -> int:
        return self.courses_created + self.courses_updated

    @property
    def total_lessons_synced(self) -> int:
        return self.lessons_created + self.lessons_updated

    @property
    def all_successful(self) -> bool:
        return self.total_courses_synced == self.total_courses and self.total_lessons_synced == self.total_lessons

    def __str__(self) -> str:
        return (
            f"Courses: {self.courses_created} created, {self.courses_updated} updated | "
            f"Lessons: {self.lessons_created} created, {self.lessons_updated} updated"
        )


@dataclass(frozen=True, slots=True)
class SyncResult:
    success: bool
    message: str
    stats: SyncStats
    course_code: str | None = None

    @classmethod
    def success_result(cls, stats: SyncStats, course_code: str | None = None) -> Self:
        operation = f"course {course_code}" if course_code else "all courses"
        return cls(
            success=True,
            message=f"Successfully synchronized {operation}: {stats}",
            stats=stats,
            course_code=course_code,
        )

    @classmethod
    def failure_result(cls, message: str, course_code: str | None = None, stats: SyncStats | None = None) -> Self:
        if stats is None:
            stats = SyncStats(
                courses_created=0,
                courses_updated=0,
                lessons_created=0,
                lessons_updated=0,
                total_courses=0,
                total_lessons=0,
            )

        return cls(
            success=False,
            message=message,
            stats=stats,
            course_code=course_code,
        )

    def to_api_response(self):
        from services.scraper.schemas.api import SyncResponse

        return SyncResponse(
            success=self.success,
            message=self.message,
            courses_created=self.stats.courses_created,
            courses_updated=self.stats.courses_updated,
            lessons_created=self.stats.lessons_created,
            lessons_updated=self.stats.lessons_updated,
            total_courses=self.stats.total_courses,
            total_lessons=self.stats.total_lessons,
        )

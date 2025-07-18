from typing import Self

from pydantic import BaseModel, Field

from services.scraper.schemas.domain import SyncResult
from shared.database.models import Course, Lesson


class SyncResponse(BaseModel):
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


class CourseResponse(BaseModel):
    id: int
    code: str
    name: str
    subtitle: str | None = None
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, course: Course) -> Self:
        return cls(
            id=course.id,
            code=course.code,
            name=course.name,
            subtitle=course.subtitle,
            created_at=course.created_at.isoformat(),
            updated_at=course.updated_at.isoformat(),
        )


class LessonResponse(BaseModel):
    """API response model for lesson data."""

    id: int
    number: int
    title: str
    video_url: str | None = None
    course_id: int
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, lesson: Lesson) -> Self:
        return cls(
            id=lesson.id,
            number=lesson.number,
            title=lesson.title,
            video_url=lesson.video_url,
            course_id=lesson.course_id,
            created_at=lesson.created_at.isoformat(),
            updated_at=lesson.updated_at.isoformat(),
        )


class CourseWithLessonsResponse(BaseModel):
    """API response for course with lessons."""

    course: CourseResponse
    lessons: list[LessonResponse]
    total_lessons: int = Field(description="Total number of lessons for this course")

    @classmethod
    def from_models(cls, course: Course, lessons: list[Lesson]) -> Self:
        return cls(
            course=CourseResponse.from_model(course),
            lessons=[LessonResponse.from_model(lesson) for lesson in lessons],
            total_lessons=len(lessons),
        )

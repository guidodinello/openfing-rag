from typing import Self

from pydantic import BaseModel, Field


class SyncResponse(BaseModel):
    """API response for sync operations."""

    success: bool
    message: str
    courses_created: int = 0
    courses_updated: int = 0
    lessons_created: int = 0
    lessons_updated: int = 0
    total_courses: int = 0
    total_lessons: int = 0


class CourseResponse(BaseModel):
    """API response model for course data."""

    id: int
    code: str
    name: str
    subtitle: str | None = None
    created_at: str
    updated_at: str


class LessonResponse(BaseModel):
    """API response model for lesson data."""

    id: int
    number: int
    title: str
    video_url: str | None = None
    course_id: int
    created_at: str
    updated_at: str


class CourseWithLessonsResponse(BaseModel):
    """API response for course with lessons."""

    course: CourseResponse
    lessons: list[LessonResponse]
    total_lessons: int = Field(description="Total number of lessons for this course")

    @classmethod
    def from_domain(cls, course, lessons: list) -> Self:
        """Convert from domain models to API response."""
        return cls(
            course=CourseResponse(
                id=course.id,
                code=course.code,
                name=course.name,
                subtitle=course.subtitle,
                created_at=course.created_at.isoformat() if course.created_at else "",
                updated_at=course.updated_at.isoformat() if course.updated_at else "",
            ),
            lessons=[
                LessonResponse(
                    id=lesson.id,
                    number=lesson.number,
                    title=lesson.title,
                    video_url=lesson.video_url,
                    course_id=lesson.course_id,
                    created_at=lesson.created_at.isoformat() if lesson.created_at else "",
                    updated_at=lesson.updated_at.isoformat() if lesson.updated_at else "",
                )
                for lesson in lessons
            ],
            total_lessons=len(lessons),
        )

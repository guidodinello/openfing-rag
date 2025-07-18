from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from shared.database.models import Course, Lesson
from shared.database.repositories import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    def __init__(self, db: Session):
        super().__init__(Lesson, db)

    def get_by_course_and_number(self, course_id: int, number: int) -> Lesson | None:
        return self.get_by(course_id=course_id, number=number)

    def get_by_course(self, course_id: int) -> list[Lesson]:
        return (
            self.db.execute(
                select(self.model).where(self.model.course_id == course_id).order_by(self.model.number),
            )
            .scalars()
            .all()
        )

    def get_with_course(self, course_code: str, lesson_number: int) -> Lesson | None:
        """Get lesson with course relationship loaded."""
        return (
            self.db.query(self.model)
            .options(joinedload(self.model.course))
            .join(Course)
            .filter(Course.code == course_code)
            .filter(self.model.number == lesson_number)
            .first()
        )

    def update_or_create_by_course_and_number(
        self,
        course_id: int,
        number: int,
        **data,
    ) -> tuple[Lesson, bool]:
        return self.update_or_create(data, course_id=course_id, number=number)

    def get_downloadable_lessons_by_course_code(
        self,
        course_code: str,
        lesson_numbers: list[int] | None = None,
    ) -> list[Lesson]:
        query = (
            select(self.model)
            .join(Course, self.model.course_id == Course.id)
            .where(
                Course.code == course_code,
                self.model.video_url.isnot(None),  # WHERE video_url IS NOT NULL
                self.model.video_url != "",  # AND video_url != ''
            )
        )

        if lesson_numbers:
            query = query.where(self.model.number.in_(lesson_numbers))
        query = query.order_by(self.model.number)

        return self.db.execute(query).scalars().all()

    def bulk_sync_lessons(self, lessons_data: list[dict[str, Any]]) -> dict[str, int]:
        return self.bulk_update_or_create(
            lessons_data,
            unique_fields=["course_id", "number"],
        )

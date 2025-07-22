from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.database.models import Course
from shared.database.repositories import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, db: Session):
        super().__init__(Course, db)

    def get_by_code(self, code: str) -> Course | None:
        return self.get_by(code=code)

    def get_by_codes(self, codes: list[str]) -> dict[str, Course]:
        courses = self.db.execute(select(self.model).where(self.model.code.in_(codes))).scalars().all()
        return {course.code: course for course in courses}

    def bulk_sync_courses(self, courses_data: list[dict[str, Any]]) -> dict[str, int]:
        return self.bulk_update_or_create(courses_data, unique_fields=["code"])

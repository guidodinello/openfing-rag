from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.database.models.rag.lesson import Lesson
from shared.database.repositories.base_repository import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    def __init__(self, db: Session):
        super().__init__(Lesson, db)

    def get_by_course_and_number(self, course_id: int, number: int) -> Lesson | None:
        return self.get_by(course_id=course_id, number=number)

    def get_by_course(self, course_id: int) -> list[Lesson]:
        return (
            self.db.execute(select(self.model).where(self.model.course_id == course_id).order_by(self.model.number))
            .scalars()
            .all()
        )

    def update_or_create_by_course_and_number(self, course_id: int, number: int, **data) -> tuple[Lesson, bool]:
        return self.update_or_create(data, course_id=course_id, number=number)

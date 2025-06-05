from sqlalchemy.orm import Session

from shared.database.models.rag.course import Course
from shared.database.repositories.base_repository import BaseRepository


class CourseRepository(BaseRepository[Course]):
    """Repository for Course operations."""

    def __init__(self, db: Session):
        super().__init__(Course, db)

    def get_by_code(self, code: str) -> Course | None:
        return self.get_by(code=code)

    def update_or_create_by_code(self, code: str, **data) -> tuple[Course, bool]:
        return self.update_or_create(data, code=code)

from shared.database.factories import CourseFactory
from shared.database.repositories.course_repository import CourseRepository
from shared.database.seeders.base import BaseSeeder


class CourseSeeder(BaseSeeder):
    def __init__(self, db, course_repo: CourseRepository):
        super().__init__(db)
        self.course_repo = course_repo

    def run(self, count: int = 50) -> None:
        _ = CourseFactory(self.db).create_batch(count)

from shared.database.factories.lesson import LessonFactory
from shared.database.models import Course
from shared.database.repositories import CourseRepository, LessonRepository
from shared.database.seeders.base import BaseSeeder


class LessonSeeder(BaseSeeder):
    def __init__(
        self,
        db,
        lesson_repo: LessonRepository,
        course_repo: CourseRepository,
    ):
        super().__init__(db)
        self.lesson_repo = lesson_repo
        self.course_repo = course_repo

    def run(self, lessons_per_course: int = 3) -> None:
        course_ids = self.get_random_records(Course, columns=Course.id, limit=5)
        factory = LessonFactory(db=self.db)
        for course_id in course_ids:
            _ = factory.create_batch(count=lessons_per_course, course_id=course_id)

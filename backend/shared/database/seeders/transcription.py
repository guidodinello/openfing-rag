from shared.database.factories import TranscriptionFactory
from shared.database.models.rag.lesson import Lesson
from shared.database.repositories.lesson_repository import LessonRepository
from shared.database.seeders.base import BaseSeeder


class TranscriptionSeeder(BaseSeeder):
    def __init__(self, db, lesson_repo: LessonRepository):
        super().__init__(db)
        self.lesson_repo = lesson_repo

    def run(self, count_per_lesson: int = 3) -> None:
        lesson_ids = self.get_random_records(Lesson, columns=Lesson.id, limit=5)
        factory = TranscriptionFactory(db=self.db)

        for lesson_id in lesson_ids:
            _ = factory.create_batch(count=count_per_lesson, lesson_id=lesson_id)

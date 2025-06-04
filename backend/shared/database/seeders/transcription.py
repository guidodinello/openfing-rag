from shared.database.factories import TranscriptionFactory
from shared.database.models import Lesson
from shared.database.seeders import BaseSeeder


class TranscriptionSeeder(BaseSeeder):
    async def run(self):
        factory = TranscriptionFactory(db=self.db)

        lesson_ids = await self.get_random_records(Lesson, columns=Lesson.id, limit=5)
        for lesson_id in lesson_ids:
            await factory.create_batch(
                3,
                lesson_id=lesson_id,
            )

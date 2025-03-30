from app.db.factories import RawTranscriptionFactory
from app.db.seeders import BaseSeeder
from app.models import Lesson


class RawTranscriptionSeeder(BaseSeeder):
    async def run(self):
        factory = RawTranscriptionFactory(db=self.db)

        lesson_ids = await self.get_random_records(Lesson, columns=Lesson.id, limit=5)
        for lesson_id in lesson_ids:
            await factory.create_batch(
                3,
                lesson_id=lesson_id,
            )

from app.models import Lesson

from tests.factories import RawTranscriptionFactory
from tests.seeders import BaseSeeder


class RawTranscriptionSeeder(BaseSeeder):
    async def run(self):
        factory = RawTranscriptionFactory(db=self.db)

        lesson_ids = await self.get_random_records(Lesson, columns=Lesson.id, limit=5)
        for lesson_id in lesson_ids:
            await factory.create_batch(
                3,
                lesson_id=lesson_id,
            )

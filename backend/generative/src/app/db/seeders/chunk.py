from app.db.factories import ChunkFactory
from app.db.seeders import BaseSeeder
from app.models import RawTranscription


class ChunkSeeder(BaseSeeder):
    async def run(self):
        factory = ChunkFactory(db=self.db)

        transcription_pairs = await self.get_related_records(
            RawTranscription,
            relations=RawTranscription.lesson_id,
            limit=5,
        )
        for transcription_id, lesson_id in transcription_pairs:
            await factory.create_batch(
                3,
                transcription_id=transcription_id,
                lesson_id=lesson_id,
            )

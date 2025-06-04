from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.seeders import CourseSeeder, LessonSeeder
from shared.database.seeders.transcription import TranscriptionSeeder
from shared.database.seeders.user import UserSeeder


class DatabaseSeeder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.seeders = [
            UserSeeder(db),
            CourseSeeder(db),
            LessonSeeder(db),
            TranscriptionSeeder(db),
        ]

    async def run(self):
        for seeder in self.seeders:
            await seeder.run()
        await self.db.commit()

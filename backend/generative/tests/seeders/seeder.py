# app/database/seeder.py
from sqlalchemy.ext.asyncio import AsyncSession

from tests.seeders import CourseSeeder, LessonSeeder


class DatabaseSeeder:
    """Main seeder class that orchestrates all seeders."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.seeders = [
            CourseSeeder(db),  # First seed courses
            LessonSeeder(db),  # Then lessons that reference courses
            # RawTranscriptionSeeder(db),
            # ChunkSeeder(db),  # Finally chunks that reference lessons
        ]

    async def run(self):
        """Run all seeders."""
        for seeder in self.seeders:
            await seeder.run()
        await self.db.commit()

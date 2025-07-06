from sqlalchemy.orm import Session

from shared.database.repositories import CourseRepository, LessonRepository, UserRepository
from shared.database.seeders.user import UserSeeder
from shared.logging.logger import get_logger

logger = get_logger(__name__)


class DatabaseSeeder:
    """
    Main database seeder that orchestrates all individual seeders.
    """

    def __init__(self, db: Session):
        self.db = db

        self.user_repo = UserRepository(db)
        self.course_repo = CourseRepository(db)
        self.lesson_repo = LessonRepository(db)

        self.seeders = [
            UserSeeder(db, self.user_repo),
            # CourseSeeder(db, self.course_repo),
            # LessonSeeder(db, self.lesson_repo, self.course_repo),
            # TranscriptionSeeder(db, self.lesson_repo),
        ]

    def run(self) -> None:
        logger.info("Starting database seeding...")

        try:
            for seeder in self.seeders:
                seeder_name = seeder.__class__.__name__
                logger.info(f"🏃‍♂️ Running {seeder_name}...")

                seeder.run()
                logger.info(f"✅ {seeder_name} completed")

            self.db.commit()
            logger.info("✅ All seeders completed successfully")

        except Exception as e:
            logger.error(f"❌ Seeding failed: {e}")
            self.db.rollback()
            raise

from sqlalchemy.orm import Session

from services.scraper.scrapers.course_scraper import Course as CourseSchema
from services.scraper.scrapers.lesson_scraper import Lesson as LessonSchema
from services.scraper.scrapers.openfing_scraper import OpenFingScraper
from shared.database.repositories.course_repository import CourseRepository
from shared.database.repositories.lesson_repository import LessonRepository
from shared.logging.logger import get_logger

logger = get_logger(__name__)


class ScrapingService:
    """Service for scraping and syncing OpenFing data."""

    def __init__(
        self,
        db: Session,
        course_repo: CourseRepository = None,
        lesson_repo: LessonRepository = None,
        scraper: OpenFingScraper = None,
    ):
        """
        Initialize scraping service.

        Args:
            db: Database session
            course_repo: Course repository (will create if None)
            lesson_repo: Lesson repository (will create if None)
            scraper: OpenFing scraper (will create if None)
        """
        self.db = db
        self.course_repo = course_repo or CourseRepository(db)
        self.lesson_repo = lesson_repo or LessonRepository(db)
        self.scraper = scraper or OpenFingScraper()

    def sync_openfing_data(self) -> dict[str, int]:
        """
        Scrape OpenFing and sync with database.

        Returns:
            Dictionary with sync statistics
        """
        logger.info("Starting OpenFing data synchronization")

        try:
            scraping_result = self.scraper.scrape()

            courses_stats = self._sync_courses(scraping_result.courses)
            lessons_stats = self._sync_lessons(scraping_result.lessons)

            # Commit all changes
            self.db.commit()

            total_stats = {
                "courses_created": courses_stats["created"],
                "courses_updated": courses_stats["updated"],
                "lessons_created": lessons_stats["created"],
                "lessons_updated": lessons_stats["updated"],
                "total_courses": len(scraping_result.courses),
                "total_lessons": len(scraping_result.lessons),
            }

            logger.info(
                f"Sync completed: {total_stats['courses_created']} courses created, "
                f"{total_stats['lessons_created']} lessons created",
            )

            return total_stats

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self.db.rollback()
            raise

    def _sync_courses(self, scraped_courses: list[CourseSchema]) -> dict[str, int]:
        """Sync scraped courses to database."""
        created_count = 0
        updated_count = 0

        for scraped_course in scraped_courses:
            try:
                course, was_created = self.course_repo.update_or_create_by_code(
                    code=scraped_course.acronym,
                    name=scraped_course.title,
                    subtitle=scraped_course.subtitle,
                    course_metadata={
                        "url": scraped_course.url,
                        "scraped_from": "openfing",
                    },
                )

                if was_created:
                    created_count += 1
                    logger.debug(f"Created course: {course.code}")
                else:
                    updated_count += 1
                    logger.debug(f"Updated course: {course.code}")

            except Exception as e:
                logger.error(f"Failed to sync course {scraped_course.acronym}: {e}")
                continue

        return {"created": created_count, "updated": updated_count}

    def _sync_lessons(self, scraped_lessons: list[LessonSchema]) -> dict[str, int]:
        """Sync scraped lessons to database."""
        created_count = 0
        updated_count = 0

        for scraped_lesson in scraped_lessons:
            try:
                course = self.course_repo.get_by_code(scraped_lesson.course_acronym)
                if not course:
                    logger.warning(
                        f"Course {scraped_lesson.course_acronym} not found for lesson {scraped_lesson.number}",
                    )
                    continue

                lesson, was_created = self.lesson_repo.update_or_create_by_course_and_number(
                    course_id=course.id,
                    number=scraped_lesson.number,
                    title=scraped_lesson.title,
                    video_url=scraped_lesson.url,
                )

                if was_created:
                    created_count += 1
                    logger.debug(f"Created lesson: {course.code} - {lesson.number}")
                else:
                    updated_count += 1
                    logger.debug(f"Updated lesson: {course.code} - {lesson.number}")

            except Exception as e:
                logger.error(f"Failed to sync lesson {scraped_lesson.course_acronym}#{scraped_lesson.number}: {e}")
                continue

        return {"created": created_count, "updated": updated_count}

    def sync_course_only(self, course_acronym: str) -> dict[str, int]:
        """
        Sync a specific course and its lessons.

        Args:
            course_acronym: Course code to sync

        Returns:
            Dictionary with sync statistics
        """
        logger.info(f"Starting sync for course: {course_acronym}")

        try:
            scraping_result = self.scraper.scrape()

            target_course = next((c for c in scraping_result.courses if c.acronym == course_acronym), None)

            if not target_course:
                logger.warning(f"Course {course_acronym} not found in scraped data")
                return {"courses_created": 0, "courses_updated": 0, "lessons_created": 0, "lessons_updated": 0}

            course_lessons = [lesson for lesson in scraping_result.lessons if lesson.course_acronym == course_acronym]

            courses_stats = self._sync_courses([target_course])
            lessons_stats = self._sync_lessons(course_lessons)

            self.db.commit()

            result = {
                "courses_created": courses_stats["created"],
                "courses_updated": courses_stats["updated"],
                "lessons_created": lessons_stats["created"],
                "lessons_updated": lessons_stats["updated"],
                "total_lessons": len(course_lessons),
            }

            logger.info(f"Course sync completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Course sync failed: {e}")
            self.db.rollback()
            raise

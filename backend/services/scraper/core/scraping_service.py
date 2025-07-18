from collections.abc import Collection, Iterable

from sqlalchemy.orm import Session

from services.scraper.core.scrapers.course_scraper import Course as CourseSchema
from services.scraper.core.scrapers.lesson_scraper import Lesson as LessonSchema
from services.scraper.core.scrapers.openfing_scraper import OpenFingScraper
from services.scraper.schemas import SyncResult, SyncStats
from shared.database.models import Course
from shared.database.repositories import CourseRepository, LessonRepository
from shared.logging import get_logger

logger = get_logger(__name__)


class ScrapingService:
    """Service for scraping and syncing OpenFing data."""

    def __init__(
        self,
        db: Session,
        course_repo: CourseRepository,
        lesson_repo: LessonRepository,
        scraper: OpenFingScraper,
    ):
        self.db = db
        self.course_repo = course_repo
        self.lesson_repo = lesson_repo
        self.scraper = scraper

    def sync_openfing_data(self) -> SyncResult:
        """
        Scrape all OpenFing courses and lessons, then sync with database.
        """
        logger.info("Starting full OpenFing data synchronization")

        scraping_result = self.scraper.scrape()
        stats = self._sync_data(scraping_result.courses, scraping_result.lessons)

        return SyncResult.success_result(stats)

    def sync_course_only(self, course_acronym: str) -> SyncResult:
        logger.info(f"Starting sync for course: {course_acronym=}")

        scraping_result = self.scraper.scrape()

        # Filter to target course only
        target_course = [c for c in scraping_result.courses if c.acronym == course_acronym]
        target_lessons = [le for le in scraping_result.lessons if le.course_acronym == course_acronym]

        if not target_course:
            logger.warning(f"Course {course_acronym} not found in scraped data")
            return SyncResult.failure_result(
                f"Course '{course_acronym}' not found on OpenFing",
                course_code=course_acronym,
            )

        stats = self._sync_data(target_course, target_lessons)

        return SyncResult.success_result(stats, course_code=course_acronym)

    def _sync_data(
        self,
        courses: Collection[CourseSchema],
        lessons: Collection[LessonSchema],
    ) -> SyncStats:
        try:
            courses_stats = self._sync_courses(courses)

            lessons_stats = self._sync_lessons(
                lessons,
                course_mapping=self.course_repo.get_by_codes(course.acronym for course in courses),
            )

            self.db.commit()

            return SyncStats(
                courses_created=courses_stats["created"],
                courses_updated=courses_stats["updated"],
                lessons_created=lessons_stats["created"],
                lessons_updated=lessons_stats["updated"],
                total_courses=len(courses),
                total_lessons=len(lessons),
            )

        except Exception:
            logger.error("Sync failed!")
            self.db.rollback()
            raise

    def _sync_lessons(
        self,
        scraped_lessons: Iterable[LessonSchema],
        course_mapping: dict[str, Course],
    ) -> dict[str, int]:
        lessons_data = []

        for lesson in scraped_lessons:
            course = course_mapping.get(lesson.course_acronym)
            if not course:
                logger.warning(
                    f"Course {lesson.course_acronym} not found for lesson {lesson.number}",
                )
                continue

            lessons_data.append(
                {
                    "course_id": course.id,
                    "number": lesson.number,
                    "title": lesson.title,
                    "video_url": lesson.url,
                },
            )

        return self.lesson_repo.bulk_sync_lessons(lessons_data)

    def _sync_courses(self, scraped_courses: Iterable[CourseSchema]) -> dict[str, int]:
        return self.course_repo.bulk_sync_courses(
            [
                {
                    "code": course.acronym,
                    "name": course.title,
                    "subtitle": course.subtitle,
                    "course_metadata": {
                        "url": course.url,
                        "scraped_from": "openfing",
                    },
                }
                for course in scraped_courses
            ],
        )

from dataclasses import dataclass

from services.scraper.core.scrapers.course_scraper import Course, CourseScraper
from services.scraper.core.scrapers.lesson_scraper import Lesson, LessonScraper
from shared.http.client import HTTPClient
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ScrapingResult:
    courses: list[Course]
    lessons: list[Lesson]


class OpenFingScraper:
    def __init__(self, http_client: HTTPClient):
        self._http_client = http_client
        self._course_scraper = CourseScraper(self._http_client)
        self._lesson_scraper = LessonScraper(self._http_client)

    def scrape(self) -> ScrapingResult:
        """Scrape all courses and their lessons from OpenFing."""
        courses = self._course_scraper.get_courses()
        lessons = []

        for course in courses:
            course_lessons = self._lesson_scraper.get_lessons(course.acronym)
            lessons.extend(course_lessons)

        logger.debug(
            f"Scraped {len(courses)} courses and {len(lessons)} lessons from OpenFing",
        )

        return ScrapingResult(courses=courses, lessons=lessons)

from dataclasses import dataclass

from services.scraper.scrapers.course_scraper import Course, CourseScraper
from services.scraper.scrapers.lesson_scraper import Lesson, LessonScraper
from shared.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ScrapingResult:
    courses: list[Course]
    lessons: list[Lesson]


class OpenFingScraper:
    def __init__(self):
        self.__logger = logger
        self.__course_scraper = CourseScraper()
        self.__lesson_scraper = LessonScraper()

    def scrape(self) -> ScrapingResult:
        """Scrape all courses and their lessons from OpenFing."""
        courses = self.__course_scraper.get_courses()
        lessons = []

        for course in courses:
            course_lessons = self.__lesson_scraper.get_lessons(course.acronym)
            lessons.extend(course_lessons)

        self.__logger.debug(f"Scraped {len(courses)} courses and {len(lessons)} lessons from OpenFing")

        return ScrapingResult(courses=courses, lessons=lessons)

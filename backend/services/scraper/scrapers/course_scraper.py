from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag

from services.scraper.constants.constants import OPEN_FING_URL
from shared.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Course:
    acronym: str
    title: str
    subtitle: str
    url: str


class CourseScraper:
    def __init__(self):
        self.__logger = logger
        self.__http_client = requests

    def get_courses(self) -> list[Course]:
        soup = self.__get_html(OPEN_FING_URL)
        courses_urls = self.__get_courses_urls(soup)

        results = []
        for course_url in courses_urls:
            soup = self.__get_html(course_url)
            title = self.__get_course_title(soup)

            for subcourse_tag in self.__get_subcourses_tags(soup):
                results.append(
                    Course(
                        acronym=self.__get_acronym_from_url(subcourse_tag.get("href")),
                        title=title,
                        subtitle=subcourse_tag.text,
                        url=subcourse_tag.get("href"),
                    ),
                )

        return results

    def __get_subcourses_tags(self, soup: BeautifulSoup) -> list[Tag]:
        return soup.find_all(
            "a",
            class_="related-links__item",
        )

    def __get_courses_urls(self, soup: BeautifulSoup) -> list[str]:
        course_items = soup.find_all("a", class_="name course")
        courses = [course["href"] for course in course_items]
        return courses

    def __get_course_title(self, soup: BeautifulSoup) -> str:
        return soup.find("h1").text.strip()

    def __get_acronym_from_url(self, url: str) -> str:
        courses_url_base = f"{OPEN_FING_URL}/courses/"
        return url.replace(courses_url_base, "").rstrip("/")

    def __get_html(self, url: str) -> BeautifulSoup | None:
        try:
            response = self.__http_client.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.__logger.error(f"Failed to scrape {url=}: {e}")
            return None

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            return soup

        except Exception as e:
            self.__logger.error(f"Failed to parse response from {url=}: {e}")
            return None

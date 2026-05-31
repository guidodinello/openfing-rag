from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag

from shared.config import get_settings
from shared.http.client import HTTPClient
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass(frozen=True, slots=True)
class Lesson:
    course_acronym: str
    number: int
    title: str
    url: str


class LessonScraper:
    def __init__(self, http_client: HTTPClient):
        self._http_client = http_client

    def get_lessons(self, course_acronym: str) -> list[Lesson]:
        soup = self._get_html(
            f"{settings.SCRAPER.OPENFING_URL}/courses/{course_acronym}/",
        )

        return [
            Lesson(
                course_acronym=course_acronym,
                number=self._get_lesson_number(lesson_tag),
                title=self._get_lesson_title(lesson_tag),
                url=lesson_tag.get("href"),
            )
            for lesson_tag in self._get_lessons_tags(soup)
        ]

    def _get_lessons_tags(self, soup: BeautifulSoup) -> list[Tag]:
        return soup.find_all("a", class_="clase-enlace")

    def _get_lesson_number(self, soup: BeautifulSoup) -> int:
        return int(soup.find("span", class_="clase-numero").text.strip())

    def _get_lesson_title(self, soup: BeautifulSoup) -> str:
        return soup.find("div", class_="clase-titulo").text.strip()

    def _get_html(self, url: str) -> BeautifulSoup | None:
        try:
            response = self._http_client.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to scrape {url=}: {e}")
            return None

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            return soup

        except Exception as e:
            logger.error(f"Failed to parse response from {url=}: {e}")
            return None

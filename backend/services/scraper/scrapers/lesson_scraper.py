from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag

from services.scraper.constants.constants import OPEN_FING_URL
from shared.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Lesson:
    course_acronym: str
    number: int
    title: str
    url: str


# TODO:
# scrapear para sacar las clases no es la mejor idea, si cambian la interfaz de la pagina se rompe todo
# lo mejor seria hablar con los de open fing. capaz tienen una api
# o generann los links con un metodo especifico.
class LessonScraper:
    def __init__(self):
        self.__logger = logger
        self.__http_client = requests

    def get_lessons(self, course_acronym: str) -> list[Lesson]:
        soup = self.__get_html(f"{OPEN_FING_URL}/courses/{course_acronym}/")

        return [
            Lesson(
                course_acronym=course_acronym,
                number=self.__get_lesson_number(lesson_tag),
                title=self.__get_lesson_title(lesson_tag),
                url=lesson_tag.get("href"),
            )
            for lesson_tag in self.__get_lessons_tags(soup)
        ]

    def __get_lessons_tags(self, soup: BeautifulSoup) -> list[Tag]:
        return soup.find_all("a", class_="class-list__item")

    def __get_lesson_number(self, soup: BeautifulSoup) -> int:
        return int(soup.find("span", class_="class-list__item-number").text.strip())

    def __get_lesson_title(self, soup: BeautifulSoup) -> str:
        return soup.find("div", class_="class-list__item-name").text.strip()

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

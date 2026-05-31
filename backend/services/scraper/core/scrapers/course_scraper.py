from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag

from shared.config import get_settings
from shared.http.client import HTTPClient
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass(frozen=True, slots=True)
class Course:
    acronym: str
    title: str
    subtitle: str
    url: str


class CourseScraper:
    def __init__(self, http_client: HTTPClient):
        self._http_client = http_client

    def get_courses(self) -> list[Course]:
        soup = self._get_html(settings.SCRAPER.OPENFING_URL)

        courses_urls = self._get_courses_urls(soup)

        return self._scrape_courses_concurrent(courses_urls)

    def _scrape_courses_concurrent(self, course_urls: Iterable[str]) -> list[Course]:
        all_courses = []

        with ThreadPoolExecutor(max_workers=settings.SCRAPER.WORKERS) as executor:
            # Submit all HTTP requests tasks at once
            future_to_url = {executor.submit(self._scrape_single_course, url): url for url in course_urls}

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    courses = future.result()
                    all_courses.extend(courses)
                except Exception as e:
                    logger.error(f"Failed to scrape course page {url}: {e}")

        return all_courses

    def _scrape_single_course(self, course_url: str) -> list[Course]:
        soup = self._get_html(course_url)

        title = self._get_course_title(soup)
        subcourse_tags = self._get_subcourses_tags(soup)

        return [
            Course(
                acronym=self._get_acronym_from_url(subcourse_tag.get("href", "")),
                title=title,
                subtitle=subcourse_tag.text.strip(),
                url=subcourse_tag.get("href", ""),
            )
            for subcourse_tag in subcourse_tags
            if subcourse_tag.get("href")
        ]

    def _get_subcourses_tags(self, soup: BeautifulSoup) -> list[Tag]:
        return soup.find_all(
            "a",
            class_="curso-enlace",
        )

    def _get_courses_urls(self, soup: BeautifulSoup) -> list[str]:
        course_items = soup.find_all("a", class_="enlace-curso")
        urls = [course.get("href", "") for course in course_items]
        return urls

    def _get_course_title(self, soup: BeautifulSoup) -> str:
        return soup.find("h1").text.strip()

    def _get_acronym_from_url(self, url: str) -> str:
        return url.split("/courses/")[-1].rstrip("/")

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

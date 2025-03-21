import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup


class CourseScraper:
    def __init__(
        self,
        url="https://open.fing.edu.uy/courses/",
        db_path="../DB/CoursesNames/",
    ):
        self.url = url
        self.db_path = db_path
        self.timestamp_path = Path(db_path) / "last_run_timestamp.txt"

    def fetch_courses(self):
        if self.should_run():
            response = requests.get(self.url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                course_list_div = soup.find("div", class_="course-list")
                course_acronyms = []
                course_names = []

                if course_list_div:
                    courses = course_list_div.find_all("a", class_="name course")
                    for course in courses:
                        href = course.get("href")
                        if href:
                            acronym = href.split("/")[-2]
                            course_acronyms.append(acronym)

                        course_title_span = course.find("span", class_="course-title")
                        if course_title_span:
                            course_names.append(course_title_span.text.strip())

                self.write_to_file(course_acronyms, "course_acronyms.txt")
                self.write_to_file(course_names, "course_names.txt")
                logging.info(
                    "Course acronyms and names have been written to 'course_acronyms.txt' and 'course_names.txt'."
                )
                self.update_timestamp()
            else:
                logging.info(
                    f"Failed to retrieve the page. Status code: {response.status_code}"
                )
        else:
            logging.info(
                "CourseScraper skipped as it was already run within the last week."
            )

    def write_to_file(self, data, filename):
        file_path = Path(self.db_path) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            for item in data:
                file.write(f"{item}\n")

    def should_run(self):
        if self.timestamp_path.exists():
            with open(self.timestamp_path, "r", encoding="utf-8") as f:
                last_run = datetime.fromisoformat(f.read().strip())
                return datetime.now() - last_run > timedelta(weeks=1)
        return True

    def update_timestamp(self):
        with open(self.timestamp_path, "w", encoding="utf-8") as f:
            f.write(datetime.now().isoformat())

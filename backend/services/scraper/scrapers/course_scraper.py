import ast
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from Constants.Constants import ACRONYMS_FOLDER, OPEN_FING_URL

from shared.logging import get_logger

logger = get_logger(__name__)


class CourseScraper:
    def __init__(self):
        self.__logger = logger

    def ensure_course_scraped(self, course_acronym: str):
        self.__course_acronym = course_acronym
        self.__path = Path(ACRONYMS_FOLDER + "/" + course_acronym + ".txt")
        if not self.__is_course_scraped():
            return self.__scrape_course()
        else:
            return self.__get_previous_scraped()

    def __is_course_scraped(self):
        return self.__path.exists()

    def update_course_classes(self, course_acronym: str):
        self.__course_acronym = course_acronym
        self.__path = Path(ACRONYMS_FOLDER + "/" + course_acronym + ".txt")
        self.__scrape_course()

    def __scrape_course(self):
        # TODO:
        # scrapear para sacar las clases no es la mejor idea, si cambian la interfaz de la pagina se rompe todo
        # lo mejor seria hablar con los de open fing. capaz tienen una api
        # o generann los links con un metodo especifico.
        self.__logger.log_message(f"Scraping course {self.__course_acronym}")
        classes_numbers = self.__get_class_numbers(self.__course_acronym)
        if len(classes_numbers) > 0:
            self.__logger.log_message(f"Writing classes numbers to {self.__path}")
            self.__logger.write_on_file(self.__path, classes_numbers)
        return classes_numbers

    def __get_class_numbers(self, course_acronym):
        url = f"{OPEN_FING_URL}/courses/{course_acronym}/"
        self.__logger.log_message(url)
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            class_items = soup.find_all("span", class_="class-list__item-number")
            classes_numbers = [int(item.text.strip()) for item in class_items]
            return classes_numbers
        else:
            self.__logger.log_message(
                f"Failed to retrieve the page for {url}. Status code: {response.status_code}",
            )
            return []

    def __get_previous_scraped(self):
        with open(self.__path) as file:
            content = file.read().strip()
            numbers = ast.literal_eval(content)
            print(self.__path)
            print(content)
            print(numbers)
            return numbers

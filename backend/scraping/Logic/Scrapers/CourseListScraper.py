from Logger.Logger import Logger
from Constants.Constants import OPEN_FING_URL, COURSES_ACRONYMS_PATH
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import ast

class CourseListScraper:
    def __init__(self):
        self.__logger = Logger()
        self.__acronym_path=Path(COURSES_ACRONYMS_PATH)
        self.__main_page_courses_class_name='name course'
        # self.__active_couse_class_name="related-links__item related-links__item--active"
        self.__courses_class_name="related-links__item"
    
    def ensure_acronyms(self):

        if self.__acronym_path.exists():
            return self.__acronyms_scraped_previously()
        else:
            return self.acronym_scraper(self)

    def __acronyms_scraped_previously(self):
       with open(self.__acronym_path, 'r') as file:
            content = file.read().strip()
            acronyms = ast.literal_eval(content)
            return acronyms

    def acronym_scraper(self):
        # "
        # Scrapes course acronyms from OpenFing and returns them as an array.
        # For each course found on the main page:
        # - Adds its acronym
        # - Finds referenced courses on that course's page
        # - Adds referenced course acronyms
        # Returns an array of all course acronyms.
        # "
        courseUrlList = self.__get_course_list_main_page()
        result = {}

        for course_url in courseUrlList:
            title= self.__get_page_title(course_url)
            courses_links= self.__current_page.find_all('a', class_=self.__courses_class_name)
            for link in courses_links:
                text=link.text
                acronym=self.__URL_to_acronym(link['href'])
                result[acronym] = title + ': ' + text
        self.__logger.log_message(result)
        self.__logger.write_on_file(self.__acronym_path, result)
        return result

    def __get_course_list_main_page(self):
        html_page = requests.get(OPEN_FING_URL)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        courseList = soup.find_all('a', class_=self.__main_page_courses_class_name)
        courseList = [course['href'] for course in courseList]
        return courseList

    def __URL_to_acronym(self, url:str):
        url = url.replace(OPEN_FING_URL + '/courses/', '')
        url = url.replace('/', '')
        return url

    def __get_page_title(self, url:str):
        html_page = requests.get(url)
        self.__current_page = BeautifulSoup(html_page.text, 'html.parser')
        html_a_elements = self.__current_page.find('h1')
        if(len(html_a_elements) < 1):
            return ""
        else:
            return html_a_elements.text

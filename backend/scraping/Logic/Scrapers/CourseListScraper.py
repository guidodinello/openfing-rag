# from Backend.Logger.Logger import Logger
# from constants.constants import OPEN_FING_URL, COURSES_ACRONYMS_PATH, HELPERS_FOLDER
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import os


class CourseListScraper:
    def __init__(self):
        pass
        # # self.logger = Logger()    

    def acronym_scraper(self):
        # "
        # Scrapes course acronyms from OpenFing and returns them as an array.
        # For each course found on the main page:
        # - Adds its acronym
        # - Finds referenced courses on that course's page
        # - Adds referenced course acronyms
        # Returns an array of all course acronyms.
        # "
        courseList = self.get_course_list_main_page()
        result = []
        
        for course_url in courseList:
            course_acronym = self.URL_to_acronym(course_url)
            result.append(course_acronym)
            # self.logger.log_message(f'Scraping course list: {course_acronym}')
            referenced_course_list = self.get_course_list_referenced_page(course_url)
            result.extend(self.get_referenced_courses(referenced_course_list))
        # self.logger.log_message(result)
        # self.logger.write_on_file(Path(COURSES_ACRONYMS_PATH), result)
        return result

    def get_course_list_main_page(self):
        OPEN_FING_URL=""
        html_page = requests.get(OPEN_FING_URL)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        courseList = soup.find_all('a', class_='name course')
        courseList = [course['href'] for course in courseList]
        # self.logger.log_message(f'courseList: {courseList}')
        return courseList
    
    def get_course_list_referenced_page(self, course_url):
        html_page = requests.get(course_url)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        referenced_course_list = soup.find_all('a', class_='related-links__item')
        return referenced_course_list

    def get_referenced_courses(self, referenced_course_list):
        result = []
        for referenced_course in referenced_course_list:
            referenced_course_url = referenced_course.get('href')
            referenced_course_acronym = self.URL_to_acronym(referenced_course_url)
            result.append(referenced_course_acronym)
            # self.logger.log_message(f'Scraping course list: {referenced_course_acronym}')
        return result

    def URL_to_acronym(self, url):
        OPEN_FING_URL=""
        url.replace(OPEN_FING_URL + '/courses/', '')
        url.replace('/', '')
        return url
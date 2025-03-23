from Logger.Logger import Logger
from Constants.Constants import OPEN_FING_URL, COURSES_ACRONYMS_PATH
from bs4 import BeautifulSoup
import requests
from pathlib import Path

class CourseListScraper:
    def __init__(self):
        self.logger = Logger()    
    
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
            referenced_acronyms = self.get_referenced_acronyms(course_url)
            result.extend(referenced_acronyms)
        self.logger.log_message(result)
        self.logger.write_on_file(Path(COURSES_ACRONYMS_PATH), result)
        return result

    def get_course_list_main_page(self):
        html_page = requests.get(OPEN_FING_URL)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        courseList = soup.find_all('a', class_='name course')
        courseList = [course['href'] for course in courseList]
        return courseList
    
    def get_referenced_acronyms(self, course_url:str):
        html_page = requests.get(course_url)
        soup = BeautifulSoup(html_page.text, 'html.parser')
        html_a_elements = soup.find_all('a', class_='related-links__item')
        referenced_course_list = [course['href'] for course in html_a_elements]
        referenced_course_list = referenced_course_list.remove(course_url)
        referenced_acronyms = [self.URL_to_acronym(course) for course in referenced_course_list]    
        return referenced_acronyms

    def URL_to_acronym(self, url:str):
        url = url.replace(OPEN_FING_URL + '/courses/', '')
        url = url.replace('/', '')
        return url
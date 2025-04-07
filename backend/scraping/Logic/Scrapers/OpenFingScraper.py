from .ClassScraper import ClassScraper
from .CourseListScraper import CourseListScraper
from .CourseScraper import CourseScraper
from Constants.Constants import COURSES_ACRONYMS_PATH
import os

class OpenFingScraper:
    
    def __init__(self):
        self.course_list_scraper = CourseListScraper()
        self.course_scraper = CourseScraper()
        # self.class_scraper = ClassScraper();

    def scrape_openfing(self):
        course_acronyms = self.get_course_acronyms()
        for course_acronym in course_acronyms:
            return self.course_scraper.ensure_course_scraped(course_acronym)
    
    def do_scrape_openfing(self):
        course_acronyms = self.course_list_scraper.get_course_acronyms()
        for course_acronym in course_acronyms:
            return self.course_scraper.ensure_course_scraped(course_acronym)
        
    # def scrape_class(self):
        # return self.class_scraper.scrape_class()

    def get_course_acronyms(self):
        if os.path.exists(COURSES_ACRONYMS_PATH):
            with open(COURSES_ACRONYMS_PATH, 'r') as file:
                acronyms = file.read().splitlines()
        else:
            acronyms = self.course_list_scraper.acronym_scraper()
        return acronyms

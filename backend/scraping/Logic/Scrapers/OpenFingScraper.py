from .CourseListScraper import CourseListScraper
from .CourseScraper import CourseScraper
from Constants.Constants import COURSES_ACRONYMS_PATH
class OpenFingScraper:
    
    def __init__(self):
        self.course_list_scraper = CourseListScraper()
        self.course_scraper = CourseScraper()
        

    def scrape_openfing(self):
        course_acronyms = self.get_course_acronyms()
        for course_acronym in course_acronyms:
            self.course_scraper.ensure_course_scraped(course_acronym)
    
    def do_scrape_openfing(self):
        course_acronyms = self.course_list_scraper.get_course_acronyms()
        for course_acronym in course_acronyms:
            self.course_scraper.ensure_course_scraped(course_acronym)
        
    def scrape_class(self):
        self.class_scraper.scrape_class()

    def get_course_acronyms(self):
        try:
            with open(COURSES_ACRONYMS_PATH, 'r') as file:
                acronyms = file.read().splitlines()
        except FileNotFoundError:
            acronyms = self.course_list_scraper.acronym_scraper()
        return acronyms

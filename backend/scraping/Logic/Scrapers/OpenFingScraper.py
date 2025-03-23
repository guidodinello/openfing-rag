from .CourseListScraper import CourseListScraper
from .CourseScraper import CourseScraper

class OpenFingScraper:
    
    def __init__(self):
        self.course_list_scraper = CourseListScraper()
        self.course_scraper = CourseScraper()
        

    def scrape_openfing(self):
        course_acronyms = self.course_list_scraper.acronym_scraper()
        for course_acronym in course_acronyms:
            self.course_scraper.scrape_course(course_acronym)
        
    def scrape_class(self):
        self.class_scraper.scrape_class()

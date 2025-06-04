from .course_list_scraper import CourseListScraper
from .course_scraper import CourseScraper


class OpenFingScraper:
    def __init__(self):
        self.__course_list_scraper = CourseListScraper()
        self.__course_scraper = CourseScraper()
        # self.class_scraper = ClassScraper();

    def get_acronyms(self):
        return self.__course_list_scraper.ensure_acronyms()

    def get_classes(self, acronym):
        classes = self.__course_scraper.ensure_course_scraped(acronym)
        if classes and len(classes) == 0:
            return f"{acronym} not found in classes"
        return classes

    def update_openfing(self):
        course_acronyms = self.__course_list_scraper.acronym_scraper()
        for acronym in course_acronyms:
            self.__course_scraper.update_course_classes(acronym)

    def update_acronyms(self):
        self.__course_list_scraper.acronym_scraper()

    def update_course(self, acronym):
        self.__course_scraper.update_course_classes(acronym)

    def update_courses_classes(self):
        course_acronyms = self.__course_list_scraper.ensure_acronyms()
        for acronym in course_acronyms:
            self.__course_scraper.update_course_classes(acronym)

from Logger.Logger import Logger
from Constants.Constants import OPEN_FING_URL, ACRONYMS_FOLDER
import requests
from bs4 import BeautifulSoup
from pathlib import Path

class CourseScraper:
    
    def __init__(self):
        self.logger = Logger()

    def ensure_course_scraped(self,course_acronym:str):
        self.course_acronym = course_acronym
        self.path = Path(ACRONYMS_FOLDER + '/' + course_acronym + '.txt')
        if(not self.is_course_scraped()):
            self.scrape_course()
            
    def is_course_scraped(self):
        return self.path.exists()        

    def scrape_course(self):
        # TODO:
            # scrapear para sacar las clases no es la mejor idea, si cambian la interfaz de la pagina se rompe todo
            # lo mejor seria hablar con los de open fing. capaz tienen una api o generann los links con un metodo especifico.
        self.logger.log_message(f"Scraping course {self.course_acronym}")
        class_items = self.get_classes_urls(self.course_acronym)
        classes_numbers = []
        for class_item in class_items:
            class_number = class_item.text
            classes_numbers.append(class_number)
        self.logger.log_message(f"Writing classes numbers to {self.path}")
        self.logger.write_on_file(self.path, classes_numbers)

    def get_classes_urls(self, course_acronym):
        url = f"{OPEN_FING_URL}/courses/{course_acronym}/"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            class_items = soup.find_all("span", class_="class-list__item-number")
            return class_items
        else:
            self.logger.log_message(
                f"Failed to retrieve the page for {url}. Status code: {response.status_code}"
            )
            return []
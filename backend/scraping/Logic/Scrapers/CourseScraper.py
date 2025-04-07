from Logger.Logger import Logger
from Constants.Constants import OPEN_FING_URL, ACRONYMS_FOLDER
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import os
class CourseScraper:
    
    def __init__(self):
        self.logger = Logger()

    def ensure_course_scraped(self,course_acronym:str):
        self.course_acronym = course_acronym
        self.path = Path(ACRONYMS_FOLDER + '/' + course_acronym + '.txt')
        if(not self.is_course_scraped()):
            return self.scrape_course()
        else:
            return self.get_previous_scraped()
                
    def is_course_scraped(self):
        return self.path.exists()        

    def scrape_course(self):
        # TODO:
            # scrapear para sacar las clases no es la mejor idea, si cambian la interfaz de la pagina se rompe todo
            # lo mejor seria hablar con los de open fing. capaz tienen una api o generann los links con un metodo especifico.
        self.logger.log_message(f"Scraping course {self.course_acronym}")
        classes_numbers = self.get_class_numbers(self.course_acronym)
        self.logger.log_message(f"Writing classes numbers to {self.path}")
        self.logger.write_on_file(self.path, classes_numbers)
        return classes_numbers

    def get_class_numbers(self, course_acronym):
        url = f"{OPEN_FING_URL}/courses/{course_acronym}/"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            class_items = soup.find_all("span", class_="class-list__item-number")
            classes_numbers = [item.text for item in class_items]
            return classes_numbers
        else:
            self.logger.log_message(
                f"Failed to retrieve the page for {url}. Status code: {response.status_code}"
            )
            return []
    def get_previous_scraped(self):
        ##read the file in self.path and return the list of numbers
        ##content of the file [number1,number2,number3 ...]
        with open(self.path, 'r') as file:
            content = file.read()
            numbers = content.strip().split(',')
            return [int(number) for number in numbers]
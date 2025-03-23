# from backend.Logic.Logger.Logger import Logger
# from constants.constants import OPEN_FING_URL
import requests
from bs4 import BeautifulSoup

class CourseScraper:
    
    def __init__(self):
        # # self.logger = Logger()
        self.classes_numbers = []

    def scrape_course(self, course_acronym):
        self.course_acronym = course_acronym
         # TODO:
            # scrapear para sacar las clases no es la mejor idea, si cambian la interfaz de la pagina se rompe todo
            # lo mejor seria hablar con los de open fing. capaz tienen una api o generann los links con un metodo especifico.
        url = f"{OPEN_FING_URL}/{self.course_acronym}/"
        response = requests.get(url)

        if response.status_code == 200:
           
            soup = BeautifulSoup(response.content, "html.parser")
            class_urls = soup.find_all("a", class_="class-list__item")
            for class_item in class_urls:
                href = class_item.get("href")
                if href:
                    class_number = href.split("/")[-1]
                    self.classes_numbers.append(class_number)
                    print(self.course_acronym + ":"+ class_number)
        else:
            pass
            # self.logger.log_message(
                # f"Failed to retrieve the page for {self.course_acronym}. Status code: {response.status_code}"
            # )

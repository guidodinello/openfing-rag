import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup


class ClassScraper:
    def __init__(self, db_path="../DB/Opens/"):
        self.db_path = Path(db_path)
        self.timestamp_path = Path(db_path) / "last_run_timestamp.txt"

    def get_classes_for_course(self, course_acronym):
        url = f"https://open.fing.edu.uy/courses/{course_acronym}/"
        response = requests.get(url)
        class_numbers = []

        if response.status_code == 200:
            # TODO:
            # scrapear para sacar las clases no es la mejor idea, si cambian la interfaz de la pagina se rompe todo
            # lo mejor seria hablar con los de open fing. capaz tienen una api o generann los links con un metodo especifico.
            soup = BeautifulSoup(response.content, "html.parser")
            class_list_div = soup.find("div", class_="class-list")

            if class_list_div:
                classes = class_list_div.find_all("a", class_="class-list__item")
                for class_item in classes:
                    href = class_item.get("href")
                    if href:
                        class_number = href.split("/")[-2]
                        class_numbers.append(class_number)
        else:
            logging.info(
                f"Failed to retrieve the page for {course_acronym}. Status code: {response.status_code}"
            )

        return class_numbers

    def save_classes_to_file(self, course_acronym):
        if self.should_run():
            classes = self.get_classes_for_course(course_acronym)
            output_dir = Path(self.db_path) / course_acronym
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "classes.txt"

            with open(output_file, "w", encoding="utf-8") as class_file:
                for class_number in classes:
                    class_file.write(f"{class_number}\n")

            logging.info(
                f"Class numbers for course {course_acronym} have been written to {output_file}"
            )
            self.update_timestamp()
        else:
            logging.info(
                "ClassScraper skipped as it was already run within the last week."
            )

    def should_run(self):
        if self.timestamp_path.exists():
            with open(self.timestamp_path, "r", encoding="utf-8") as f:
                last_run = datetime.fromisoformat(f.read().strip())
                return datetime.now() - last_run > timedelta(weeks=1)
        return True

    def update_timestamp(self):
        with open(self.timestamp_path, "w", encoding="utf-8") as f:
            f.write(datetime.now().isoformat())

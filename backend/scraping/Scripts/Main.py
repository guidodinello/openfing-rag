import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ClassScraper import ClassScraper
from constants import BYTES_TO_GB
from CourseDownloader import CourseDownloader  # Updated import
from CourseScraper import CourseScraper
from tqdm import tqdm
from Transcriber import Transcriber

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def download_course_videos(acronym, course_downloader: CourseDownloader):
    course_downloader.process_course(acronym)


def main():
    course_scraper = CourseScraper()
    class_scraper = ClassScraper()

    course_acronyms_path = Path("../DB/CoursesNames/course_acronyms.txt")

    if course_scraper.should_run() or class_scraper.should_run():
        course_scraper.fetch_courses()

        if course_acronyms_path.exists():
            with open(course_acronyms_path, "r", encoding="utf-8") as file:
                course_acronyms = [line.strip() for line in file if line.strip()]

            for acronym in course_acronyms:
                class_scraper.save_classes_to_file(acronym)
        else:
            logging.info(
                f"Course acronyms file not found at {course_acronyms_path}. Aborting process."
            )
            return
        course_scraper.update_timestamp()
        class_scraper.update_timestamp()
    else:
        logging.info(
            "CourseScraper and ClassScraper skipped as they were already run within the last week."
        )

    transcriber = Transcriber(model_name="medium")

    course_downloader = CourseDownloader(transcriber, total_max_size=2 * BYTES_TO_GB)

    if course_acronyms_path.exists():
        with open(course_acronyms_path, "r", encoding="utf-8") as file:
            course_acronyms = [line.strip() for line in file if line.strip()]

        # TODO: modificar la concurrencia
        # el main spawnea hilos que llaman al course_downloader.process_course que spawna mas hilos
        # 1. whisper no es thread-safe https://github.com/openai/whisper/discussions/951
        # 2. muchas veces el uso de hilos en python no tiene provecho por el Global Interpreter Lock. usar procesos en tal caso.
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = {
                executor.submit(
                    download_course_videos, acronym, course_downloader
                ): acronym
                for acronym in course_acronyms
            }

        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing courses"
        ):
            acronym = futures[future]
            try:
                future.result()
                logging.info(f"Finished processing course: {acronym}")
            except Exception as e:
                logging.info(f"Error processing course {acronym}: {str(e)}")


if __name__ == "__main__":
    main()

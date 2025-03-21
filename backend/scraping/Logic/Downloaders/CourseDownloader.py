import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from ClassDownloader import ClassDownloader
from constants import BYTES_TO_GB


class CourseDownloader:
    def __init__(self, transcriber, base_url="https://open.fing.edu.uy/media/{course}/{course}_{nn}.mp4", db_path="../DB/Opens/", total_max_size=15 * BYTES_TO_GB):
        self.base_url = base_url
        self.transcriber = transcriber
        self.db_path = db_path
        self.total_max_size = total_max_size
        self.class_downloader = ClassDownloader(transcriber)

    def get_folder_size(self, path):
        return path.stat().st_size

    def process_course(self, course_name):
        total_downloaded = 0
        course_path = Path(self.db_path) / course_name
        course_path.mkdir(exist_ok=True)
        classes_file_path = course_path / "classes.txt"

        if not classes_file_path.exists():
            logging.info(f"No classes.txt found for {course_name}, skipping...")
            return

        with open(classes_file_path, "r") as file:
            class_numbers = [line.strip() for line in file if line.strip().isdigit()]

        folder_size = self.get_folder_size(course_path)
        file_count = 0

        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = []
            for nn in class_numbers:
                formatted_nn = nn.zfill(2)
                video_path = course_path / f"{course_name}_{formatted_nn}.mp4"
                video_url = self.base_url.format(course=course_name, nn=formatted_nn)

                # Initialize expected_size to a default value
                expected_size = 0
                try:
                    response = requests.head(video_url)
                    expected_size = int(response.headers.get('content-length', 0))
                except Exception as e:
                    logging.info(f"Failed to get expected size for {video_url}: {str(e)}")
                    continue  # Skip this video if we can't determine the expected size

                if total_downloaded >= self.total_max_size:
                    break

                futures.append(executor.submit(self.class_downloader.process_class, video_url, video_path, expected_size, course_name))

            for future in as_completed(futures):
                future.result()
                file_count += 1
                total_downloaded = self.get_folder_size(course_path)  # Recalculate total size
                if total_downloaded >= self.total_max_size:
                    break

        logging.info(f"Course: {course_name}, Files: {file_count}, Directory size: {folder_size / BYTES_TO_GB:.2f} GB")

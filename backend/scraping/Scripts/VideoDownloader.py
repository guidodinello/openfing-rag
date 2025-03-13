import requests
import os
from pathlib import Path
import cv2
from concurrent.futures import ThreadPoolExecutor, as_completed

from constants import BYTES_TO_GB

class VideoDownloader:
    def __init__(self, logger, transcriber, base_url="https://open.fing.edu.uy/media/{course}/{course}_{nn}.mp4",
                 db_path="../DB/Opens/", total_max_size=15 * BYTES_TO_GB):
        self.logger = logger
        self.transcriber = transcriber
        self.base_url = base_url
        self.db_path = db_path
        self.total_max_size = total_max_size

    def get_folder_size(self, path):
        total_size = 0
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        return total_size

    def download_video(self, url, path, expected_size):
        """Download or resume a video from a URL and save it to a specified path."""
        try:
            headers = {}
            existing_file_size = 0

            if path.exists():
                existing_file_size = os.path.getsize(path)
                if existing_file_size > 0:
                    if existing_file_size < expected_size:
                        headers = {'Range': f'bytes={existing_file_size}-'}
                        self.logger.log_message(f"Resuming download for {path} at byte {existing_file_size}")
                    else:
                        self.logger.log_message(f"Existing file size {existing_file_size / BYTES_TO_GB:.2f} GB is greater than or equal to expected {expected_size / BYTES_TO_GB:.2f} GB. Redownloading...")
                        os.remove(path)

            response = requests.get(url, stream=True, headers=headers)
            if response.status_code in [200, 206]:
                with open(path, 'ab' if existing_file_size > 0 else 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                actual_size = os.path.getsize(path)
                return actual_size
            else:
                self.logger.log_message(f"Failed to download {url}. Status code: {response.status_code}")
                return 0
        except requests.RequestException as e:
            self.logger.log_message(f"Failed to download {url}: {str(e)}")
            return 0

    def is_download_complete(self, file_path):
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return False
            ret, _ = cap.read()
            cap.release()
            return ret
        except Exception as e:
            self.logger.log_message(f"Error checking playability of {file_path}: {str(e)}")
            return False

    def validate_existing_file(self, video_path, expected_size):
        """Validate that a previously downloaded file matches the expected size and is playable."""
        actual_size = os.path.getsize(video_path)
        if actual_size != expected_size:
            self.logger.log_message(f"File {video_path} size mismatch: expected {expected_size / BYTES_TO_GB:.2f} GB, got {actual_size / BYTES_TO_GB:.2f} GB")
            return False
        if not self.is_download_complete(video_path):
            self.logger.log_message(f"File {video_path} is not playable.")
            return False
        return True

    def process_course(self, course_name):
        total_downloaded = 0
        course_path = Path(self.db_path) / course_name
        course_path.mkdir(exist_ok=True)
        classes_file_path = course_path / "classes.txt"

        if not classes_file_path.exists():
            self.logger.log_message(f"No classes.txt found for {course_name}, skipping...")
            return

        with open(classes_file_path, "r") as file:
            class_numbers = [line.strip() for line in file if line.strip().isdigit()]

        folder_size = self.get_folder_size(course_path)
        file_count = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
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
                    self.logger.log_message(f"Failed to get expected size for {video_url}: {str(e)}")
                    continue  # Skip this video if we can't determine the expected size

                if video_path.exists():
                    if not self.validate_existing_file(video_path, expected_size):
                        self.logger.log_message(f"File {video_path} failed validation, redownloading.")
                        os.remove(video_path)
                    else:
                        self.logger.log_message(f"File {video_path} passed validation checks.")
                        self.transcriber.transcribe_video(video_path, course_name)
                        continue

                if total_downloaded >= self.total_max_size:
                    break

                futures.append(executor.submit(self.download_video, video_url, video_path, expected_size))

            for future in as_completed(futures):
                actual_size = future.result()
                if actual_size > 0:
                    file_count += 1
                    folder_size += actual_size
                    total_downloaded += actual_size
                    if total_downloaded >= self.total_max_size:
                        break

                    if not self.is_download_complete(video_path):
                        self.logger.log_message(f"File {video_path} is not playable, skipping transcription.")
                        continue

                    self.transcriber.transcribe_video(video_path, course_name)

        self.logger.log_message(f"Course: {course_name}, Files: {file_count}, Directory size: {folder_size / BYTES_TO_GB:.2f} GB")

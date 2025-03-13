import logging
import os
from pathlib import Path

import cv2
import requests
from constants import BYTES_TO_GB
from Transcriber import Transcriber


class ClassDownloader:
    def __init__(
        self, transcriber: Transcriber, validation_log_file : str = "../DB/validation_test_pass.txt"
    ):
        self.transcriber = transcriber
        self.validation_log_file = Path(validation_log_file)
        self.validation_log_path = Path(self.validation_log_file)

    def load_validation_log(self):
        """Load the validation log file into a set for quick lookup."""
        if self.validation_log_path.exists():
            with open(self.validation_log_path, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f)
        return set()

    def log_validation_pass(self, video_path):
        """Log the video path in the validation log file."""
        with open(self.validation_log_path, "a", encoding="utf-8") as f:
            f.write(f"{video_path}\n")

    def validate_video_file(self, video_path, expected_size: int):
        """Validate that a previously downloaded file matches the expected size and is playable."""
        actual_size = Path(video_path).stat().st_size
        if actual_size != expected_size:
            logging.info(
                f"File {video_path} size mismatch: expected {expected_size / BYTES_TO_GB:.2f} GB, got {actual_size / BYTES_TO_GB:.2f} GB"
            )
            return False
        if not self.is_download_complete(video_path):
            logging.info(f"File {video_path} is not playable.")
            return False
        return True

    def download_video(self, url, path, expected_size):
        """Download or resume a video from a URL and save it to a specified path."""
        path = Path(path)
        try:
            headers = {}
            existing_file_size = 0

            if path.exists():
                existing_file_size = path.stat().st_size
                if existing_file_size > 0:
                    if existing_file_size < expected_size:
                        headers = {"Range": f"bytes={existing_file_size}-"}
                        logging.info(
                            f"Resuming download for {path} at byte {existing_file_size}"
                        )
                    else:
                        logging.info(
                            f"Existing file size {existing_file_size / BYTES_TO_GB:.2f} GB is greater than or equal to expected {expected_size / BYTES_TO_GB:.2f} GB. Redownloading..."
                        )
                        path.unlink()

            response = requests.get(url, stream=True, headers=headers)
            if response.status_code in [200, 206]:
                with open(path, "ab" if existing_file_size > 0 else "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                actual_size = path.stat().st_size
                return actual_size
            else:
                logging.info(
                    f"Failed to download {url}. Status code: {response.status_code}"
                )
                return 0
        except requests.RequestException as e:
            logging.info(f"Failed to download {url}: {str(e)}")
            return 0

    def is_download_complete(self, file_path):
        """Check if the downloaded file is complete and playable."""
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return False
            ret, _ = cap.read()
            cap.release()
            return ret
        except Exception as e:
            logging.info(
                f"Error checking playability of {file_path}: {str(e)}"
            )
            return False

    # TODO: no me gusta el nombre process. transcribe o algo asi tendria mas sentido 
    def process_class(self, video_url, video_path, expected_size, course_name):
        validation_log = self.load_validation_log()

        # Check if this video has already passed validation
        if str(video_path) in validation_log:
            logging.info(
                f"Skipping validation for {video_path}, already passed previously."
            )
            self.transcriber.transcribe_video(video_path, course_name)
            return

        # If the video exists, validate it
        if video_path.exists():
            if not self.validate_video_file(video_path, expected_size):
                logging.info(
                    f"File {video_path} failed validation, redownloading."
                )
                os.remove(video_path)
            else:
                logging.info(f"File {video_path} passed validation checks.")
                self.log_validation_pass(video_path)
                self.transcriber.transcribe_video(video_path, course_name)
                return

        # Download the video if it hasn't been validated
        actual_size = self.download_video(video_url, video_path, expected_size)
        if actual_size > 0:
            if not self.is_download_complete(video_path):
                logging.info(
                    f"File {video_path} is not playable, skipping transcription."
                )
                return
            self.log_validation_pass(video_path)
            self.transcriber.transcribe_video(video_path, course_name)

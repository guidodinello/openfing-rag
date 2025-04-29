import os
import logging
import requests
from pathlib import Path
from typing import Dict

from Constants.Constants import OPEN_FING_URL_MEDIA_URL, VIDEO_EXTENSION, TMP_DOWNLOAD_FOLDER


class VideoDownloader:
    def __init__(self):
        self.__logger = logging.getLogger(__name__)
        self.__BYTES_TO_GB = 1024 ** 3

    def is_video_downloaded(self, course_acronym: str, class_number: int) -> bool:
        video_path = self.__get_video_path(course_acronym, class_number)
        if video_path.exists():
            expected_size = self.__get_expected_file_size(self.__get_url(course_acronym, class_number))
            return self.__validate_existing_file(video_path, expected_size)
        return False

    def process_video(self, course_acronym: str, class_number: int) -> dict:
        video_path = self.__get_video_path(course_acronym, class_number)
        url = self.__get_url(course_acronym, class_number)
        expected_size = self.__get_expected_file_size(url)

        result = {
            "status": "unknown",
            "path": str(video_path),
            "error": None,
            "progress": 0,
        }

        if video_path.exists() and self.__validate_existing_file(video_path, expected_size):
            result["status"] = "exists_valid"
            return result

        try:
            downloaded_size = self.__download_video(url, video_path)
            if downloaded_size == expected_size:
                result["status"] = "completed"
                result["progress"] = 100
            else:
                result["status"] = "failed"
                result["error"] = "Size mismatch after download"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def __download_video(self, url: str, path: Path) -> int:
        headers = {}
        existing_file_size = 0

        if path.exists():
            existing_file_size = os.path.getsize(path)
            if existing_file_size > 0:
                headers = {'Range': f'bytes={existing_file_size}-'}

        response = requests.get(url, stream=True, headers=headers)
        if response.status_code in [200, 206]:
            total_size = int(response.headers.get('content-length', 0))
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'ab' if existing_file_size > 0 else 'wb') as f:
                downloaded = existing_file_size
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            return os.path.getsize(path)
        else:
            raise RuntimeError(f"Failed to download {url}, status code {response.status_code}")

    def __get_url(self, course_acronym, class_number):
        class_number_string = f"{class_number:02d}"
        return f"{OPEN_FING_URL_MEDIA_URL}{course_acronym}/{course_acronym}_{class_number_string}.{VIDEO_EXTENSION}"

    def __get_video_path(self, course_acronym, class_number):
        class_number_string = f"{class_number:02d}"
        filename = f"{course_acronym}_{class_number_string}.{VIDEO_EXTENSION}"
        return Path(TMP_DOWNLOAD_FOLDER) / course_acronym / filename

    def __get_expected_file_size(self, url):
        try:
            response = requests.head(url)
            return int(response.headers.get('content-length', 0))
        except requests.RequestException as e:
            self.__logger.error(f"Error getting file size: {str(e)}")
            return 0

    def __validate_existing_file(self, video_path, expected_size):
        try:
            actual_size = os.path.getsize(video_path)
            if actual_size != expected_size:
                self.__logger.warning(
                    f"File {video_path} size mismatch: expected {expected_size / self.__BYTES_TO_GB:.2f} GB, "
                    f"got {actual_size / self.__BYTES_TO_GB:.2f} GB"
                )
                return False
            return self.__is_video_playable(video_path)
        except Exception as e:
            self.__logger.error(f"Error validating file {video_path}: {str(e)}")
            return False

    def __is_video_playable(self, video_path):
        # Stubbed method: implement actual validation if needed
        return True

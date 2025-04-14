import asyncio
import aiohttp  
import logging
import requests
import os
from typing import Dict, Any, Optional
from Constants.Constants import OPEN_FING_URL_MEDIA_URL, VIDEO_EXTENSION, TMP_DOWNLOAD_FOLDER
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Dict


class VideoDownloader:
    def __init__(self):
        _instance= None
        _lock = threading.Lock()
        self.__logger = logging.getLogger(__name__)
        self.__current_download: Optional[Dict] = None  # Track current download
        self.__BYTES_TO_GB = 1024 ** 3
        self.__executor = ThreadPoolExecutor(max_workers=1)  # Single worker
        self.__download_lock = threading.Lock()  # Lock for download operations

    # def __new__(cls):
    #     if cls._instance is None:
    #         with cls._lock:
    #             if cls._instance is None:
    #                 cls._instance = super().__new__(cls)
    #     return cls._instance

    def process_video(self, course_acronym: str, class_number: int) -> dict:
        """Start video download process if no download is in progress"""
        video_path = self.__get_video_path(course_acronym, class_number)
        download_id = f"{course_acronym}_{class_number}"

        result = {
            "status": "unknown",
            "path": str(video_path),
            "error": None,
            "progress": 0,
            "download_id": download_id
        }

        try:
            if (self.__current_download and 
                self.__current_download["download_id"] == download_id):
                return self.__current_download

            url = self.__get_url(course_acronym, class_number)
            expected_size = self.__get_expected_file_size(url)

            if video_path.exists() and self.__validate_existing_file(video_path, expected_size):
                result["status"] = "exists_valid"
                return result

            with self.__download_lock:
                if self.__current_download and self.__current_download["status"] == "downloading":
                    result["status"] = "busy"
                    result["error"] = "Another download is in progress"
                    return result

                self.__current_download = {
                    "status": "downloading",
                    "progress": 0,
                    "total_size": expected_size,
                    "downloaded_size": 0,
                    "download_id": download_id,
                    "path": str(video_path)
                }

            self.__executor.submit(
                self.__download_video,
                url,
                video_path,
                download_id
            )

            return self.__current_download

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            return result

    def get_download_status(self) -> dict:
        """Get status of current/last download"""
        return self.__current_download if self.__current_download else {
            "status": "no_downloads",
            "progress": 0
        }

    def __download_video(self, url: str, path: Path, download_id: str) -> int:
        """Download video in background thread with progress tracking"""
        try:
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
                            # Update progress
                            with self.__download_lock:
                                self.__current_download.update({
                                    "progress": int((downloaded / total_size) * 100),
                                    "downloaded_size": downloaded,
                                    "status": "downloading"
                                })

                # Update final status
                with self.__download_lock:
                    self.__current_download["status"] = "completed"
                return os.path.getsize(path)
            else:
                with self.__download_lock:
                    self.__current_download["status"] = "failed"
                self.__logger.error(f"Failed to download {url}. Status code: {response.status_code}")
                return 0

        except Exception as e:
            with self.__download_lock:
                self.__current_download["status"] = "failed"
                self.__current_download["error"] = str(e)
            self.__logger.error(f"Failed to download {url}: {str(e)}")
            return 0

    def __get_url(self, course_acronym, class_number):
        """Generate the URL for the video."""
        class_number_string = f"{class_number:02d}"  # Zero-pad to 2 digits
        return f"{OPEN_FING_URL_MEDIA_URL}{course_acronym}/{course_acronym}_{class_number_string}.{VIDEO_EXTENSION}"
    
    def __get_video_path(self, course_acronym, class_number):
        """Generate the path where the video will be saved."""
        class_number_string = f"{class_number:02d}"
        filename = f"{course_acronym}_{class_number_string}.{VIDEO_EXTENSION}"
        return Path(TMP_DOWNLOAD_FOLDER) / course_acronym / filename
    
    def __get_expected_file_size(self, url):
        """Get the expected file size from the server."""
        try:
            response = requests.head(url)
            return int(response.headers.get('content-length', 0))
        except requests.RequestException as e:
            self.__logger.error(f"Error getting file size: {str(e)}")
            return 0
    
    def __validate_existing_file(self, video_path, expected_size):
        """Validate that a previously downloaded file matches the expected size and is playable."""
        try:
            actual_size = os.path.getsize(video_path)
            if actual_size != expected_size:
                self.__logger.warning(
                    f"File {video_path} size mismatch: expected {expected_size / self.__BYTES_TO_GB:.2f} GB, "
                    f"got {actual_size / self.__BYTES_TO_GB:.2f} GB"
                )
                return False
            if not self.__is_video_playable(video_path):
                self.__logger.warning(f"File {video_path} is not playable.")
                return False
            return True
        except Exception as e:
            self.__logger.error(f"Error validating file {video_path}: {str(e)}")
            return False
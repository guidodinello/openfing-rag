from Constants.Constants import OPEN_FING_URL_MEDIA_URL, VIDEO_EXTENSION, TMP_DOWNLOAD_FOLDER
import logging
import requests
import os
from pathlib import Path

class VideoDownloader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_video(self, course_acronym, class_number):
        """Main method to process a video: get URL, download, and validate."""
        try:
            url = self.get_url(course_acronym, class_number)
            video_path = self.get_video_path(course_acronym, class_number)
            expected_size = self.get_expected_file_size(url)
            
            if video_path.exists() and self.validate_existing_file(video_path, expected_size):
                ##TO DO, añadir validaciíon si esta o no en la base actual
                self.logger.info(f"Video already exists and is valid: {video_path}")
                return True
            
            actual_size = self.download_video(url, video_path)
            if actual_size == 0:
                return False
                
            return self.validate_existing_file(video_path, expected_size)
            
        except Exception as e:
            self.logger.error(f"Error processing video: {str(e)}")
            return False

    def get_url(self, course_acronym, class_number):
        """Generate the URL for the video."""
        class_number_string = f"{class_number:02d}"  # Zero-pad to 2 digits
        return f"{OPEN_FING_URL_MEDIA_URL}{course_acronym}/{course_acronym}_{class_number_string}.{VIDEO_EXTENSION}"

    def get_video_path(self, course_acronym, class_number):
        """Generate the path where the video will be saved."""
        class_number_string = f"{class_number:02d}"
        filename = f"{course_acronym}_{class_number_string}.{VIDEO_EXTENSION}"
        return Path(TMP_DOWNLOAD_FOLDER) / course_acronym / filename

    def get_expected_file_size(self, url):
        """Get the expected file size from the server."""
        try:
            response = requests.head(url)
            return int(response.headers.get('content-length', 0))
        except requests.RequestException as e:
            self.logger.error(f"Error getting file size: {str(e)}")
            return 0

    def download_video(self, url, path):
        """Download a video from a URL and save it to the specified path."""
        try:
            headers = {}
            existing_file_size = 0

            if path.exists():
                existing_file_size = os.path.getsize(path)
                expected_size = self.get_expected_file_size(url)
                
                if existing_file_size > 0:
                    if existing_file_size < expected_size:
                        headers = {'Range': f'bytes={existing_file_size}-'}
                        self.logger.info(f"Resuming download for {path} at byte {existing_file_size}")
                    else:
                        self.logger.info(f"Existing file size {existing_file_size / self.BYTES_TO_GB:.2f} GB is greater than or equal to expected {expected_size / self.BYTES_TO_GB:.2f} GB. Redownloading...")
                        os.remove(path)

            response = requests.get(url, stream=True, headers=headers)
            if response.status_code in [200, 206]:
                with open(path, 'ab' if existing_file_size > 0 else 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return os.path.getsize(path)
            else:
                self.logger.error(f"Failed to download {url}. Status code: {response.status_code}")
                return 0
        except requests.RequestException as e:
            self.logger.error(f"Failed to download {url}: {str(e)}")
            return 0

    #def is_video_playable(self, file_path):
    #    """Check if the downloaded video is playable."""
    #    try:
    #        cap = cv2.VideoCapture(str(file_path))
    #        if not cap.isOpened():
    #            return False
    #        ret, _ = cap.read()
    #        cap.release()
    #        return ret
    #    except Exception as e:
    #        self.logger.error(f"Error checking playability of {file_path}: {str(e)}")
    #        return False

    def validate_existing_file(self, video_path, expected_size):
        """Validate that a previously downloaded file matches the expected size and is playable."""
        try:
            actual_size = os.path.getsize(video_path)
            if actual_size != expected_size:
                self.logger.warning(
                    f"File {video_path} size mismatch: expected {expected_size / self.BYTES_TO_GB:.2f} GB, "
                    f"got {actual_size / self.BYTES_TO_GB:.2f} GB"
                )
                return False
            if not self.is_video_playable(video_path):
                self.logger.warning(f"File {video_path} is not playable.")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error validating file {video_path}: {str(e)}")
            return False
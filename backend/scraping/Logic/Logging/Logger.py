from pathlib import Path
from datetime import datetime
from constants import LOGGING_FOLDER

class Logger:
    def __init__(self, log_dir=LOGGING_FOLDER):
        today = datetime.now().strftime("%Y_%m_%d")
        self.log_file_path = Path(log_dir) / f"log_{today}.txt"
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_message(self, message):
        """Write a message to the log file. Creates the file if it doesn't exist."""
        try:
            with open(self.log_file_path, "a", encoding='utf-8') as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d")
                log_file.write(f"[{timestamp}] {message}\n")
        except IOError as e:
            print(f"Error writing to log file: {e}")
            raise

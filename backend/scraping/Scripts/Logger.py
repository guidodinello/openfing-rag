from pathlib import Path
from datetime import datetime

class Logger:
    def __init__(self, log_dir="../Logs"):
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = Path(log_dir) / f"log_{current_time}.txt"
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_message(self, message):
        """Write a message to the log file."""
        with open(self.log_file_path, "a") as log_file:
            log_file.write(message + "\n")

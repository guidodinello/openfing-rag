from pathlib import Path
from datetime import datetime
import inspect
from Constants.Constants import LOG_FOLDER  
class Logger:
    def __init__(self, log_dir=LOG_FOLDER):
        today = datetime.now().strftime("%Y_%m_%d")
        self.log_file_path = Path(log_dir) / f"log_{today}.txt"
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    def log_message(self, message):
        """Write a message to the log file. Creates the file if it doesn't exist."""
        try:
            caller_frame = inspect.currentframe().f_back
            file_name = caller_frame.f_code.co_filename
            line_number = caller_frame.f_lineno
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
                log_message = f"[{timestamp}] {file_name}:{line_number} - {message}"
                log_file.write(log_message + "\n") 
        except IOError as e:
            print(f"Error writing to log file: {e}")
            raise
    def write_on_file(self, file_path, message):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch(exist_ok=True)
        with open(file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(str(message) + "\n")
            
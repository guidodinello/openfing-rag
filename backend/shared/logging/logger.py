import logging
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from shared.config import get_settings

settings = get_settings()

CONSOLE_FORMAT = "%(levelname)s | %(name)s | %(message)s"
FILE_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    green = "\x1b[32m"
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: grey + FILE_FORMAT + reset,
        logging.INFO: green + FILE_FORMAT + reset,
        logging.WARNING: yellow + FILE_FORMAT + reset,
        logging.ERROR: red + FILE_FORMAT + reset,
        logging.CRITICAL: bold_red + FILE_FORMAT + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


@lru_cache
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with both file and console handlers.

    Args:
        name: The name of the logger (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """

    logger = logging.getLogger(name)

    logger.setLevel(settings.LOG.LEVEL)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG.LEVEL)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)

    # File handler - daily rotating log file
    logs_dir = Path(settings.LOG.DIR)
    logs_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(logs_dir / f"{today}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger


if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

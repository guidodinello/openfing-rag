import re
from pathlib import Path
from typing import Any

from services.transcriber.schemas.enums import WhisperModelSize
from shared.config.config import get_settings
from shared.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TranscriptionFileUtils:
    """Static utility methods for transcription file operations."""

    TRANSCRIBER_SUFFIXES = ["fasterwhisper", "openai", "whisperx"]

    @staticmethod
    def get_transcription_file_paths(course_code: str, lesson_number: int, model_size: WhisperModelSize) -> list[Path]:
        """Get all possible transcription file paths for a lesson."""
        transcriptions_dir = settings.TRANSCRIBER.OUTPUT_DIR / model_size.value / course_code.lower()

        paths = []
        for suffix in TranscriptionFileUtils.TRANSCRIBER_SUFFIXES:
            filename = f"{course_code.lower()}_{lesson_number:02d}_{model_size.value}_{suffix}.json"
            paths.append(transcriptions_dir / filename)

        return paths

    @staticmethod
    def find_existing_transcription_file(
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize,
    ) -> Path | None:
        """Find the first existing transcription file for a lesson."""
        for path in TranscriptionFileUtils.get_transcription_file_paths(course_code, lesson_number, model_size):
            if path.exists():
                return path
        return None

    @staticmethod
    def find_transcription_files_for_course(course_code: str, model_size: WhisperModelSize) -> list[int]:
        """Find all existing transcription files for a course and return lesson numbers."""
        transcriber_dir = settings.TRANSCRIBER.OUTPUT_DIR / model_size.value / course_code.lower()

        if not transcriber_dir.exists():
            return []

        lesson_numbers = set()

        # Pattern to match any transcriber implementation
        pattern = rf"{re.escape(course_code.lower())}_(\d{{1,2}})_{re.escape(model_size.value)}_\w+\.json"

        for file_path in transcriber_dir.glob("*.json"):
            if match := re.search(pattern, file_path.name):
                lesson_numbers.add(int(match.group(1)))

        return sorted(lesson_numbers)

    @staticmethod
    def load_transcription_from_file(
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize,
    ) -> dict[str, Any] | None:
        """Load transcription data from JSON file. Returns None if file doesn't exist."""
        file_path = TranscriptionFileUtils.find_existing_transcription_file(course_code, lesson_number, model_size)

        if not file_path:
            return None

        try:
            import json

            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load transcription file {file_path}: {e}")
            return None

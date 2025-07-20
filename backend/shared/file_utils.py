import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from shared.config import get_settings
from shared.enums import WhisperModelSize
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TranscriptionFileUtils:
    ## media files

    @staticmethod
    def extract_course_and_lesson_number_from_media_file(file_name: str) -> tuple[str, int]:
        lesson_path = Path(file_name).stem
        course_code, lesson_number = lesson_path.split("_")
        return course_code, int(lesson_number)

    @staticmethod
    def find_media_file(course_code: str, lesson_number: int) -> Path | None:
        media_course_folder = settings.TRANSCRIBER.INPUT_DIR / course_code.lower()
        pattern = f"{course_code.lower()}_{lesson_number:02d}.*"
        files = list(media_course_folder.glob(pattern))
        return files[0] if files else None

    @staticmethod
    def find_media_files(course_code: str | None) -> Iterator[Path]:
        media_course_folder = settings.TRANSCRIBER.INPUT_DIR
        pattern = "./*/*"
        if course_code is not None:
            course_code = course_code.lower()
            media_course_folder /= course_code
            pattern = f"{course_code}_*"

        return filter(lambda path: path.is_file(), media_course_folder.glob(pattern))

    ## transcription files

    @staticmethod
    def extract_course_and_lesson_number_from_transcription_file(file_name: str) -> tuple[str, int, str, str]:
        transcription_path = Path(file_name).stem
        course_code, lesson_number, model_size, transcriber_suffix = transcription_path.split("_")
        return course_code, int(lesson_number), model_size, transcriber_suffix

    @staticmethod
    def model_dir(model_size: WhisperModelSize) -> Path:
        return settings.TRANSCRIBER.OUTPUT_DIR / model_size.value

    @staticmethod
    def course_dir(model_size: WhisperModelSize, course_code: str) -> Path:
        return TranscriptionFileUtils.model_dir(model_size) / course_code.lower()

    @staticmethod
    def base_file_name(
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize,
    ) -> str:
        return f"{course_code.lower()}_{lesson_number:02d}_{model_size.value}"

    @staticmethod
    def generate_filename(
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize,
        transcriber_suffix: str,
    ) -> str:
        return f"{TranscriptionFileUtils.base_file_name(course_code, lesson_number, model_size)}_{transcriber_suffix}"

    @staticmethod
    def get_file_path(
        model_size: WhisperModelSize,
        course_code: str,
        lesson_number: int,
        transcriber_identifier: str,
    ) -> Path:
        filename = TranscriptionFileUtils.generate_filename(
            course_code,
            lesson_number,
            model_size,
            transcriber_identifier,
        )
        return TranscriptionFileUtils.course_dir(model_size, course_code) / f"{filename}.json"

    @staticmethod
    def save_transcription(
        result: dict[str, Any],
        model_size: WhisperModelSize,
        course_code: str,
        lesson_number: int,
        transcriber_suffix: str,
    ) -> Path:
        """Save transcription result to standardized location."""
        file_path = TranscriptionFileUtils.get_file_path(model_size, course_code, lesson_number, transcriber_suffix)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Saved faster-whisper transcription result to {file_path}")
        return file_path

    @staticmethod
    def find_transcription_file(
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize,
        transcriber_identifier: str | None = None,
    ) -> Path | None:
        """Find transcription file, optionally filtered by transcriber."""
        if transcriber_identifier:
            file_path = TranscriptionFileUtils.get_file_path(
                model_size,
                course_code,
                lesson_number,
                transcriber_identifier,
            )
            return file_path if file_path.exists() else None

        course_dir = TranscriptionFileUtils.course_dir(model_size, course_code)
        if not course_dir.exists():
            return None

        pattern = f"{TranscriptionFileUtils.base_file_name(course_code, lesson_number, model_size)}_*.json"
        files = list(course_dir.glob(pattern))
        return files[0] if files else None

    @staticmethod
    def load_transcription(
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize,
        transcriber_suffix: str | None = None,
    ) -> dict[str, Any] | None:
        """Load transcription data from file."""
        file_path = TranscriptionFileUtils.find_transcription_file(
            course_code,
            lesson_number,
            model_size,
            transcriber_suffix,
        )
        if not file_path:
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load transcription file {file_path}: {e}")
            return None

    @staticmethod
    def find_transcribed_course_lessons(
        model_size: WhisperModelSize,
        course_code: str,
        transcriber_suffix: str | None = None,
    ) -> list[int]:
        """Find all lesson numbers with transcriptions for a course."""
        course_dir = TranscriptionFileUtils.course_dir(model_size, course_code)
        if not course_dir.exists():
            return []

        suffix_pattern = transcriber_suffix or r"\w+"
        pattern = rf"{re.escape(course_code.lower())}_(\d{{1,2}})_{re.escape(model_size.value)}_{suffix_pattern}\.json"

        lesson_numbers = {
            int(match.group(1))
            for file_path in course_dir.glob("*.json")
            if (match := re.search(pattern, file_path.name))
        }

        return sorted(lesson_numbers)

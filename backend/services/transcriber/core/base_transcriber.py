import re
from pathlib import Path

from services.transcriber.core.file_utils import TranscriptionFileUtils
from services.transcriber.schemas.domain import LessonScanResult, TranscriptionResult
from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.config.config import get_settings
from shared.logging.logger import get_logger
from shared.utils import megabytes_to_bytes
from transcriber.core.asr.transcriber_protocol import TranscriberProtocol

logger = get_logger(__name__)
settings = get_settings()


class BaseTranscriptionService:
    """File-based transcription service that doesn't require database access."""

    def __init__(self, transcriber: TranscriberProtocol):
        self._transcriber = transcriber
        self.media_base_path = settings.TRANSCRIBER.INPUT_DIR
        self.output_base_path = settings.TRANSCRIBER.OUTPUT_DIR

    # === STATIC FILE OPERATIONS ===

    @staticmethod
    def find_available_lessons_by_size(course_code: str, max_file_size_mb: float | None = None) -> LessonScanResult:
        """Scan for available lesson files, optionally filtered by size and sorted by size."""
        try:
            lessons = BaseTranscriptionService._scan_course_folder(course_code)

            # Filter by size if specified
            if max_file_size_mb is not None:
                max_bytes = megabytes_to_bytes(max_file_size_mb)
                lessons = [le for le in lessons if le["file_size"] <= max_bytes]

            # Sort by file size (smallest first for local processing)
            lessons.sort(key=lambda x: x["file_size"])

            return LessonScanResult(
                success=True,
                message=f"Found {len(lessons)} lesson files for course {course_code}"
                + (f" (≤{max_file_size_mb}MB)" if max_file_size_mb else ""),
                lessons=lessons,
            )

        except Exception as e:
            logger.error(f"Error scanning lessons for {course_code}: {e}")
            return LessonScanResult(success=False, message=f"Failed to scan lessons: {str(e)}", lessons=[])

    # === INSTANCE METHODS (Need transcriber state) ===

    def create_transcription_file(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
        force_retranscribe: bool = False,
    ) -> tuple[bool, dict | None, str]:
        """Create transcription JSON file from audio."""
        if not force_retranscribe:
            existing_data = TranscriptionFileUtils.load_transcription_from_file(course_code, lesson_number, model_size)
            if existing_data:
                logger.info(
                    f"Transcription file already exists for {course_code} L{lesson_number} ({model_size.value})",
                )
                return True, existing_data, "Transcription file already exists"

        media_file = self._find_media_file(course_code, lesson_number)
        if not media_file:
            return False, None, f"No media file found for {course_code} lesson {lesson_number}"

        try:
            logger.info(f"Creating transcription file for {course_code} L{lesson_number} with {model_size.value}")
            result = self._transcriber.transcribe(model_size=model_size, language=language, audio_path=media_file)

            transcription_data = {
                **result,
                "course_code": course_code,
                "lesson_number": lesson_number,
                "model_size": model_size.value,
                "language": language.value,
                "source_file": str(media_file),
                "file_size_bytes": media_file.stat().st_size,
            }

            logger.info("Transcription file created successfully")
            return True, transcription_data, "Transcription file created successfully"

        except Exception as e:
            logger.error(f"Failed to create transcription file: {e}")
            return False, None, f"Transcription failed: {str(e)}"

    def transcribe_to_file_only(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize = WhisperModelSize.base,
        language: WhisperModelLanguage = WhisperModelLanguage.spanish,
        force_retranscribe: bool = False,
    ) -> TranscriptionResult:
        """Complete file-only transcription workflow."""
        success, data, message = self.create_transcription_file(
            course_code,
            lesson_number,
            model_size,
            language,
            force_retranscribe,
        )

        if success:
            return TranscriptionResult.success_result(
                message=message,
                transcription_id=None,
                data={
                    "course_code": course_code,
                    "lesson_number": lesson_number,
                    "transcribed": True,
                    "vectorized": False,
                    "text_length": len(data.get("text", "")) if data else 0,
                    "processing_time": data.get("processing_time", 0) if data else 0,
                },
            )
        else:
            return TranscriptionResult.failure_result(
                message,
                data={"course_code": course_code, "lesson_number": lesson_number},
            )

    # === PRIVATE HELPERS ===

    def _find_media_file(self, course_code: str, lesson_number: int) -> Path | None:
        """Find media file for given course and lesson."""
        course_dir = self.media_base_path / course_code
        if not course_dir.exists():
            return None

        file_pattern = f"{course_code}_{lesson_number:02d}"
        for file_path in course_dir.iterdir():
            if file_path.is_file() and file_path.stem == file_pattern:
                return file_path
        return None

    @staticmethod
    def _scan_course_folder(course_code: str) -> list[dict]:
        """Scan folder for lesson files and return lesson data."""
        lessons = []
        extensions = [".mp3", ".m4a", ".wav", ".flac", ".mp4", ".mkv", ".avi", ".opus"]

        base_path = settings.TRANSCRIBER.INPUT_DIR
        lesson_files = base_path.rglob(f"*/{course_code}/*")
        logger.debug(list(lesson_files))

        for file_path in lesson_files:
            if not file_path.is_file() or file_path.suffix.lower() not in extensions:
                continue

            lesson_number = BaseTranscriptionService._extract_lesson_number(file_path.stem, course_code)
            if lesson_number:
                lessons.append(
                    {
                        "lesson_number": lesson_number,
                        "filename": file_path.name,
                        "file_size": file_path.stat().st_size,
                        "file_path": str(file_path),
                        "extension": file_path.suffix,
                    },
                )

        return lessons

    @staticmethod
    def _extract_lesson_number(filename: str, course_code: str) -> int | None:
        """Extract lesson number from filename."""
        if match := re.search(rf"{re.escape(course_code.lower())}_(\d{{1,2}})", filename.lower()):
            return int(match.group(1))
        return None

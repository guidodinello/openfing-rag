import re
from pathlib import Path

from sqlalchemy.orm import Session

from services.transcriber.schemas.domain import LessonScanResult, TranscriptionListResult, TranscriptionResult
from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.config.config import get_settings
from shared.database.models.rag.lesson import Lesson
from shared.database.models.rag.transcription import Transcription
from shared.database.repositories.lesson_repository import LessonRepository
from shared.database.repositories.transcription_repository import TranscriptionRepository
from shared.database.repositories.vector_repository import VectorRepository
from shared.logging.logger import get_logger
from shared.utils import normalize_json
from transcriber.core.asr.transcriber_protocol import TranscriberProtocol

logger = get_logger(__name__)
settings = get_settings()


class TranscriptionService:
    def __init__(
        self,
        db: Session,
        lesson_repo: LessonRepository,
        transcription_repo: TranscriptionRepository,
        vector_repo: VectorRepository,
        transcriber: TranscriberProtocol,
    ):
        self.db = db
        self.lesson_repo = lesson_repo
        self.transcription_repo = transcription_repo
        self.vector_repo = vector_repo
        self._transcriber = transcriber
        self.media_base_path = settings.TRANSCRIBER.INPUT_DIR

    # ==== PRIMARY WORKFLOWS ====

    def only_transcribe(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize = WhisperModelSize.base,
        language: WhisperModelLanguage = WhisperModelLanguage.spanish,
    ) -> TranscriptionResult:
        """Transcribe audio file without database operations - just generate JSON files."""
        try:
            media_file = self._find_media_file(course_code, lesson_number)
            if not media_file:
                logger.error(f"No media file found for {course_code} lesson {lesson_number}")
                return TranscriptionResult.failure_result(
                    f"No media file found for {course_code} lesson {lesson_number}",
                    data={"course_code": course_code, "lesson_number": lesson_number},
                )

            # Perform transcription
            result = self._transcriber.transcribe(model_size=model_size, language=language, audio_path=media_file)

            # Build metadata (but don't save to DB)
            _ = self._build_transcription_metadata(result, media_file)

            logger.info(f"Transcription completed for {course_code} lesson {lesson_number}")
            logger.info(f"Text length: {len(result['text'])} characters")
            logger.info(f"Processing time: {result.get('processing_time', 0):.2f}s")

            return TranscriptionResult.success_result(
                message="Transcription completed (file-only mode)",
                transcription_id=None,  # No DB ID
                data={
                    "course_code": course_code,
                    "lesson_number": lesson_number,
                    "transcribed": True,
                    "vectorized": False,
                    "text_length": len(result["text"]),
                    "processing_time": result.get("processing_time", 0),
                },
            )

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return TranscriptionResult.failure_result(
                f"Transcription failed: {str(e)}",
                data={"course_code": course_code, "lesson_number": lesson_number},
            )

    def transcribe_lesson(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize = WhisperModelSize.base,
        language: WhisperModelLanguage = WhisperModelLanguage.spanish,
        force_retranscribe: bool = False,
        force_revectorize: bool = False,
    ) -> TranscriptionResult:
        """Complete transcription workflow: audio → text → vectors."""
        try:
            lesson = self.lesson_repo.get_with_course(course_code, lesson_number)
            if not lesson:
                return TranscriptionResult.failure_result(
                    f"Lesson {lesson_number} not found for course {course_code}. Please update using the scraper.",
                    data={"course_code": course_code, "lesson_number": lesson_number},
                )

            transcription_id, was_transcribed = self._ensure_transcription_exists(
                lesson,
                course_code,
                lesson_number,
                model_size,
                language,
                force_retranscribe,
            )
            if not transcription_id:
                return TranscriptionResult.failure_result(
                    f"Failed to transcribe {course_code} lesson {lesson_number}",
                    data={"course_code": course_code, "lesson_number": lesson_number},
                )

            was_vectorized = self._ensure_vectors_exist(transcription_id, force_revectorize)

            self.db.commit()

            return self._create_success_response(
                transcription_id,
                course_code,
                lesson_number,
                was_transcribed,
                was_vectorized,
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Transcription workflow failed: {e}")
            return TranscriptionResult.failure_result(f"Transcription failed: {str(e)}")

    def get_transcription(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize | None = None,
    ) -> TranscriptionResult:
        """Get existing transcription by course and lesson."""
        transcription = self.transcription_repo.get_by_course_lesson_and_model(course_code, lesson_number, model_size)

        if not transcription:
            return TranscriptionResult.failure_result(
                f"No transcription found for {course_code} lesson {lesson_number}",
            )

        return TranscriptionResult.success_result(
            message="Transcription retrieved",
            transcription_id=transcription.id,
            data=self._format_transcription_detail(transcription),
        )

    def list_transcriptions(
        self,
        course_code: str | None = None,
        unvectorized_only: bool = False,
    ) -> TranscriptionListResult:
        """List transcriptions with optional filtering."""
        try:
            transcriptions = self.transcription_repo.get_filtered_transcriptions(
                course_code=course_code,
                unvectorized_only=unvectorized_only,
            )

            transcription_list = [self._format_transcription_summary(t) for t in transcriptions]
            vectorized_count = sum(1 for t in transcription_list if t["is_vectorized"])

            return TranscriptionListResult(
                success=True,
                message=f"Found {len(transcription_list)} transcriptions",
                data={
                    "transcriptions": transcription_list,
                    "total_count": len(transcription_list),
                    "vectorized_count": vectorized_count,
                    "unvectorized_count": len(transcription_list) - vectorized_count,
                },
            )
        except Exception as e:
            logger.error(f"Error listing transcriptions: {e}")
            return TranscriptionListResult(
                success=False,
                message=f"Failed to list transcriptions: {str(e)}",
                data={"transcriptions": [], "total_count": 0},
            )

    def vectorize_transcription(self, transcription_id: int) -> TranscriptionResult:
        """Add existing transcription to vector store."""
        try:
            if not self.transcription_repo.get_by_id(transcription_id):
                return TranscriptionResult.failure_result(f"Transcription {transcription_id} not found")

            vector_ids = self.vector_repo.upsert_transcription(transcription_id)
            self.db.commit()

            return TranscriptionResult.success_result(
                message=f"Vectorized into {len(vector_ids)} chunks",
                transcription_id=transcription_id,
                data={"vector_chunks": len(vector_ids)},
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Vectorization failed: {e}")
            return TranscriptionResult.failure_result(f"Vectorization failed: {str(e)}")

    def find_available_lessons(self, course_code: str) -> LessonScanResult:
        """Scan course folder and return available lessons with their files."""
        try:
            course_folder = self.media_base_path / course_code

            if not course_folder.exists():
                return LessonScanResult(
                    success=True,
                    message=f"No lesson files found - directory {course_folder} does not exist",
                    lessons=[],
                )

            lessons = self._scan_course_folder(course_folder, course_code)
            return LessonScanResult(
                success=True,
                message=f"Found {len(lessons)} lesson files for course {course_code}",
                lessons=lessons,
            )

        except Exception as e:
            logger.error(f"Error scanning lessons for {course_code}: {e}")
            return LessonScanResult(success=False, message=f"Failed to scan lessons: {str(e)}", lessons=[])

    # ==== PRIVATE HELPERS ====

    def _ensure_transcription_exists(
        self,
        lesson: Lesson,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
        force_retranscribe: bool,
    ) -> tuple[int | None, bool]:
        """Ensure transcription exists, create if needed. Returns (transcription_id, was_created)."""
        if not force_retranscribe:
            existing = self.transcription_repo.get_by_lesson_and_model(lesson.id, model_size)
            if existing:
                logger.info(f"Skipping transcription as it already exists. {existing.id}")
                return existing.id, False

        media_file = self._find_media_file(course_code, lesson_number)
        if not media_file:
            logger.error(f"No media file found for {course_code} lesson {lesson_number}")
            return None, False

        transcription_id = self._create_transcription(lesson.id, media_file, model_size, language)
        return transcription_id, True

    def _ensure_vectors_exist(self, transcription_id: int, force_revectorize: bool) -> bool:
        """Ensure vectors exist for transcription. Returns whether vectorization occurred."""
        if not force_revectorize and self.transcription_repo.is_vectorized(transcription_id):
            logger.info(f"Transcription {transcription_id} already vectorized")
            return False

        try:
            if force_revectorize:
                self.vector_repo.delete_by_transcription(transcription_id)

            vector_ids = self.vector_repo.upsert_transcription(transcription_id)
            logger.info(f"Created {len(vector_ids)} vector chunks")
            return True
        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            return False

    def _create_transcription(
        self,
        lesson_id: int,
        media_file: Path,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
    ) -> int:
        """Perform actual transcription and save to database."""
        result = self._transcriber.transcribe(model_size=model_size, language=language, audio_path=media_file)

        metadata = self._build_transcription_metadata(result, media_file)

        ## TODO: we should consider, only update if it matches another one with the same
        # model_size and language, it shouldnt overwrite if those not match
        transcription = self.transcription_repo.create_or_update_for_lesson(
            lesson_id=lesson_id,
            content=result["text"],
            metadata=metadata,
        )

        logger.info(f"Created transcription {transcription.id}")
        return transcription.id

    def _find_media_file(self, course_code: str, lesson_number: int) -> Path | None:
        """Find audio/video file for transcription."""
        course_dir = self.media_base_path / course_code
        if not course_dir.exists():
            return None

        file_pattern = f"{course_code}_{lesson_number:02d}"

        for file_path in course_dir.iterdir():
            if file_path.is_file() and file_path.stem == file_pattern:
                return file_path

        return None

    def _build_transcription_metadata(self, transcription_result: dict, media_file: Path) -> dict:
        """Build metadata dict for transcription record."""
        segments = transcription_result.get("segments", [])

        return {
            **normalize_json(self._transcriber.model_info(), prefix="transcriber"),
            "transcriber_model_size": transcription_result.get("model_size"),
            "language": transcription_result.get("language"),
            "duration_seconds": segments[-1].get("end", 0.0) if segments else 0.0,
            "segments_count": transcription_result.get("segments_count", 0),
            "content_length": len(transcription_result.get("text", "")),
            "processing_time": transcription_result.get("processing_time", 0.0),
            "source_file": str(media_file),
            "file_size_bytes": media_file.stat().st_size,
            "vectorized": False,
            "created_by": __name__,
        }

    def _format_transcription_detail(self, transcription: Transcription) -> dict:
        """Format transcription for detailed API response."""
        return {
            "id": transcription.id,
            "content": transcription.content,
            "metadata": transcription.transcription_metadata,
            "lesson": {
                "id": transcription.lesson.id,
                "number": transcription.lesson.number,
                "title": transcription.lesson.title,
                "course_code": transcription.lesson.course.code,
            },
        }

    def _format_transcription_summary(self, transcription: Transcription) -> dict:
        """Format transcription for list API response."""
        return {
            "id": transcription.id,
            "lesson_id": transcription.lesson_id,
            "course_code": transcription.lesson.course.code,
            "lesson_number": transcription.lesson.number,
            "lesson_title": transcription.lesson.title,
            "content_length": len(transcription.content) if transcription.content else 0,
            "model_size": transcription.transcription_metadata.get("transcriber_model_size"),
            "package": transcription.transcription_metadata.get("transcriber_package_name"),
            "language": transcription.transcription_metadata.get("language"),
            "is_vectorized": transcription.transcription_metadata.get("vectorized", False),
            "created_at": transcription.created_at.isoformat() if transcription.created_at else None,
        }

    def _create_success_response(
        self,
        transcription_id: int,
        course_code: str,
        lesson_number: int,
        was_transcribed: bool,
        was_vectorized: bool,
    ) -> TranscriptionResult:
        """Build success response based on what actions were performed."""
        actions = []
        if was_transcribed:
            actions.append("transcribed")
        if was_vectorized:
            actions.append("vectorized")

        if not actions:
            message = "Transcription already exists and is vectorized"
        else:
            message = f"Successfully {' and '.join(actions)}"

        return TranscriptionResult.success_result(
            message=message,
            transcription_id=transcription_id,
            data={
                "course_code": course_code,
                "lesson_number": lesson_number,
                "transcribed": was_transcribed,
                "vectorized": was_vectorized,
            },
        )

    def _scan_course_folder(self, course_folder: Path, course_code: str) -> list[dict]:
        """Scan folder for lesson files and return lesson data."""
        lessons = []
        extensions = [".mp3", ".m4a", ".wav", ".flac", ".mp4", ".mkv", ".avi", ".opus"]

        logger.debug(f"Scanning folder {course_folder}")
        for file_path in course_folder.iterdir():
            if not file_path.is_file() or file_path.suffix.lower() not in extensions:
                continue

            lesson_number = self._extract_lesson_number(file_path.stem, course_code)
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
                logger.debug(f"Found lesson {lesson_number} in {file_path}")

        return sorted(lessons, key=lambda x: x["lesson_number"])

    def _extract_lesson_number(self, filename: str, course_code: str) -> int | None:
        """Extract lesson number from filename."""
        if match := re.search(pattern=rf"{re.escape(course_code.lower())}_(\d{{1,2}})", string=filename.lower()):
            return int(match.group(1))

        return None

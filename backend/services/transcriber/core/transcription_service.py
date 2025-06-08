from pathlib import Path

from sqlalchemy.orm import Session

from services.transcriber.core.transcriber import Transcriber
from services.transcriber.schemas.domain import LessonScanResult, TranscriptionListResult, TranscriptionResult
from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.config.config import get_settings
from shared.database.repositories.course_repository import CourseRepository
from shared.database.repositories.lesson_repository import LessonRepository
from shared.database.repositories.transcription_repository import TranscriptionRepository
from shared.database.repositories.vector_repository import VectorRepository
from shared.logging.logger import get_logger
from shared.utils import deep_get

logger = get_logger(__name__)
settings = get_settings()


class TranscriptionService:
    def __init__(
        self,
        db: Session,
        course_repo: CourseRepository,
        lesson_repo: LessonRepository,
        transcription_repo: TranscriptionRepository,
        vector_repo: VectorRepository,
    ):
        self.db = db
        self.course_repo = course_repo
        self.lesson_repo = lesson_repo
        self.transcription_repo = transcription_repo
        self.vector_repo = vector_repo

        self.media_base_path = Path(settings.TRANSCRIBER.INPUT_DIR)
        self.output_dir = Path(settings.TRANSCRIBER.OUTPUT_DIR)

        logger.info("TranscriptionService initialized")

    def transcribe_lesson(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize = WhisperModelSize.base,
        language: WhisperModelLanguage = WhisperModelLanguage.spanish,
        force_retranscribe: bool = False,
        force_revectorize: bool = False,
    ) -> TranscriptionResult:
        """Transcribe a lesson audio/video file."""
        try:
            lesson = self.lesson_repo.get_with_course(course_code, lesson_number)
            if not lesson:
                return TranscriptionResult.failure_result(
                    f"Lesson {lesson_number} not found for course {course_code}. Please update using the scraper.",
                    data={"course_code": course_code, "lesson_number": lesson_number},
                )

            transcription_id, transcribed = self._handle_transcription(
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

            vectorized = self._handle_vectorization(transcription_id, force_revectorize)

            self.db.commit()

            return self._build_success_response(transcription_id, course_code, lesson_number, transcribed, vectorized)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Transcription operation failed: {e}")
            return TranscriptionResult.failure_result(
                f"Transcription operation failed: {str(e)}",
                data={"course_code": course_code, "lesson_number": lesson_number},
            )

    def revectorize_transcription(self, transcription_id: int) -> TranscriptionResult:
        """Force revectorization of a specific transcription."""
        try:
            if not self.transcription_repo.exists(transcription_id):
                return TranscriptionResult.failure_result(
                    f"Transcription {transcription_id} not found",
                    data={"transcription_id": transcription_id},
                )

            self.vector_repo.delete_by_transcription(transcription_id)
            vector_ids = self.vector_repo.ingest_transcription(transcription_id)
            self.db.commit()

            return TranscriptionResult.success_result(
                message=f"Revectorized transcription into {len(vector_ids)} chunks",
                transcription_id=transcription_id,
                data={"vector_chunks": len(vector_ids)},
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Revectorization failed: {e}")
            return TranscriptionResult.failure_result(
                f"Revectorization failed: {str(e)}",
                data={"transcription_id": transcription_id},
            )

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

            transcription_list = [self._format_transcription_data(t) for t in transcriptions]
            vectorized_count = sum(1 for t in transcription_list if t["is_vectorized"])

            filter_desc = f" for course {course_code}" if course_code else ""
            filter_desc += " (unvectorized only)" if unvectorized_only else ""

            return TranscriptionListResult(
                success=True,
                message=f"Found {len(transcription_list)} transcriptions{filter_desc}",
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
                data={"transcriptions": [], "total_count": 0, "error": str(e)},
            )

    def get_transcription(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize | None = None,
    ) -> TranscriptionResult:
        try:
            transcription = self.transcription_repo.get_by_course_lesson_and_model(
                course_code,
                lesson_number,
                model_size,
            )
            if not transcription:
                return TranscriptionResult.failure_result(
                    f"No transcription found for {course_code=}, {lesson_number=}, "
                    f"model_size={model_size.value if model_size else None}",
                    data={"course_code": course_code, "lesson_number": lesson_number},
                )

            return TranscriptionResult.success_result(
                message="Transcription found",
                transcription_id=transcription.id,
                data={
                    "id": transcription.id,
                    "content": transcription.content,
                    "metadata": transcription.transcription_metadata,
                    "lesson": {
                        "id": transcription.lesson.id,
                        "number": transcription.lesson.number,
                        "title": transcription.lesson.title,
                        "course_code": transcription.lesson.course.code,
                    },
                },
            )

        except Exception as e:
            logger.error(f"Error retrieving transcription: {e}")
            return TranscriptionResult.failure_result(
                f"Error retrieving transcription: {str(e)}",
                data={"course_code": course_code, "lesson_number": lesson_number},
            )

    def vectorize_transcription(self, transcription_id: int) -> TranscriptionResult:
        """Vectorize a specific transcription."""
        try:
            if not self.transcription_repo.exists(transcription_id):
                return TranscriptionResult.failure_result(
                    f"Transcription {transcription_id} not found",
                    data={"transcription_id": transcription_id},
                )

            vector_ids = self.vector_repo.ingest_transcription(transcription_id)
            self.db.commit()

            return TranscriptionResult.success_result(
                message=f"Vectorized transcription into {len(vector_ids)} chunks",
                transcription_id=transcription_id,
                data={"vector_chunks": len(vector_ids)},
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Vectorization failed: {e}")
            return TranscriptionResult.failure_result(
                f"Vectorization failed: {str(e)}",
                data={"transcription_id": transcription_id},
            )

    def _scan_course_folder(self, course_folder: Path, course_code: str) -> list[dict]:
        """Scan folder for lesson files and return lesson data."""
        lessons = []
        extensions = [".mp3", ".m4a", ".wav", ".flac", ".mp4", ".mkv", ".avi"]

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

        return sorted(lessons, key=lambda x: x["lesson_number"])

    def _extract_lesson_number(self, filename: str, course_code: str) -> int | None:
        """Extract lesson number from filename."""
        import re

        filename = filename.lower()
        course_code = course_code.lower()

        patterns = [
            rf"{re.escape(course_code)}_(\d{{1,2}})",  # course_XX
            r"^(\d{1,2})(?:_|\.)",  # number at start
            r"_(\d{1,2})$",  # number at end
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return int(match.group(1))

        return None

    def _find_media_file(self, course_code: str, lesson_number: int) -> Path | None:
        """Find media file for a course and lesson."""
        base_folder = self.media_base_path / course_code

        if not base_folder.exists():
            logger.error(f"Course folder not found: {base_folder}")
            return None

        file_pattern = f"{course_code}_{lesson_number:02d}"

        for file_path in base_folder.iterdir():
            if file_path.is_file() and file_path.stem == file_pattern:
                logger.info(f"Found media file: {file_path}")
                return file_path

        logger.error(f"No media file found matching pattern: {file_pattern}.*")
        return None

    ## TODO: return a transcription dataclass?
    def _format_transcription_data(self, transcription) -> dict:
        """Format single transcription for API response."""
        return {
            "id": transcription.id,
            "lesson_id": transcription.lesson_id,
            "course_code": transcription.lesson.course.code,
            "lesson_number": transcription.lesson.number,
            "lesson_title": transcription.lesson.title,
            "content_length": len(transcription.content) if transcription.content else 0,
            "model_size": transcription.transcription_metadata.get("model_size"),
            "language": transcription.transcription_metadata.get("language"),
            "is_vectorized": transcription.transcription_metadata.get("vectorized", False),
            "created_at": transcription.created_at.isoformat() if transcription.created_at else None,
        }

    def _handle_transcription(
        self,
        lesson,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
        force_retranscribe: bool,
    ) -> tuple[int | None, bool]:
        """Handle transcription logic, return (transcription_id, was_transcribed)."""
        ## TODO: we should retrieve the one made for this model_size and language not the latest
        existing = self.transcription_repo.get_latest_by_lesson_id(lesson.id)

        if existing and not force_retranscribe:
            logger.info(f"Using existing transcription {existing.id}")
            return existing.id, False

        # Need to transcribe
        media_file = self._find_media_file(course_code, lesson_number)
        if not media_file:
            logger.error(f"Media file not found for {course_code=} lesson {lesson_number=}")
            return None, False

        transcription_id = self._perform_transcription(lesson.id, media_file, model_size, language)
        return transcription_id, True

    def _perform_transcription(
        self,
        lesson_id: int,
        media_file: Path,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
    ) -> int:
        transcriber = Transcriber(
            audio_path=str(media_file),
            output_dir=str(self.output_dir),
            model_size=model_size,
            language=language,
        )

        result = transcriber.transcribe()
        metadata = self._build_transcription_metadata(result, media_file)

        ## TODO: we should consider, only update if it matches another one with the same
        # model_size and language, it shouldnt overwrite if those not match
        transcription = self.transcription_repo.create_or_update_for_lesson(
            lesson_id=lesson_id,
            content=result["text"],
            metadata=metadata,
        )

        logger.info(f"Transcription completed with ID: {transcription.id}")
        return transcription.id

    def _build_transcription_metadata(
        self,
        transcription_result: dict,
        media_file: Path,
    ) -> dict:
        segments = transcription_result.get("segments", [])

        return {
            # ASR Model Info
            "asr_model": "whisper",
            "asr_model_size": deep_get(transcription_result, "asr_model", "model", "size", default="unknown"),
            "asr_language": transcription_result.get("language"),
            # Content Metrics
            "duration_seconds": segments[-1].get("end", 0.0) if segments else 0.0,
            "segments_count": len(segments),
            "content_length": len(transcription_result.get("text", "")),
            # Processing Info
            "processing_time": transcription_result.get("processing_time", 0.0),
            "source_file": str(media_file),
            "file_size_bytes": media_file.stat().st_size,
            # Vectorization Status
            "vectorized": False,
            "embedding_model": None,
            # System Info
            "created_by": "transcription_service",
        }

    def _handle_vectorization(self, transcription_id: int, force_revectorize: bool) -> bool:
        """Handle vectorization logic, return whether vectorization occurred."""
        if not self._should_vectorize(transcription_id, force_revectorize):
            logger.info(f"Transcription {transcription_id} already vectorized, skipping")
            return False

        try:
            if force_revectorize:
                logger.info(f"Force revectorize: removing existing vectors for transcription {transcription_id}")
                self.vector_repo.delete_by_transcription(transcription_id)

            vector_ids = self.vector_repo.ingest_transcription(transcription_id)
            logger.info(f"Added transcription to vector store: {len(vector_ids)} chunks")
            return True

        except Exception as e:
            logger.error(f"Failed to add to vector store: {e}")
            return False

    def _should_vectorize(self, transcription_id: int, force_revectorize: bool) -> bool:
        if force_revectorize:
            return True
        return not self.transcription_repo.is_vectorized(transcription_id)

    def _build_success_response(
        self,
        transcription_id: int,
        course_code: str,
        lesson_number: int,
        transcribed: bool,
        vectorized: bool,
    ) -> TranscriptionResult:
        actions = []
        if transcribed:
            actions.append("transcribed")
        if vectorized:
            actions.append("vectorized")

        if not actions:
            message = "transcription_already_exists_and_vectorized"
        else:
            message = f"transcription_{'_and_'.join(actions)}"

        return TranscriptionResult.success_result(
            message=message,
            transcription_id=transcription_id,
            data={
                "course_code": course_code,
                "lesson_number": lesson_number,
                "transcribed": transcribed,
                "vectorized": vectorized,
            },
        )

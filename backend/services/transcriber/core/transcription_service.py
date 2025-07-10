from sqlalchemy.orm import Session

from services.transcriber.core.base_transcriber import BaseTranscriptionService
from services.transcriber.core.file_utils import TranscriptionFileUtils
from services.transcriber.schemas.domain import TranscriptionListResult, TranscriptionResult
from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.database.repositories import LessonRepository, TranscriptionRepository, VectorRepository
from shared.logging.logger import get_logger
from shared.utils import normalize_json
from transcriber.core.asr.transcriber_protocol import TranscriberProtocol

logger = get_logger(__name__)


class TranscriptionService(BaseTranscriptionService):
    def __init__(
        self,
        db: Session,
        lesson_repo: LessonRepository,
        transcription_repo: TranscriptionRepository,
        vector_repo: VectorRepository,
        transcriber: TranscriberProtocol,
    ):
        super().__init__(transcriber)
        self.db = db
        self.lesson_repo = lesson_repo
        self.transcription_repo = transcription_repo
        self.vector_repo = vector_repo

    # === DATABASE OPERATIONS ===

    def save_transcription_to_db(
        self,
        course_code: str,
        lesson_number: int,
        transcription_data: dict,
        force_update: bool = False,
    ) -> tuple[bool, int | None, str]:
        """Save transcription data to database."""
        try:
            lesson = self.lesson_repo.get_with_course(course_code, lesson_number)
            if not lesson:
                return (
                    False,
                    None,
                    f"Lesson {lesson_number} not found for course {course_code}. Please update using the scraper.",
                )

            model_size = WhisperModelSize(transcription_data.get("model_size"))
            existing = self.transcription_repo.get_by_lesson_and_model(lesson.id, model_size)

            if existing and not force_update:
                logger.info(f"Transcription already exists in database: {existing.id}")
                return True, existing.id, "Transcription already exists in database"

            metadata = self._build_transcription_metadata(transcription_data)
            transcription = self.transcription_repo.create_or_update_for_lesson(
                lesson_id=lesson.id,
                content=transcription_data.get("text", ""),
                metadata=metadata,
            )

            logger.info(f"Saved transcription to database: {transcription.id}")
            return True, transcription.id, "Transcription saved to database"

        except Exception as e:
            logger.error(f"Failed to save transcription to database: {e}")
            return False, None, f"Database save failed: {str(e)}"

    def ensure_transcription_vectorized(
        self,
        transcription_id: int,
        force_revectorize: bool = False,
    ) -> tuple[bool, str]:
        """Ensure transcription is vectorized."""
        try:
            if not force_revectorize and self.transcription_repo.is_vectorized(transcription_id):
                return False, "Already vectorized"

            if force_revectorize:
                self.vector_repo.delete_by_transcription(transcription_id)

            vector_ids = self.vector_repo.upsert_transcription(transcription_id)
            logger.info(f"Created {len(vector_ids)} vector chunks")
            return True, f"Vectorized into {len(vector_ids)} chunks"

        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            return False, f"Vectorization failed: {str(e)}"

    # === WORKFLOW METHODS ===

    def save_transcription_from_file_to_db(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize = WhisperModelSize.base,
        force_update: bool = False,
        force_revectorize: bool = False,
    ) -> TranscriptionResult:
        """Load transcription from file and save to database with vectorization."""
        try:
            transcription_data = TranscriptionFileUtils.load_transcription_from_file(
                course_code,
                lesson_number,
                model_size,
            )
            if not transcription_data:
                return TranscriptionResult.failure_result(
                    f"No transcription file found for {course_code=} {lesson_number=} with {model_size.value=}",
                )

            db_success, transcription_id, db_message = self.save_transcription_to_db(
                course_code,
                lesson_number,
                transcription_data,
                force_update,
            )

            if not db_success or transcription_id is None:
                return TranscriptionResult.failure_result(db_message)

            was_vectorized, vector_message = self.ensure_transcription_vectorized(transcription_id, force_revectorize)
            self.db.commit()

            return TranscriptionResult.success_result(
                message=f"Saved to database and {vector_message.lower()}",
                transcription_id=transcription_id,
                data={
                    "course_code": course_code,
                    "lesson_number": lesson_number,
                    "transcribed": True,
                    "vectorized": was_vectorized,
                },
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save transcription from file: {e}")
            return TranscriptionResult.failure_result(f"Failed to save transcription: {str(e)}")

    def transcribe_lesson(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize = WhisperModelSize.base,
        language: WhisperModelLanguage = WhisperModelLanguage.spanish,
        force_retranscribe: bool = False,
        force_revectorize: bool = False,
    ) -> TranscriptionResult:
        """Complete transcription workflow: audio → file → database → vectors."""
        try:
            # Step 1: Create transcription file
            file_success, transcription_data, file_message = self.create_transcription_file(
                course_code,
                lesson_number,
                model_size,
                language,
                force_retranscribe,
            )

            if not file_success:
                return TranscriptionResult.failure_result(file_message)

            # Step 2: Save to database
            db_success, transcription_id, db_message = self.save_transcription_to_db(
                course_code,
                lesson_number,
                transcription_data,
                force_retranscribe,
            )

            if not db_success or transcription_id is None:
                return TranscriptionResult.failure_result(db_message)

            # Step 3: Vectorize
            was_vectorized, _ = self.ensure_transcription_vectorized(transcription_id, force_revectorize)
            self.db.commit()

            # Determine actions performed
            was_transcribed = "created" in file_message.lower()
            actions = []
            if was_transcribed:
                actions.append("transcribed")
            if was_vectorized:
                actions.append("vectorized")

            message = (
                "Successfully " + " and ".join(actions) if actions else "Transcription already exists and is vectorized"
            )

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

        except Exception as e:
            self.db.rollback()
            logger.error(f"Complete transcription workflow failed: {e}")
            return TranscriptionResult.failure_result(f"Transcription workflow failed: {str(e)}")

    # === QUERY OPERATIONS ===

    def get_transcription(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize | None = None,
    ) -> TranscriptionResult:
        """Get transcription from database."""
        transcription = self.transcription_repo.get_by_course_lesson_and_model(course_code, lesson_number, model_size)

        if transcription:
            return TranscriptionResult.success_result(
                message="Transcription retrieved from database",
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

        return TranscriptionResult.failure_result(f"No transcription found for {course_code} lesson {lesson_number}")

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
        """Vectorize existing transcription."""
        try:
            was_vectorized, message = self.ensure_transcription_vectorized(transcription_id, force_revectorize=True)
            self.db.commit()

            return TranscriptionResult.success_result(
                message=message,
                transcription_id=transcription_id,
                data={"vectorized": was_vectorized},
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Vectorization failed: {e}")
            return TranscriptionResult.failure_result(f"Vectorization failed: {str(e)}")

    # === PRIVATE HELPERS ===

    def _build_transcription_metadata(self, transcription_data: dict) -> dict:
        """Build metadata for transcription."""
        segments = transcription_data.get("segments", [])
        return {
            **normalize_json(transcription_data.get("asr_model", {}), prefix="transcriber"),
            "transcriber_model_size": transcription_data.get("model_size"),
            "language": transcription_data.get("language"),
            "duration_seconds": segments[-1].get("end", 0.0) if segments else 0.0,
            "segments_count": transcription_data.get("segments_count", 0),
            "content_length": len(transcription_data.get("text", "")),
            "processing_time": transcription_data.get("processing_time", 0.0),
            "source_file": transcription_data.get("source_file"),
            "file_size_bytes": transcription_data.get("file_size_bytes", 0),
            "vectorized": False,
            "created_by": __name__,
        }

    def _format_transcription_summary(self, transcription) -> dict:
        """Format transcription for list response."""
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

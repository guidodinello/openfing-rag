from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from services.transcriber.core import TranscriberProtocol
from services.transcriber.core.file_utils import TranscriptionFileUtils
from services.transcriber.schemas import (
    Chunk,
    ChunkResult,
    Lesson,
    LessonListResult,
    Transcription,
    TranscriptionListResult,
    TranscriptionResult,
    WhisperModelLanguage,
    WhisperModelSize,
)
from shared.config import get_settings
from shared.database.repositories import LessonRepository, TranscriptionRepository, VectorRepository
from shared.logging import get_logger
from shared.utils import megabytes_to_bytes, normalize_json

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class DatabaseDependencies:
    lesson_repo: LessonRepository
    transcription_repo: TranscriptionRepository
    vector_repo: VectorRepository
    db: Session


class TranscriptionService:
    def __init__(
        self,
        transcriber: TranscriberProtocol,
        database: DatabaseDependencies | None = None,
    ):
        self.transcriber = transcriber
        self.database = database
        self.media_base_path = settings.TRANSCRIBER.INPUT_DIR

    def transcribe_lesson(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize = WhisperModelSize.base,
        language: WhisperModelLanguage = WhisperModelLanguage.spanish,
    ) -> TranscriptionResult:
        try:
            transcription_file = TranscriptionFileUtils.find_transcription_file(
                course_code, lesson_number, model_size, self.transcriber.identifier
            )
            if transcription_file:
                return TranscriptionResult.failure_result(f"Transcription file already exists! {transcription_file=}")

            media_file = TranscriptionFileUtils.find_media_file(course_code, lesson_number)
            if not media_file:
                return TranscriptionResult.failure_result(f"No media file found for {course_code=} {lesson_number=}")

            result = self.transcriber.transcribe(
                model_size=model_size,
                language=language,
                audio_path=media_file,
            )
            result.update(
                {
                    "course_code": course_code,
                    "lesson_number": lesson_number,
                    "model_size": model_size.value,
                    "language": language.value,
                    "source_file": str(media_file),
                    "file_size_bytes": media_file.stat().st_size,
                }
            )

            file_path = TranscriptionFileUtils.save_transcription(
                result=result,
                model_size=model_size,
                course_code=course_code,
                lesson_number=lesson_number,
                transcriber_suffix=self.transcriber.identifier,
            )
            logger.info(f"Transcription file created successfully {file_path=}")

            return TranscriptionResult.success_result(
                message="Transcription file created successfully",
                item=Transcription(
                    id=-1,
                    course_code=course_code,
                    lesson_number=lesson_number,
                    lesson_id=-1,
                    lesson_title="Unknown",
                    content_length=file_path.stat().st_size,
                    vectorized=False,
                ),
            )

        except Exception as e:
            logger.error(f"Failed to create transcription file: {e}")
            return TranscriptionResult.failure_result(f"Transcription failed: {str(e)}")

    def save_transcription_from_file_to_db(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize = WhisperModelSize.base,
    ) -> TranscriptionResult:
        assert self.database is not None, "Database dependencies are needed for save_transcription_from_file_to_db"

        try:
            transcription_data = TranscriptionFileUtils.load_transcription(course_code, lesson_number, model_size)
            if not transcription_data:
                return TranscriptionResult.failure_result(
                    f"No transcription file found for {course_code} L{lesson_number} ({model_size.value})"
                )

            lesson = self.repos.lesson_repo.get_with_course(course_code, lesson_number)
            if not lesson:
                return TranscriptionResult.failure_result(
                    f"Lesson {lesson_number} not found for course {course_code}. Please update using the scraper."
                )

            existing = self.repos.transcription_repo.get_by_lesson_and_model(lesson.id, model_size)
            if existing:
                logger.info(f"Transcription already exists in database: {existing.id}")
                return TranscriptionResult.success_result(
                    message="Transcription already exists in database", transcription_id=existing.id, data={}
                )

            transcription = self.repos.transcription_repo.create_or_update_for_lesson(
                lesson_id=lesson.id,
                content=transcription_data.get("text", ""),
                metadata=self._build_transcription_metadata(transcription_data),
            )

            self.db.commit()

            logger.info(f"Saved transcription to database: {transcription.id}")
            return TranscriptionResult.success_result(
                message="Transcription saved to database", item=Transcription.from_model(transcription)
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save transcription from file: {e}")
            return TranscriptionResult.failure_result(message=f"Failed to save: {str(e)}")

    def find_available_lessons_by_size(
        self,
        course_code: str | None = None,
        max_file_size_mb: int | None = None,
        largest_first: bool = False,
    ) -> LessonListResult:
        try:
            lessons = sorted(
                filter(
                    lambda le: le.file_bytes <= megabytes_to_bytes(max_file_size_mb),
                    map(Lesson.from_path, TranscriptionFileUtils.find_media_files(course_code)),
                ),
                key=lambda le: le.file_bytes,
                reverse=largest_first,
            )

            return LessonListResult.success_result(
                message=f"Found {len(lessons)} lesson files for course {course_code}"
                + (f" (≤{max_file_size_mb}MB)" if max_file_size_mb else ""),
                items=lessons,
            )

        except Exception as e:
            logger.error(f"Error scanning lessons for {course_code=}: {e}")
            return LessonListResult.failure_result(message=f"Failed to scan lessons: {str(e)}")

    def get_transcription(
        self,
        course_code: str,
        lesson_number: int,
        model_size: Optional[WhisperModelSize] = None,
    ) -> TranscriptionResult:
        """Get transcription from database."""
        assert self.database is not None, "Database dependencies are needed for get_transcription"

        transcription = self.repos.transcription_repo.get_by_course_lesson_and_model(
            course_code, lesson_number, model_size
        )

        if transcription:
            return TranscriptionResult.success_result(
                message="Transcription retrieved from database",
                transcription_id=transcription.id,
                item=Transcription.from_model(transcription),
            )

        return TranscriptionResult.failure_result(f"No transcription found for {course_code} lesson {lesson_number}")

    def list_transcriptions(
        self,
        course_code: Optional[str] = None,
    ) -> TranscriptionListResult:
        """List transcriptions in database."""
        assert self.database is not None, "Database dependencies are needed for list_transcriptions"

        try:
            transcriptions = [
                Transcription.from_model(t)
                for t in self.repos.transcription_repo.get_filtered_transcriptions(course_code=course_code)
            ]
            vectorized_count = sum(1 for t in transcriptions if t.is_vectorized)

            return TranscriptionListResult(
                success=True,
                message=f"Found {len(transcriptions)} transcriptions",
                data={
                    "transcriptions": transcriptions,
                    "total_count": len(transcriptions),
                    "vectorized_count": vectorized_count,
                    "unvectorized_count": len(transcriptions) - vectorized_count,
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
        assert self.database is not None, "Database dependencies are needed for vectorize_transcription"

        try:
            if self.repos.transcription_repo.is_vectorized(transcription_id):
                logger.info("Transcription already vectorized")
                return ChunkResult.success_result(message="Transcription is already vectorized")

            vector_ids = self.repos.vector_repo.upsert_transcription(transcription_id)
            logger.info(f"Created {len(vector_ids)} vector chunks")

            self.db.commit()
            return ChunkResult.success_result(
                message="Transcription vectorized succesfully", data=[Chunk(id) for id in vector_ids]
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Vectorization failed: {e}")
            return ChunkResult.failure_result(f"Vectorization failed: {str(e)}")

    def _build_transcription_metadata(self, transcription_data: dict) -> dict:
        """Build metadata for transcription."""
        segments = transcription_data.get("segments", [])
        return {
            **normalize_json(
                transcription_data.get("asr_model", {}),
                prefix="transcriber",
            ),
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

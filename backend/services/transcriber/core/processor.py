from pathlib import Path
from typing import Any

from shared.config.config import get_settings
from shared.database.database import Database
from shared.database.vectorstore import VectorStore
from shared.logging.logger import get_logger
from transcriber.constants.constants import TMP_DOWNLOAD_FOLDER
from transcriber.core.transcriber import Transcriber
from transcriber.schemas.model_language import WhisperModelLanguage
from transcriber.schemas.model_size import WhisperModelSize

logger = get_logger(__name__)
settings = get_settings()


class Processor:
    def __init__(self, database_config=settings):
        self.db = Database(connection_string=settings.DATABASE.URL)
        self.vector_store = VectorStore(config=settings)  # TODO: fix

    def update_transcription(
        self,
        course_acronym: str,
        class_number: int,
        model_size: WhisperModelSize = WhisperModelSize.base,
        language: WhisperModelLanguage = WhisperModelLanguage.spanish,
    ) -> tuple[bool, str]:
        """
        Update or create a transcription for a course lesson.

        Args:
            course_acronym: Course code
            class_number: Lesson number
            model_size: Whisper model size to use
            language: Language of the audio

        Returns:
            Tuple of (success, message)
        """
        # Find the actual media file (any extension)
        file_path = self.__find_media_file(course_acronym, class_number)
        if not file_path:
            logger.error(f"No media file found for {course_acronym} class {class_number}")
            return False, "Media File Not Found"

        # Get output path for transcription
        output_path = self.__get_output_path(course_acronym, class_number, model_size)

        # Create transcriber and process video
        transcriber = Transcriber(
            audio_path=file_path,
            output_dir=output_path,
            model_size=model_size,
            language=language,
        )

        try:
            # Run transcription
            result = transcriber.transcribe()

            # Save to database
            self._save_to_database(
                course_acronym,
                class_number,
                result,
                model_size,
                language,
            )

            return True, "Transcription Completed"
        except Exception as e:
            logger.exception(f"Transcription failed: {str(e)}")
            return False, f"Transcription failed: {str(e)}"

    def __find_media_file(self, course_acronym: str, class_number: int) -> Path | None:
        """
        Find media file matching pattern: {course_acronym}_{class_number:02d}.*

        Args:
            course_acronym: Course code
            class_number: Lesson number

        Returns:
            Path to the media file if found, None otherwise
        """
        base_folder = Path(TMP_DOWNLOAD_FOLDER) / course_acronym

        if not base_folder.exists():
            logger.error(f"Course folder not found: {base_folder.absolute()}")
            return None

        file_name = f"{course_acronym}_{class_number:02d}"

        for file_path in base_folder.iterdir():
            if file_path.is_file() and file_path.stem == file_name:
                logger.info(f"Found matching file: {file_path}")
                return file_path

        logger.error(f"No file found {file_name=}.*")
        return None

    def get_transcription(
        self,
        course_acronym: str,
        class_number: int,
        model_size: str = "base",
    ) -> tuple[bool, str | dict[str, Any]]:
        """
        Get a transcription for a course lesson.

        Args:
            course_acronym: Course code
            class_number: Lesson number
            model_size: Whisper model size to filter by

        Returns:
            Tuple of (success, message or data)
        """
        try:
            course = self.db.get_course_by_code(course_acronym)
            if not course:
                return False, f"Course {course_acronym} not found"

            lesson = self.db.get_lesson_by_course_number(course["id"], class_number)
            if not lesson:
                return (
                    False,
                    f"Lesson {class_number} not found in course {course_acronym}",
                )

            transcription = self.db.get_transcription_by_lesson(lesson["id"])
            if not transcription:
                return (
                    False,
                    f"No transcription found for lesson {class_number} in course {course_acronym}",
                )

            metadata = transcription.get("transcription_metadata", {})
            if model_size and model_size != metadata.get("model_size"):
                return False, f"Transcription with model size {model_size} not found"

            return True, {"content": transcription["content"], "metadata": metadata}

        except Exception as e:
            logger.exception(f"Error retrieving transcription: {str(e)}")
            return False, f"Database error: {str(e)}"

    def __get_output_path(
        self,
        course_acronym: str,
        class_number: int,
        model_size: str,
    ) -> Path:
        """
        Generate the path where the transcription will be saved.

        Args:
            course_acronym: Course code
            class_number: Lesson number
            model_size: Model size

        Returns:
            Path to save the transcription output
        """
        class_number_string = f"{class_number:02d}"
        filename = f"{course_acronym}_{class_number_string}_{model_size}.json"
        return Path("transcriptions") / course_acronym / filename

    def _save_to_database(
        self,
        course_acronym: str,
        class_number: int,
        transcription_result: dict[str, Any],
        model_size: str,
        language: str,
    ) -> None:
        """
        Save transcription results to the database and vector store.

        Args:
            course_acronym: Course code
            class_number: Lesson number
            transcription_result: Transcription data from Whisper
            model_size: Model size used
            language: Language of the audio
        """
        try:
            # Get or create course
            course = self.db.get_course_by_code(course_acronym)
            if not course:
                course_id = self.db.create_course(
                    code=course_acronym,
                    name=f"Course {course_acronym}",
                    metadata={"created_by": "transcription_service"},
                )
                logger.info(f"Created new course {course_acronym} with ID {course_id}")
            else:
                course_id = course["id"]

            # Get or create lesson
            lesson = self.db.get_lesson_by_course_number(course_id, class_number)
            if not lesson:
                lesson_id = self.db.create_lesson(
                    title=f"Lesson {class_number}",
                    number=class_number,
                    course_id=course_id,
                    metadata={"created_by": "transcription_service"},
                )
                logger.info(f"Created new lesson {class_number} with ID {lesson_id}")
            else:
                lesson_id = lesson["id"]

            # Save/update transcription
            existing_transcription = self.db.get_transcription_by_lesson(lesson_id)

            # Prepare metadata
            metadata = {
                "model_size": model_size,
                "language": language,
                "duration": transcription_result.get("duration", 0),
                "segments_count": len(transcription_result.get("segments", [])),
                "processing_timestamp": transcription_result.get(
                    "processing_timestamp",
                ),
            }

            # Extract just the text content
            content = transcription_result.get("text", "")

            if existing_transcription:
                success = self.db.update_transcription(
                    existing_transcription["id"],
                    content,
                    metadata,
                )
                if success:
                    logger.info(f"Updated transcription for lesson {lesson_id}")
                else:
                    logger.error(
                        f"Failed to update transcription for lesson {lesson_id}",
                    )
            else:
                # Create new transcription
                transcription_id = self.db.save_transcription(
                    content,
                    metadata,
                    lesson_id,
                )
                logger.info(
                    f"Created new transcription {transcription_id} for lesson {lesson_id}",
                )

            # Process for vector store
            self.vector_store.process_transcription(
                lesson_id,
                content,
                {**metadata, **transcription_result},
            )
            logger.info(f"Processed transcription for RAG for lesson {lesson_id}")

        except Exception as e:
            logger.exception(f"Error saving transcription to database: {str(e)}")
            raise

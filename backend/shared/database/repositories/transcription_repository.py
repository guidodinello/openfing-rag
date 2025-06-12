from sqlalchemy import and_, update
from sqlalchemy.orm import Session, joinedload

from shared.database.models.rag.course import Course
from shared.database.models.rag.lesson import Lesson
from shared.database.models.rag.transcription import Transcription
from shared.database.repositories.base_repository import BaseRepository
from transcriber.schemas.enums import WhisperModelSize


class TranscriptionRepository(BaseRepository[Transcription]):
    def __init__(self, db: Session):
        super().__init__(Transcription, db)

    def get_by_lesson_id(self, lesson_id: int) -> list[Transcription]:
        """Get all transcriptions for a lesson."""
        return self.db.query(self.model).filter(self.model.lesson_id == lesson_id).all()

    def get_by_lesson(self, lesson_id: int) -> list[Transcription]:
        """Alias for get_by_lesson_id for backward compatibility."""
        return self.get_by_lesson_id(lesson_id)

    def get_latest_by_lesson_id(self, lesson_id: int) -> Transcription | None:
        """Get the most recent transcription for a lesson."""
        return (
            self.db.query(self.model)
            .filter(self.model.lesson_id == lesson_id)
            .order_by(self.model.created_at.desc())
            .first()
        )

    def get_by_lesson_and_model(
        self,
        lesson_id: int,
        model_size: WhisperModelSize | None = None,
    ) -> Transcription | None:
        """Get by lesson and optionally filter by model size."""
        query = self.db.query(self.model).filter(self.model.lesson_id == lesson_id)

        if model_size:
            query = query.filter(self.model.transcription_metadata["model_size"].astext == model_size.value)

        return query.order_by(self.model.created_at.desc()).first()

    def get_by_course_lesson_and_model(
        self,
        course_code: str,
        lesson_number: int,
        model_size: WhisperModelSize | None = None,
    ) -> Transcription | None:
        query = (
            self.db.query(self.model)
            .options(joinedload(Transcription.lesson).joinedload(Lesson.course))
            .filter(
                Transcription.lesson.has(
                    and_(Lesson.number == lesson_number, Lesson.course.has(Course.code == course_code)),
                ),
            )
        )

        if model_size:
            query = query.filter(self.model.transcription_metadata["model_size"].astext == model_size.value)

        return query.order_by(self.model.created_at.desc()).first()

    def get_unvectorized_transcriptions(self) -> list[Transcription]:
        """Get all transcriptions that haven't been vectorized."""
        return (
            self.db.query(self.model)
            .options(joinedload(Transcription.lesson).joinedload(Lesson.course))
            .filter(~self.model.transcription_metadata.op("?")("vectorized"))
            .all()
        )

    def get_filtered_transcriptions(
        self,
        course_code: str | None = None,
        unvectorized_only: bool = False,
    ) -> list[Transcription]:
        """Get transcriptions with optional filtering."""
        query = self.db.query(self.model).options(joinedload(Transcription.lesson).joinedload(Lesson.course))

        if unvectorized_only:
            query = query.filter(~self.model.transcription_metadata.op("?")("vectorized"))

        if course_code:
            query = query.join(Lesson).join(Course).filter(Course.code == course_code)

        return query.all()

    def get_transcriptions_with_filters(
        self,
        course_code: str | None = None,
        unvectorized_only: bool = False,
    ) -> list[Transcription]:
        """Alias for get_filtered_transcriptions."""
        return self.get_filtered_transcriptions(course_code, unvectorized_only)

    def create_or_update_for_lesson(self, lesson_id: int, content: str, metadata: dict) -> Transcription:
        """Create new transcription or update existing one for a lesson."""
        existing = self.get_latest_by_lesson_id(lesson_id)

        if existing:
            # Update existing transcription
            existing.content = content
            existing.transcription_metadata = {
                **existing.transcription_metadata,
                **metadata,
                "updated_by": "transcription_service",
            }
            self.db.flush()
            self.db.refresh(existing)
            return existing
        else:
            # Create new transcription
            return self.create(
                content=content,
                transcription_metadata=metadata,
                lesson_id=lesson_id,
            )

    def is_vectorized(self, transcription_id: int) -> bool:
        """Check if a transcription has been vectorized."""
        transcription = self.get_by_id(transcription_id)
        if not transcription:
            return False
        return transcription.transcription_metadata.get("vectorized", False)

    def mark_as_vectorized(self, transcription_id: int) -> bool:
        """Mark transcription as vectorized."""
        try:
            self.db.execute(
                update(self.model)
                .where(self.model.id == transcription_id)
                .values(transcription_metadata=self.model.transcription_metadata.op("||")({"vectorized": True})),
            )
            return True
        except Exception:
            return False

    def mark_as_not_vectorized(self, transcription_id: int) -> bool:
        """Mark transcription as not vectorized."""
        try:
            self.db.execute(
                update(self.model)
                .where(self.model.id == transcription_id)
                .values(transcription_metadata=self.model.transcription_metadata.op("||")({"vectorized": False})),
            )
            return True
        except Exception:
            return False

    def update(self, transcription_id: int, **data) -> Transcription:
        """Update transcription by ID."""
        transcription = self.get_by_id(transcription_id)
        if not transcription:
            raise ValueError(f"Transcription {transcription_id} not found")

        for key, value in data.items():
            if hasattr(transcription, key):
                setattr(transcription, key, value)

        self.db.flush()
        self.db.refresh(transcription)
        return transcription

    def update_metadata(self, transcription_id: int, new_metadata: dict) -> bool:
        """Update transcription metadata."""
        try:
            self.db.execute(
                update(self.model)
                .where(self.model.id == transcription_id)
                .values(transcription_metadata=self.model.transcription_metadata.op("||")(new_metadata)),
            )
            return True
        except Exception:
            return False

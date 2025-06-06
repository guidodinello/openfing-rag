from sqlalchemy import update
from sqlalchemy.orm import Session

from shared.database.models.rag.transcription import Transcription
from shared.database.repositories.base_repository import BaseRepository


class TranscriptionRepository(BaseRepository[Transcription]):
    def __init__(self, db: Session):
        super().__init__(Transcription, db)

    def get_by_lesson_id(self, lesson_id: int) -> list[Transcription]:
        return self.db.query(self.model).filter(self.model.lesson_id == lesson_id).all()

    def get_unvectorized_transcriptions(self) -> list[Transcription]:
        return self.db.query(self.model).filter(~self.model.transcription_metadata.op("?")("vectorized")).all()

    def mark_as_vectorized(self, transcription_id: int) -> bool:
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
        try:
            self.db.execute(
                update(self.model)
                .where(self.model.id == transcription_id)
                .values(transcription_metadata=self.model.transcription_metadata.op("||")({"vectorized": False})),
            )
            return True
        except Exception:
            return False

    @property
    def is_vectorized(self) -> bool:
        return self.transcription_metadata.get("vectorized", False)

from typing import Self

from pydantic import BaseModel

from services.transcriber.schemas import TranscriptionFileResult
from shared.api.v1.schemas import ApiListResponse, ApiResponse
from shared.database.models import Transcription as TranscriptionModel
from shared.enums.whisper import WhisperModelSize


class Transcriber(BaseModel):
    identifier: str
    size: WhisperModelSize


class Transcription(BaseModel):
    id: int
    lesson_id: int
    course_id: int
    transcriber: Transcriber
    vectorized: bool
    lesson_title: str
    content: str
    content_length: int

    @classmethod
    def from_model(cls, transcription: TranscriptionModel) -> Self:
        return cls(
            id=transcription.id,
            course_id=transcription.lesson.course.id,
            lesson_id=transcription.lesson_id,
            lesson_title=transcription.lesson.title,
            content_length=len(transcription.content) if transcription.content else 0,
            vectorized=transcription.transcription_metadata.get("vectorized", False),
            transcriber=Transcriber(
                identifier=transcription.transcription_metadata.get("transcriber_identifier"),
                size=WhisperModelSize(transcription.transcription_metadata.get("transcriber_model_size")),
            ),
            content=transcription.content,
        )


class TranscriptionSummary(BaseModel):
    id: int
    lesson_id: int
    course_id: int
    transcriber: Transcriber
    vectorized: bool
    content_length: int

    @classmethod
    def from_model(cls, transcription: TranscriptionModel) -> Self:
        return cls(
            id=transcription.id,
            course_id=transcription.lesson.course.id,
            lesson_id=transcription.lesson_id,
            lesson_title=transcription.lesson.title,
            content_length=len(transcription.content) if transcription.content else 0,
            vectorized=transcription.transcription_metadata.get("vectorized", False),
            transcriber=Transcriber(
                identifier=transcription.transcription_metadata.get("transcriber_identifier"),
                size=WhisperModelSize(transcription.transcription_metadata.get("transcriber_model_size")),
            ),
        )


TranscriptionResponse = ApiResponse[Transcription]
ListTranscriptionsResponse = ApiListResponse[TranscriptionSummary]


class TranscriptionFile(BaseModel):
    course_code: str
    lesson_number: int
    file_path: str
    file_bytes: int
    transcriber: Transcriber

    @classmethod
    def from_transcription_file_result(cls, result: TranscriptionFileResult) -> Self:
        return cls(
            course_code=result.item.course_code,
            lesson_number=result.item.lesson_number,
            transcriber=Transcriber(
                identifier=result.item.transcriber_identifier,
                size=WhisperModelSize(result.item.transcriber_model_size),
            ),
            file_path=result.item.file_path,
            file_bytes=result.item.file_bytes,
        )


TranscriptionFileResponse = ApiResponse[TranscriptionFile]

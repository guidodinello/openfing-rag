from typing import Self

from pydantic import BaseModel

from services.transcriber.schemas import TranscriptionFileResult, TranscriptionResult
from shared.api.v1.schemas import ApiListResponse, ApiResponse
from shared.enums.whisper import WhisperModelSize


class Transcription(BaseModel):
    id: int
    lesson_id: int
    course_code: str
    lesson_number: int
    lesson_title: str
    content_length: int
    vectorized: bool

    @classmethod
    def from_transcription_result(cls, result: TranscriptionResult) -> Self:
        return cls(
            id=result.item.id,
            lesson_id=result.item.lesson_id,
            course_code=result.item.course_code,
            lesson_number=result.item.lesson_number,
            lesson_title=result.item.lesson_title,
            content_length=result.item.content_length,
            vectorized=result.item.vectorized,
        )


TranscriptionResponse = ApiResponse[Transcription]
ListTranscriptionsResponse = ApiListResponse[Transcription]


class TranscriptionFile(BaseModel):
    course_code: str
    lesson_number: int
    model_size: WhisperModelSize
    transcription_identifier: str
    file_path: str
    file_bytes: int

    @classmethod
    def from_transcription_file_result(cls, result: TranscriptionFileResult) -> Self:
        print(result)
        return cls(
            course_code=result.item.course_code,
            lesson_number=result.item.lesson_number,
            model_size=result.item.model_size,
            transcription_identifier=result.item.transcription_identifier,
            file_path=result.item.file_path,
            file_bytes=result.item.file_bytes,
        )


TranscriptionFileResponse = ApiResponse[TranscriptionFile]

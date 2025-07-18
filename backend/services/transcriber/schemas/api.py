from typing import Any, Self

from pydantic import BaseModel, Field

from services.transcriber.schemas import (
    TranscriptionListResult,
    TranscriptionResult,
    WhisperModelLanguage,
    WhisperModelSize,
)


class TranscriptionCreateRequest(BaseModel):
    model_size: WhisperModelSize = Field(default=WhisperModelSize.base, description="Whisper model size")
    language: WhisperModelLanguage = Field(default=WhisperModelLanguage.spanish, description="Audio language")
    force_retranscribe: bool = Field(default=False, description="Force to transcribe again even if it already exists")
    force_revectorize: bool = Field(default=False, description="Force to revectorize again even if it already was")


class TranscriptionResponse(BaseModel):
    success: bool
    message: str
    transcription_id: int | None = None
    data: dict[str, Any] | None = None

    @classmethod
    def from_transcription_result(cls, result: TranscriptionResult) -> Self:
        return cls(
            success=result.success,
            message=result.message,
            transcription_id=result.transcription_id,
            data=result.data,
        )


class TranscriptionListResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any]

    @classmethod
    def from_transcription_list_result(cls, result: TranscriptionListResult) -> Self:
        return cls(
            success=result.success,
            message=result.message,
            data=result.data,
        )


class AvailableLessonsResponse(BaseModel):
    success: bool
    message: str
    lessons: list[dict[str, Any]]


class LessonFile(BaseModel):
    lesson_number: int
    filename: str
    file_size: int
    file_path: str
    extension: str

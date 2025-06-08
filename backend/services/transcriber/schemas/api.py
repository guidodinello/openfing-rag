from typing import Any

from pydantic import BaseModel, Field

from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize


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


class TranscriptionListResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any]


class AvailableLessonsResponse(BaseModel):
    success: bool
    message: str
    lessons: list[dict[str, Any]]

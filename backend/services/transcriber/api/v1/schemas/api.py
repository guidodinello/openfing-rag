from pydantic import BaseModel, Field

from shared.enums import WhisperModelLanguage, WhisperModelSize


class TranscribeRequest(BaseModel):
    course_code: str = Field(..., description="Course code", example="AGPI")
    lesson_number: int = Field(..., description="Lesson number", ge=1, example=1)
    model_size: WhisperModelSize = Field(default=WhisperModelSize.base, description="Whisper model size")
    language: WhisperModelLanguage = Field(default=WhisperModelLanguage.spanish, description="Audio language")

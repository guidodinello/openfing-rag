from dataclasses import dataclass
from typing import Self

from services.transcriber.schemas.api import AvailableLessonsResponse, TranscriptionListResponse, TranscriptionResponse


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    success: bool
    message: str
    transcription_id: int | None = None
    data: dict | None = None

    @classmethod
    def success_result(cls, message: str, transcription_id: int, data: dict | None = None) -> Self:
        return cls(success=True, message=message, transcription_id=transcription_id, data=data)

    @classmethod
    def failure_result(cls, message: str, data: dict | None = None) -> Self:
        return cls(success=False, message=message, transcription_id=None, data=data)

    def to_api_response(self) -> TranscriptionResponse:
        return TranscriptionResponse(
            success=self.success,
            message=self.message,
            transcription_id=self.transcription_id,
            data=self.data,
        )


@dataclass(frozen=True, slots=True)
class LessonScanResult:
    success: bool
    message: str
    lessons: list[dict]

    def to_api_response(self) -> AvailableLessonsResponse:
        return AvailableLessonsResponse(success=self.success, message=self.message, lessons=self.lessons)


@dataclass(frozen=True, slots=True)
class TranscriptionListResult:
    success: bool
    message: str
    data: dict

    def to_api_response(self) -> TranscriptionListResponse:
        return TranscriptionListResponse(success=self.success, message=self.message, data=self.data)

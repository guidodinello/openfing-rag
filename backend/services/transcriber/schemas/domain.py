from dataclasses import dataclass
from typing import Any, Self

from services.transcriber.schemas.api import (
    AvailableLessonsResponse,
    LessonFile,
    TranscriptionListResponse,
    TranscriptionResponse,
    TranscriptionSummary,
)
from shared.database.models.rag.transcription import Transcription


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    success: bool
    message: str
    transcription_id: int | None = None
    data: dict[str, Any] | None = None

    @classmethod
    def success_result(cls, message: str, transcription_id: int | None = None, data: dict | None = None) -> Self:
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
    lessons: list[dict[str, Any]]

    @classmethod
    def success_result(cls, message: str, lessons: list[dict[str, Any]]) -> Self:
        return cls(success=True, message=message, lessons=lessons)

    @classmethod
    def failure_result(cls, message: str) -> Self:
        return cls(success=False, message=message, lessons=[])

    def to_api_response(self) -> AvailableLessonsResponse:
        return AvailableLessonsResponse(success=self.success, message=self.message, lessons=self.lessons)

    def to_lesson_files(self) -> list[LessonFile]:
        """Convert to typed lesson files."""
        return [LessonFile(**lesson) for lesson in self.lessons]


@dataclass(frozen=True, slots=True)
class TranscriptionListResult:
    success: bool
    message: str
    data: dict[str, Any]

    @classmethod
    def success_result(cls, transcriptions: list[Transcription]) -> Self:
        # Format transcriptions
        transcription_list = [_format_transcription_summary(t) for t in transcriptions]
        vectorized_count = sum(1 for t in transcription_list if t["is_vectorized"])

        return cls(
            success=True,
            message=f"Found {len(transcription_list)} transcriptions",
            data={
                "transcriptions": transcription_list,
                "total_count": len(transcription_list),
                "vectorized_count": vectorized_count,
                "unvectorized_count": len(transcription_list) - vectorized_count,
            },
        )

    @classmethod
    def failure_result(cls, message: str) -> Self:
        return cls(
            success=False,
            message=message,
            data={"transcriptions": [], "total_count": 0, "vectorized_count": 0, "unvectorized_count": 0},
        )

    def to_api_response(self) -> TranscriptionListResponse:
        return TranscriptionListResponse(success=self.success, message=self.message, data=self.data)

    def to_transcription_summaries(self) -> list[TranscriptionSummary]:
        """Convert to typed transcription summaries."""
        if not self.success:
            return []
        return [TranscriptionSummary(**t) for t in self.data.get("transcriptions", [])]


# Helper functions for formatting (moved from service)
def _format_transcription_detail(transcription: Transcription) -> dict[str, Any]:
    """Format transcription for detailed response."""
    return {
        "id": transcription.id,
        "content": transcription.content,
        "metadata": transcription.transcription_metadata,
        "lesson": {
            "id": transcription.lesson.id,
            "number": transcription.lesson.number,
            "title": transcription.lesson.title,
            "course_code": transcription.lesson.course.code,
        },
    }


def _format_transcription_summary(transcription: Transcription) -> dict[str, Any]:
    """Format transcription for list response."""
    return {
        "id": transcription.id,
        "lesson_id": transcription.lesson_id,
        "course_code": transcription.lesson.course.code,
        "lesson_number": transcription.lesson.number,
        "lesson_title": transcription.lesson.title,
        "content_length": len(transcription.content) if transcription.content else 0,
        "model_size": transcription.transcription_metadata.get("transcriber_model_size"),
        "package": transcription.transcription_metadata.get("transcriber_package_name"),
        "language": transcription.transcription_metadata.get("language"),
        "is_vectorized": transcription.transcription_metadata.get("vectorized", False),
        "created_at": transcription.created_at.isoformat() if transcription.created_at else None,
    }


def create_transcription_detail_result(transcription: Transcription) -> TranscriptionResult:
    """Create a TranscriptionResult with detailed transcription data."""
    return TranscriptionResult.success_result(
        message="Transcription retrieved from database",
        transcription_id=transcription.id,
        data=_format_transcription_detail(transcription),
    )

from dataclasses import dataclass
from pathlib import Path
from typing import Self

from services.transcriber.core.file_utils import TranscriptionFileUtils
from shared.database.models import Transcription as TranscriptionModel
from shared.database.repositories.vector_repository import ChunkId
from shared.domain import ListResult, Result


@dataclass(frozen=True, slots=True)
class Transcription:
    id: int
    lesson_id: int
    course_code: str
    lesson_number: int
    lesson_title: str
    content_length: int
    vectorized: bool

    @classmethod
    def from_model(cls, transcription: TranscriptionModel) -> Self:
        return cls(
            id=transcription.id,
            lesson_id=transcription.lesson_id,
            course_code=transcription.lesson.course.code,
            lesson_number=transcription.lesson.number,
            lesson_title=transcription.lesson.title,
            content_length=len(transcription.content) if transcription.content else 0,
            vectorized=transcription.transcription_metadata.get("vectorized", False),
        )


class TranscriptionResult(Result[Transcription]): ...


class TranscriptionListResult(ListResult[Transcription]): ...


@dataclass(frozen=True, slots=True)
class Lesson:
    course_code: str
    lesson_number: int
    file_path: str
    file_bytes: int

    @classmethod
    def from_path(cls, path: Path) -> Self:
        return cls(
            *TranscriptionFileUtils.extract_course_and_lesson_number_from_media_file(path),
            file_path=str(path),
            file_bytes=path.stat().st_size,
        )


class LessonListResult(ListResult[Lesson]): ...


@dataclass(frozen=True, slots=True)
class Chunk:
    id: ChunkId


class ChunkResult(Result[Chunk]): ...

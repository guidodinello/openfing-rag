from dataclasses import dataclass
from pathlib import Path
from typing import Self

from shared.database.models import Transcription
from shared.domain import ListResult, Result
from shared.enums.whisper import WhisperModelSize
from shared.file_utils import TranscriptionFileUtils
from shared.vectors import ChunkId


@dataclass(frozen=True, slots=True)
class TranscriptionFile:
    course_code: str
    lesson_number: int
    transcriber_model_size: WhisperModelSize
    transcriber_identifier: str
    file_path: str
    file_bytes: int

    @classmethod
    def from_path(cls, path: Path) -> Self:
        course_code, lesson_number, model_size, transcriber_suffix = (
            TranscriptionFileUtils.extract_course_and_lesson_number_from_transcription_file(path)
        )
        return cls(
            course_code,
            lesson_number,
            transcriber_model_size=WhisperModelSize(model_size),
            transcriber_identifier=transcriber_suffix,
            file_path=str(path),
            file_bytes=path.stat().st_size,
        )


class TranscriptionFileResult(Result[TranscriptionFile]): ...


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
        course_code, lesson_number = TranscriptionFileUtils.extract_course_and_lesson_number_from_media_file(path)
        return cls(
            course_code,
            lesson_number,
            file_path=str(path),
            file_bytes=path.stat().st_size,
        )


class LessonListResult(ListResult[Lesson]): ...


@dataclass(frozen=True, slots=True)
class Chunk:
    id: ChunkId


class ChunkListResult(ListResult[Chunk]): ...

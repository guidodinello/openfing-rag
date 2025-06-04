# backend/app/rag/ingestion/models.py
from dataclasses import dataclass
from typing import Any


@dataclass
class WhisperSegment:
    """Represents a single segment from Whisper output."""

    id: int
    start: float
    end: float
    text: str
    seek: int
    tokens: list[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float


@dataclass
class MergedChunk:
    """Represents a merged chunk of multiple segments."""

    start: float
    end: float
    text: str
    segments: list[WhisperSegment]


@dataclass
class ChunkMetadata:
    """Represents metadata for a processed chunk."""

    content: str
    start_time: float
    end_time: float
    raw_transcription_id: int
    lesson_id: int
    metadata: dict[str, Any]

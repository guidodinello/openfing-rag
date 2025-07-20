from dataclasses import dataclass
from typing import Any, Self

from shared.domain import Result


@dataclass(frozen=True, slots=True)
class SearchContext:
    """Represents search context for vector retrieval."""

    query: str
    lessons_ids: list[int]
    courses_ids: list[int]
    max_results: int = 4


## ESTO LO DEBERIA DEVOLVER EL SIMILARITY SEARCH DEL VECTOR REPO
@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """Represents a chunk retrieved from vector store."""

    id: str
    content: str
    score: float
    transcription_id: int
    lesson_id: int
    course_id: int
    metadata: dict[str, Any]

    ## TODO: this should probably be some Schema and not a dict
    @classmethod
    def from_search_result(cls, search_result: dict[str, Any]) -> Self:
        """Convert from vector repository search result format."""
        return cls(
            id=search_result["id"],
            content=search_result["content"],
            score=search_result["score"],
            transcription_id=search_result["metadata"]["transcription_id"],
            lesson_id=search_result["metadata"]["lesson_id"],
            course_id=search_result["metadata"]["course_id"],
            metadata=search_result["metadata"],
        )


@dataclass(frozen=True, slots=True)
class LLMAnswer:
    answer: str
    model_used: str
    role: str = "assistant"


class LLMAnswerResult(Result[LLMAnswer]): ...


@dataclass(frozen=True, slots=True)
class SourceTimestamp:
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class Source:
    id: str
    title: str
    content: str
    timestamp: SourceTimestamp
    confidence: float
    url: str


@dataclass(frozen=True, slots=True)
class Chat:
    result: LLMAnswer
    sources: list[Source]


class ChatResult(Result[Chat]): ...

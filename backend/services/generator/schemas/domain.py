from dataclasses import dataclass
from typing import Any, Self


@dataclass(frozen=True, slots=True)
class ChatResult:
    success: bool
    response: str
    sources: list[str]
    model_used: str | None = None
    error: str | None = None
    data: dict[str, Any] | None = None

    @classmethod
    def success_result(
        cls,
        response: str,
        sources: list[str],
        model_used: str,
        data: dict | None = None,
    ) -> Self:
        return cls(
            success=True,
            response=response,
            sources=sources,
            model_used=model_used,
            data=data,
        )

    @classmethod
    def failure_result(cls, error: str, data: dict | None = None) -> Self:
        return cls(
            success=False,
            response="I couldn't process your request at this time.",
            sources=[],
            error=error,
            data=data,
        )


@dataclass(frozen=True, slots=True)
class SearchContext:
    """Represents search context for vector retrieval."""

    query: str
    lesson_id: int | None = None
    course_codes: list[str] | None = None
    max_results: int = 4


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """Represents a chunk retrieved from vector store."""

    id: str
    content: str
    metadata: dict[str, Any]
    score: float
    lesson_id: int | None = None
    course_code: str | None = None
    chunk_index: int | None = None

    ## TODO: this should probably be some Schema and not a dict
    @classmethod
    def from_search_result(cls, search_result: dict[str, Any]) -> Self:
        """Convert from vector repository search result format."""
        return cls(
            id=search_result["id"],
            content=search_result["content"],
            metadata=search_result["metadata"],
            score=search_result["score"],
            lesson_id=search_result.get("lesson_id"),
            course_code=search_result.get("course_code"),
            chunk_index=search_result.get("chunk_index"),
        )

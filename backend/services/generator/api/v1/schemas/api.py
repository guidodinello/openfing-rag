from datetime import datetime, timezone
from typing import Self

from pydantic import BaseModel, Field

from services.generator.schemas import ChatResult, Source
from shared.api.v1.schemas.api import ApiResponse
from shared.database.models import MessageSource


class ChatQuery(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's message to the chatbot",
        examples=["¿Qué es una función en programación?"],
    )
    lessons_ids: list[int] | None = Field(
        default=None,
        description="Optional Lesson IDs to filter results",
        examples=[None],
    )
    courses_ids: list[int] | None = Field(
        default=None,
        description="Optional Courses IDs to filter results",
        examples=[None],
    )


class SourceTimestamp(BaseModel):
    start: float = Field(
        ...,
        description="The start position of the video in seconds",
    )
    end: float = Field(
        ...,
        description="The end position of the video in seconds",
    )


class SourceResponse(BaseModel):
    id: str = Field(..., description="Chunk UUID5")
    title: str = Field(..., description="The title of the source")
    content: str = Field(..., description="The content of the source")
    timestamp: SourceTimestamp = Field(..., description="The timestamp of the source")
    confidence: float = Field(..., description="The confidence level of the source")
    url: str = Field(..., description="The URL of the source")

    @classmethod
    def from_source(cls, source: Source) -> Self:
        return cls(
            id=source.id,
            title=source.title,
            content=source.content,
            timestamp=SourceTimestamp(
                start=source.timestamp.start,
                end=source.timestamp.end,
            ),
            confidence=source.confidence,
            url=source.url,
        )

    @classmethod
    def from_model(cls, source: MessageSource) -> Self:
        """
        Convert from MessageSource model to SourceResponse, extracting timing info from chunk metadata.
        """
        ## TODO: move this logic to service
        chunk = source.chunk

        print("METADATA", chunk.chunk_metadata)
        timestamp = SourceTimestamp(
            start=chunk.chunk_metadata.get("start_time"),
            end=chunk.chunk_metadata.get("end_time"),
        )

        # Build title from lesson and course information
        course_name = chunk.course.name if chunk.course else "Unknown Course"
        lesson_title = chunk.lesson.title if chunk.lesson else f"Lesson {chunk.lesson.number if chunk.lesson else '?'}"

        title = f"{course_name} - {lesson_title}"

        url = chunk.lesson.video_url

        return cls(
            id=str(source.chunk_id),
            content=chunk.content,
            confidence=source.confidence_score,
            title=title,
            timestamp=timestamp,
            url=url,
        )


class LLMAnswerResponse(BaseModel):
    answer: str = Field(..., description="The generated answer")
    model_used: str = Field(..., description="Model used for generation")
    role: str = Field(..., description="Role of the message (assistant/user)")

    @classmethod
    def from_llm_answer(cls, llm_answer) -> Self:
        """Convert from LLMAnswer dataclass to Pydantic model."""
        return cls(answer=llm_answer.answer, model_used=llm_answer.model_used, role=llm_answer.role)


class ChatAnswer(BaseModel):
    id: str
    answer: LLMAnswerResponse
    sources: list[SourceResponse] = Field(default_factory=list)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message Creation Timestamp",
    )

    @classmethod
    def from_chat_result(cls, result: ChatResult) -> Self:
        return cls(
            id=str(result.item.id),
            answer=LLMAnswerResponse.from_llm_answer(result.item.answer),
            sources=list(map(SourceResponse.from_source, result.item.sources)),
        )


ChatAnswerResponse = ApiResponse[ChatAnswer]

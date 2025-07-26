from datetime import datetime, timezone
from typing import Self
from uuid import uuid1

from pydantic import UUID1, BaseModel, Field

from services.generator.schemas import ChatResult, Source
from shared.api.v1.schemas.api import ApiResponse


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
    start: int = Field(
        ...,
        description="The start position of the video in seconds",
    )
    end: int = Field(
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


class ChatAnswer(BaseModel):
    id: UUID1 = Field(
        default_factory=uuid1,
        description="ID of the message",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message Creation Timestamp",
    )
    content: str = Field(..., description="The chatbot's response")
    sources: list[SourceResponse] = Field(
        default_factory=list,
        description="Source references for the response",
    )

    @classmethod
    def from_chat_result(cls, result: ChatResult) -> Self:
        return cls(
            content=result.item.result.answer,
            sources=list(map(SourceResponse.from_source, result.item.sources)),
        )


ChatAnswerResponse = ApiResponse[ChatAnswer]

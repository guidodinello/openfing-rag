from datetime import datetime, timezone
from typing import Self
from uuid import uuid1

from pydantic import UUID1, BaseModel, Field

from services.generator.schemas.domain import ChatResult


class ChatMessage(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's message to the chatbot",
    )
    lesson_id: None | int = Field(
        None,
        description="Optional lesson ID to filter results",
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


class Source(BaseModel):
    id: str = Field(..., description="Chunk UUID5")
    title: str = Field(..., description="The title of the source")
    content: str = Field(..., description="The content of the source")
    timestamp: SourceTimestamp = Field(..., description="The timestamp of the source")
    confidence: float = Field(..., description="The confidence level of the source")
    url: str = Field(..., description="The URL of the source")


# TODO: improve this response schema. see https://claude.ai/share/39d65386-d35f-4012-9603-e3f9065ead3b
class ChatResponse(BaseModel):
    id: UUID1 = Field(
        default_factory=uuid1,
        description="ID of the message",
    )  # TODO: i dont know if i should be including this tbf
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message Creation Timestamp",
    )
    content: str = Field(..., description="The chatbot's response")
    sources: list[Source] = Field(
        default_factory=list,
        description="Source references for the response",
    )

    @classmethod
    def from_chat_result(cls, result: ChatResult, sources: list[Source]) -> Self:
        return cls(content=result.response, sources=sources)

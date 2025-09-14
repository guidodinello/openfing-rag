from typing import Self

from pydantic import BaseModel

from shared.database.models import Message as MessageModel
from shared.database.models import MessageRole

from services.generator.api.v1.schemas.api import SourceResponse


class Message(BaseModel):
    id: int
    role: MessageRole
    content: str
    created_at: str
    updated_at: str
    sources: list[SourceResponse]

    @classmethod
    def from_model(cls, message: MessageModel) -> Self:
        return cls(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat(),
            updated_at=message.updated_at.isoformat(),
            sources=[SourceResponse.from_model(src) for src in message.sources] if message.sources else [],
        )

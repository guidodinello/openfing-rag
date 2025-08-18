from typing import Self

from pydantic import BaseModel, Field

from shared.api.v1.schemas import ApiListResponse, ApiResponse
from shared.database.api.v1.schemas import Message, User
from shared.database.models import Conversation as ConversationModel


class CreateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Conversation title")


class UpdateConversationRequest(BaseModel):
    new_title: str = Field(..., min_length=1, max_length=255, description="New conversation title")


class Conversation(BaseModel):
    id: int
    title: str
    owner: User
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, convo: ConversationModel) -> Self:
        return cls(
            id=convo.id,
            title=convo.title,
            owner=User.from_model(convo.user),
            created_at=convo.created_at.isoformat(),
            updated_at=convo.updated_at.isoformat(),
        )


ConversationResponse = ApiResponse[Conversation]
ListConversationsResponse = ApiListResponse[Conversation]


class ConversationWithMessages(Conversation):
    messages: list[Message]

    @classmethod
    def from_model(cls, convo: ConversationModel):
        return cls(
            id=convo.id,
            title=convo.title,
            owner=User.from_model(convo.user),
            created_at=convo.created_at.isoformat(),
            updated_at=convo.updated_at.isoformat(),
            messages=[Message.from_model(msg) for msg in convo.messages],
        )


ConversationWithMessagesResponse = ApiResponse[ConversationWithMessages]

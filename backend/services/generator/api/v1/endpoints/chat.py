from typing import Annotated

from fastapi import APIRouter, Depends

from generator.core.chat import ChatService
from generator.schemas.api import ChatMessage, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    message: ChatMessage,
    chat_service: Annotated[ChatService, Depends()],
) -> ChatResponse:
    return await chat_service.process_message(message)

from typing import Annotated

from fastapi import APIRouter, Depends

from generator.schemas.chat import ChatMessage, ChatResponse
from generator.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    chat_service: Annotated[ChatService, Depends()],
) -> ChatResponse:
    return await chat_service.process_message(message)

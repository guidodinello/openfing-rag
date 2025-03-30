from app.schemas.chat import ChatMessage, ChatResponse
from app.services.chat import ChatService
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    message: ChatMessage, chat_service: ChatService = Depends()
) -> ChatResponse:
    return await chat_service.process_message(message)

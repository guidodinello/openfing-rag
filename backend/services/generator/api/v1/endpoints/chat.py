from fastapi import HTTPException, status

from services.generator.schemas import ChatMessage, ChatResponse, SearchContext
from shared.api.router import create_auth_routers
from shared.database.service_dependencies import ChatServiceDep

routers = create_auth_routers()


@routers.read.post(
    "/chat",
    summary="Process chat message",
    description="Process a chat message using RAG to provide contextual responses",
    status_code=status.HTTP_200_OK,
)
async def chat(
    message: ChatMessage,
    chat_service: ChatServiceDep,
) -> ChatResponse:
    """Process chat message and return response with sources."""
    try:
        result = chat_service.process_message(
            SearchContext(
                query=message.message,
                lesson_id=message.lesson_id,
                max_results=4,
            ),
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error,
            )

        return ChatResponse.from_chat_result(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message",
        ) from e

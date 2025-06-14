from fastapi import APIRouter, HTTPException, status

from services.generator.schemas.api import ChatMessage, ChatResponse
from services.generator.schemas.domain import SearchContext
from shared.database.service_dependencies import ChatServiceDep

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "",
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
        # Convert API request to domain object
        search_context = SearchContext(
            query=message.message,
            lesson_id=message.lesson_id,
            max_results=4,
        )

        # Process through service layer
        result = chat_service.process_message(search_context)

        if not result.success:
            if "No relevant information found" in result.error:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No relevant information found for your query",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process your message",
                )

        return result.to_api_response()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message",
        ) from e

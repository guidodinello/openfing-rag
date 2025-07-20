from fastapi import HTTPException, status

from services.generator.api.v1.schemas import ChatAnswer, ChatAnswerResponse, ChatQuery
from services.generator.schemas import SearchContext
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
    query: ChatQuery,
    chat_service: ChatServiceDep,
) -> ChatAnswerResponse:
    """Process chat message and return response with sources."""
    try:
        result = chat_service.process_message(
            SearchContext(
                query=query.message,
                lessons_ids=query.lessons_ids or [],
                courses_ids=query.courses_ids or [],
                max_results=4,
            ),
        )

        if not result.success:
            return ChatAnswerResponse.error_response(
                message="Successfully retrieved Chat Answer",
                data=ChatAnswer.from_chat_result(result),
            )

        return ChatAnswerResponse.success_response(
            message="Successfully retrieved Chat Answer",
            data=ChatAnswer.from_chat_result(result),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message",
        ) from e

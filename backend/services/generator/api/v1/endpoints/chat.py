from fastapi import Request, status

from shared.api.router import AuthRouters
from shared.auth.authenticated_user import MaybeAuthedUser
from shared.database.service_dependencies import ChatServiceDep

from services.generator.api.v1.schemas import ChatAnswer, ChatAnswerResponse, ChatQuery
from services.generator.schemas import SearchContext

routers = AuthRouters.create()


@routers.public.post(
    "/chat",
    summary="Process chat message",
    description=(
        "Process a chat message using RAG. Supports anonymous users (ephemeral), JWT users, and API key users."
    ),
    status_code=status.HTTP_200_OK,
)
async def chat(
    request: Request,
    query: ChatQuery,
    chat_service: ChatServiceDep,
    user: MaybeAuthedUser,
) -> ChatAnswerResponse:
    """Process chat message and return response with sources."""
    result = chat_service.process_message(
        SearchContext(
            query=query.message,
            lessons_ids=query.lessons_ids or [],
            courses_ids=query.courses_ids or [],
            max_results=4,
        ),
        conversation_id=request.state.chat_context.get("conversation_id"),
        user_id=user.user.id,  ## TODO: fix if user is None
    )

    if not result.success:
        return ChatAnswerResponse.error_response(message=f"Error while retrieving Chat Answer {result.message}")

    return ChatAnswerResponse.success_response(
        message="Successfully retrieved Chat Answer",
        data=ChatAnswer.from_chat_result(result),
    )

from typing import Annotated

from fastapi import HTTPException, Query, status

from shared.api.router import AuthRouters
from shared.auth.oauth2_password_bearer import BearerTokenUser
from shared.database.api.v1.schemas import (
    Conversation,
    ConversationResponse,
    ConversationWithMessages,
    ConversationWithMessagesResponse,
    CreateConversationRequest,
    ListConversationsResponse,
    UpdateConversationRequest,
)
from shared.database.repository_dependencies import ConversationRepositoryDep

routers = AuthRouters.create(prefix="/conversations")


@routers.jwt.bearer.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
    description="Create a new conversation for the authenticated user",
)
async def create_conversation(
    conversation_repo: ConversationRepositoryDep,
    logged_user: BearerTokenUser,
    request: CreateConversationRequest,
) -> ConversationResponse:
    conversation = conversation_repo.create_conversation(logged_user.id, request.title)

    return ConversationResponse.success_response(
        message="Succesfully created conversation",
        data=Conversation.from_model(conversation),
    )


@routers.jwt.bearer.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List user conversations",
    description="Retrieve paginated list of user conversations",
)
async def get_conversations(
    conversation_repo: ConversationRepositoryDep,
    logged_user: BearerTokenUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ListConversationsResponse:
    conversations = conversation_repo.get_user_conversations(logged_user.id, limit=limit, offset=offset)
    return ListConversationsResponse.success_response(
        message="Succesfully retrieved conversations",
        data=[Conversation.from_model(c) for c in conversations],
    )


@routers.jwt.bearer.get(
    "/{conversation_id}/messages",
    status_code=status.HTTP_200_OK,
    summary="Get conversation messages",
    description="Retrieve all messages for a given conversation of the user",
)
async def get_conversation_with_sourced_messages(
    conversation_repo: ConversationRepositoryDep,
    conversation_id: int,
    logged_user: BearerTokenUser,
) -> ConversationWithMessagesResponse:
    conversation = conversation_repo.get_conversation_with_messages(conversation_id)
    if not conversation or conversation.user.id != logged_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return ConversationWithMessagesResponse.success_response(
        message="Succesfully retrieved conversation messages",
        data=ConversationWithMessages.from_model(conversation),
    )


@routers.jwt.bearer.patch(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Edit a conversation",
    description="Rename a conversation",
)
async def edit_conversation(
    conversation_repo: ConversationRepositoryDep,
    logged_user: BearerTokenUser,
    conversation_id: int,
    request: UpdateConversationRequest,
) -> ConversationResponse:
    convo = conversation_repo.get_by(id=conversation_id, user_id=logged_user.id)
    if not convo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    updated_convo = conversation_repo.update(convo, {"title": request.new_title})

    return ConversationResponse.success_response(
        message="Succesfully created conversation",
        data=Conversation.from_model(updated_convo),
    )


@routers.jwt.bearer.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation by id",
    description="Delete a conversation owned by the logged user using the id",
)
async def delete_conversation(
    conversation_repo: ConversationRepositoryDep,
    conversation_id: int,
    logged_user: BearerTokenUser,
):
    conversation = conversation_repo.get_by_id(conversation_id)
    if not conversation or conversation.user.id != logged_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    conversation_repo.delete(conversation)

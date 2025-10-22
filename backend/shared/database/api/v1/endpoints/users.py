from fastapi import status

from shared.api.router import AuthRouters
from shared.auth.oauth2_password_bearer import BearerTokenUser
from shared.database.api.v1.schemas import ListUsersResponse, User, UserResponse
from shared.database.repository_dependencies import UserRepositoryDep

routers = AuthRouters.create(prefix="/users")


@routers.jwt.bearer.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the profile information of the currently authenticated user",
)
async def read_users_me(logged_user: BearerTokenUser) -> UserResponse:
    """Get the current authenticated user's profile."""
    return UserResponse.success_response(message="User retrieved successfully", data=User.from_model(logged_user))


@routers.api_key.admin.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Retrieve a list of all users in the system",
)
async def read_users(user_repo: UserRepositoryDep) -> ListUsersResponse:
    return ListUsersResponse.success_response(
        message="Users retrieved successfully",
        data=[User.from_model(user) for user in user_repo.get_all()],
    )

from fastapi import status

from shared.api.router import AuthRouters
from shared.auth.oauth2_password_bearer import BearerTokenUser
from shared.database.api.v1.schemas import User, UserResponse

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

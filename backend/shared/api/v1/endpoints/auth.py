from typing import Annotated

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordRequestFormStrict

from shared.api.router import AuthRouters
from shared.api.v1.schemas.auth import RefreshTokenRequest, TokenResponse, UserRegister
from shared.auth.oauth2_password_bearer import JwtAuthServiceDep
from shared.config import get_settings
from shared.database.api.v1.schemas import User, UserResponse

settings = get_settings()

routers = AuthRouters.create()


@routers.public.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description=(
        "Create a new user account with email, username and password. All fields are required"
        "and username/email must be unique."
    ),
)
async def register(auth_service: JwtAuthServiceDep, user_data: UserRegister) -> UserResponse:
    """Register a new user account."""
    user = auth_service.register_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
    )
    return UserResponse.success_response(message="User registered successfully", data=User.from_model(user))


@routers.public.post(
    settings.JWT.TOKEN_URL,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and get access token",
    description="Login with username/password to receive a JWT access token for authenticated requests",
)
async def login_for_access_token(
    auth_service: JwtAuthServiceDep,
    form_data: Annotated[OAuth2PasswordRequestFormStrict, Depends()],
) -> TokenResponse:
    """Authenticate user and return access token."""
    _, access_token, refresh_token = auth_service.login(form_data.username, form_data.password)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@routers.public.post("/refresh", status_code=status.HTTP_200_OK, summary="Refresh access token")
async def refresh_access_token(
    auth_service: JwtAuthServiceDep,
    refresh_request: RefreshTokenRequest,
) -> TokenResponse:
    """Generate new access token from refresh token."""
    access_token = auth_service.refresh_access_token(refresh_request.refresh_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

from typing import Annotated

from fastapi import Cookie, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestFormStrict

from shared.api.router import AuthRouters
from shared.api.v1.schemas.auth import TokenResponse, UserRegister
from shared.auth.oauth2_password_bearer import JwtAuthServiceDep
from shared.config import get_settings
from shared.database.api.v1.schemas import User, UserResponse
from shared.exceptions.authentication_exception import AuthenticationException

settings = get_settings()

routers = AuthRouters.create()


@routers.public.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description=(
        "Create a new user account with email, username and password. "
        "All fields are required and username/email must be unique."
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
    description=(
        "Login with username/password to receive a JWT access token. "
        "The refresh token is automatically set as an HTTPOnly cookie for security."
    ),
)
async def login_for_access_token(
    response: Response,
    auth_service: JwtAuthServiceDep,
    form_data: Annotated[OAuth2PasswordRequestFormStrict, Depends()],
) -> TokenResponse:
    """
    Authenticate user and return access token.
    Refresh token is set as HTTPOnly cookie automatically.
    """
    _, access_token = auth_service.login(
        username=form_data.username,
        password=form_data.password,
        response=response,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@routers.public.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description=(
        "Generate a new access token using the refresh token from the HTTPOnly cookie. The refresh token is rotated."
    ),
)
async def refresh_access_token(
    response: Response,
    auth_service: JwtAuthServiceDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> TokenResponse:
    """
    Generate new access token from refresh token cookie.
    Also rotates the refresh token.
    """
    if not refresh_token:
        raise AuthenticationException.missing_token()

    return TokenResponse(
        access_token=auth_service.refresh_access_token(
            refresh_token=refresh_token,
            response=response,
        ),
        token_type="bearer",
    )


@routers.public.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Clears the refresh token cookie to log out the user.",
)
async def logout(
    response: Response,
    auth_service: JwtAuthServiceDep,
) -> dict[str, str]:
    """Logout user by clearing refresh token cookie."""
    auth_service.logout(response)

    return {"message": "Successfully logged out"}

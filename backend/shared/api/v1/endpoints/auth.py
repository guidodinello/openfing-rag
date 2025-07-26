from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestFormStrict

from shared.api.router import AuthRouters
from shared.api.v1.schemas.auth import TokenResponse, UserRegister, UserResponse
from shared.auth.oauth2_password_bearer import BearerTokenUser, JwtAuthService, JwtAuthServiceDep
from shared.config import get_settings

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
    try:
        user = auth_service.register_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
        )
        return UserResponse.from_model(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


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
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = JwtAuthService.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.JWT.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


@routers.jwt.bearer.get(
    "/users/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the profile information of the currently authenticated user",
)
async def read_users_me(logged_user: BearerTokenUser) -> UserResponse:
    return UserResponse.from_model(logged_user)

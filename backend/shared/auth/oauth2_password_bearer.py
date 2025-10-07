import logging as stdLogging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, Response
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from shared.config import get_settings
from shared.database.models import User
from shared.database.repository_dependencies import UserRepositoryDep
from shared.exceptions.authentication_exception import AuthenticationException
from shared.exceptions.validation_exception import ValidationException
from shared.logging import get_logger

settings = get_settings()
get_logger("passlib").setLevel(stdLogging.ERROR)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"v1{settings.JWT.TOKEN_URL}", auto_error=False)

BearerToken = Annotated[str, Depends(oauth2_scheme)]


class JwtAuthService:
    """Service for handling user authentication and authorization."""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def __init__(self, user_repo: UserRepositoryDep):
        self.user_repo = user_repo

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password for storing."""
        return cls.pwd_context.hash(password)

    def login(self, username: str, password: str, response: Response) -> tuple[User, str]:
        user = self.user_repo.get_by(username=username)
        if not user or not self.verify_password(password, user.hashed_password):
            raise AuthenticationException.invalid_credentials()

        self._set_refresh_cookie(response, self.create_refresh_token(data={"sub": user.username, "user_id": user.id}))

        return user, self.create_access_token(data={"sub": user.username, "user_id": user.id})

    def authenticated_user(self, token: str) -> User:
        """Extract and validate user from JWT access token."""
        if not token:
            raise AuthenticationException.missing_token()

        try:
            payload = jwt.decode(token, settings.JWT.SECRET_KEY.get_secret_value(), algorithms=[settings.JWT.ALGORITHM])
            if payload.get("type") != "access":
                raise AuthenticationException.invalid_token()
            username: str = payload.get("sub")
            if username is None:
                raise AuthenticationException.invalid_token()
        except jwt.ExpiredSignatureError as e:
            raise AuthenticationException.expired_token() from e
        except jwt.InvalidTokenError as e:
            raise AuthenticationException.invalid_token() from e

        user = self.user_repo.get_by(username=username)
        if not user:
            raise AuthenticationException.invalid_credentials()

        return user

    def refresh_access_token(self, refresh_token: str, response: Response) -> str:
        """
        Generate new access token from refresh token cookie.
        Also rotates the refresh token.
        """
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT.SECRET_KEY.get_secret_value(),
                algorithms=[settings.JWT.ALGORITHM],
            )

            if payload.get("type") != "refresh":
                raise AuthenticationException.invalid_token()

            username, user_id = payload.get("sub"), payload.get("user_id")
            if not username or not user_id:
                raise AuthenticationException.invalid_token()

            user = self.user_repo.get_by(username=username)
            if not user or user.id != user_id:
                raise AuthenticationException.invalid_credentials()

            # Rotate refresh token
            self._set_refresh_cookie(response, self.create_refresh_token(data={"sub": username, "user_id": user_id}))

            return self.create_access_token(data={"sub": username, "user_id": user_id})

        except jwt.ExpiredSignatureError as e:
            raise AuthenticationException.expired_token() from e
        except jwt.InvalidTokenError as e:
            raise AuthenticationException.invalid_token() from e

    def logout(self, response: Response) -> None:
        """Clear refresh token cookie on logout."""
        self._clear_refresh_cookie(response)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """Create short-lived JWT access token."""
        expire = (
            datetime.now(timezone.utc) + expires_delta
            if expires_delta
            else datetime.now(timezone.utc) + timedelta(minutes=settings.JWT.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        to_encode = data.copy()
        to_encode.update(
            {
                "exp": expire,
                "type": "access",
                "iat": datetime.now(timezone.utc),
            },
        )
        return jwt.encode(to_encode, settings.JWT.SECRET_KEY.get_secret_value(), algorithm=settings.JWT.ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create long-lived JWT refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = data.copy()
        to_encode.update(
            {
                "exp": expire,
                "type": "refresh",
                "iat": datetime.now(timezone.utc),
            },
        )
        return jwt.encode(to_encode, settings.JWT.SECRET_KEY.get_secret_value(), algorithm=settings.JWT.ALGORITHM)

    @staticmethod
    def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
        """Set refresh token as secure HTTPOnly cookie."""
        response.set_cookie(
            key="refresh_token",
            path="/api/v1/auth",  # Limit cookie scope to auth endpoints only
            httponly=True,  # Prevents JavaScript access (XSS protection)
            samesite="strict",  # CSRF protection
            secure=settings.APP.ENV == "production",
            value=refresh_token,
            max_age=settings.JWT.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    @staticmethod
    def _clear_refresh_cookie(response: Response) -> None:
        """Clear refresh token cookie."""
        response.delete_cookie(
            key="refresh_token",
            path="/api/v1/auth",
            httponly=True,
            samesite="strict",
            secure=settings.APP.ENV == "production",
        )

    def register_user(self, email: str, username: str, password: str) -> User:
        """Register a new user with validation."""
        if self.user_repo.get_by(email=email):
            raise ValidationException(
                message="Registration failed",
                field_errors={"email": ["This email is already registered"]},
                error_code="duplicate_email",
            )

        if self.user_repo.get_by(username=username):
            raise ValidationException(
                message="Registration failed",
                field_errors={"username": ["This username is already taken"]},
                error_code="duplicate_username",
            )

        password_errors = JwtAuthService._validate_password(password)
        if password_errors:
            raise ValidationException(
                message="Password validation failed",
                field_errors={"password": password_errors},
                error_code="invalid_password",
            )

        return self.user_repo.create(
            email=email,
            username=username,
            hashed_password=self.hash_password(password),
        )

    @staticmethod
    def _validate_password(password: str) -> list[str]:
        """Validate password strength."""
        validation_rules = [
            (lambda pwd: len(pwd) >= 8, "Password must be at least 8 characters long"),
            (lambda pwd: any(c.isupper() for c in pwd), "Password must contain an uppercase letter"),
            (lambda pwd: any(c.islower() for c in pwd), "Password must contain a lowercase letter"),
            (lambda pwd: any(c.isdigit() for c in pwd), "Password must contain a number"),
        ]

        return [msg for rule, msg in validation_rules if not rule(password)]


def get_jwt_auth_service(user_repo: UserRepositoryDep) -> JwtAuthService:
    return JwtAuthService(user_repo)


JwtAuthServiceDep = Annotated[JwtAuthService, Depends(get_jwt_auth_service)]


def get_jwt_user(auth_service: JwtAuthServiceDep, token: BearerToken) -> User:
    return auth_service.authenticated_user(token)


BearerTokenUser = Annotated[User, Depends(get_jwt_user)]

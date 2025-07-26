# backend/shared/auth/auth_service.py
import logging as stdLogging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from shared.config import get_settings
from shared.database.models import User
from shared.database.repository_dependencies import UserRepositoryDep
from shared.logging import get_logger

settings = get_settings()
get_logger("passlib").setLevel(stdLogging.ERROR)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.JWT.TOKEN_URL, auto_error=False)

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
    def get_password_hash(cls, password: str) -> str:
        """Hash a password for storing."""
        return cls.pwd_context.hash(password)

    def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate a user by username and password."""
        user = self.user_repo.get_by(username=username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """Create JWT access token."""
        expire = (
            datetime.now(timezone.utc) + expires_delta
            if expires_delta
            else datetime.now(timezone.utc) + timedelta(minutes=15)
        )

        to_encode = data.copy()
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.JWT.SECRET_KEY, algorithm=settings.JWT.ALGORITHM)

    def get_current_user_from_token(self, token: str) -> User:
        """Extract and validate user from JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, settings.JWT.SECRET_KEY, algorithms=[settings.JWT.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except jwt.InvalidTokenError as err:
            raise credentials_exception from err

        user = self.user_repo.get_by(username=username)
        if user is None:
            raise credentials_exception

        return user

    def register_user(self, email: str, username: str, password: str) -> User:
        if self.user_repo.get_by(email=email):
            raise ValueError("Email already registered")
        if self.user_repo.get_by(username=username):
            raise ValueError("Username already taken")

        JwtAuthService.validate_password(password)

        return self.user_repo.create(
            email=email,
            username=username,
            hashed_password=self.get_password_hash(password),
        )

    @staticmethod
    def validate_password(password: str) -> bool:
        validation_rules = [
            (lambda pwd: len(pwd) >= 8, "Password must be at least 8 characters long"),
            (lambda pwd: any(c.isupper() for c in pwd), "Password must contain an uppercase letter"),
            (lambda pwd: any(c.islower() for c in pwd), "Password must contain a lowercase letter"),
            (lambda pwd: any(c.isdigit() for c in pwd), "Password must contain a number"),
        ]

        failed_rules = [msg for rule, msg in validation_rules if not rule(password)]
        if failed_rules:
            raise ValueError("; ".join(failed_rules))

        return True


# Dependency functions
def get_jwt_auth_service(user_repo: UserRepositoryDep) -> JwtAuthService:
    return JwtAuthService(user_repo)


JwtAuthServiceDep = Annotated[JwtAuthService, Depends(get_jwt_auth_service)]


def require_jwt_user(auth_service: JwtAuthServiceDep, token: BearerToken) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    auth_service.get_current_user_from_token(token)


BearerTokenUser = Annotated[User, Depends(require_jwt_user)]

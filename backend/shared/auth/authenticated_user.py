from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from shared.auth.api_key import ApiKey, ApiKeyServiceDep
from shared.auth.oauth2_password_bearer import BearerToken, JwtAuthServiceDep
from shared.config import get_settings
from shared.database.models import ApiKey as ApiKeyModel
from shared.database.models import ApiKeyScope, User
from shared.exceptions.authentication_exception import AuthenticationException
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    user: User
    payload: ApiKeyModel | BearerToken


class AuthService:
    """Service that handles all authentication methods with user context"""

    def __init__(self, jwt_service: JwtAuthServiceDep, api_key_service: ApiKeyServiceDep):
        self.jwt_service = jwt_service
        self.api_key_service = api_key_service

    def try_with_api_key(self, api_key: str) -> AuthenticatedUser | None:
        """Authenticate using user-linked API key"""
        try:
            api_key_model = self.api_key_service.authenticated_key(api_key)
            return AuthenticatedUser(
                user=api_key_model.user,
                payload=self.api_key_service.get_api_key(api_key),
            )
        except Exception:
            return None

    def try_with_jwt(self, token: str) -> AuthenticatedUser | None:
        """Authenticate using JWT token"""
        try:
            user = self.jwt_service.authenticated_user(token)
            return AuthenticatedUser(user=user, payload=token)
        except Exception:
            return None


# Dependencies
def get_auth_service(jwt_service: JwtAuthServiceDep, api_key_service: ApiKeyServiceDep) -> AuthService:
    return AuthService(jwt_service=jwt_service, api_key_service=api_key_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_optional_auth(
    api_key: ApiKey,
    token: BearerToken,
    auth_service: AuthServiceDep,
) -> AuthenticatedUser | None:
    """Optional authentication - returns None for anonymous users"""
    if user := auth_service.try_with_api_key(api_key):
        return user

    if user := auth_service.try_with_jwt(token):
        return user

    return None


MaybeAuthedUser = Annotated[AuthenticatedUser | None, Depends(get_optional_auth)]


def get_authed_user(user: MaybeAuthedUser) -> AuthenticatedUser:
    if not user:
        raise AuthenticationException.missing_auth()
    return user


AuthedUser = Annotated[AuthenticatedUser, Depends(get_authed_user)]


def require_api_key_or_jwt_read(user: AuthedUser) -> User:
    """Require either API key with read permissions or valid JWT token"""
    if user is None:
        raise AuthenticationException.insufficient_permissions(ApiKeyScope.READ.value)

    if isinstance(user.payload, ApiKeyModel) and not user.payload.has_permission(ApiKeyScope.READ):
        raise AuthenticationException.insufficient_permissions(ApiKeyScope.WRITE.value)

    return user


def require_api_key_or_jwt_write(user: AuthedUser) -> User:
    """Require either API key with write permissions or valid JWT token"""
    if user is None:
        raise AuthenticationException.insufficient_permissions(ApiKeyScope.WRITE.value)

    if isinstance(user.payload, ApiKeyModel) and not user.payload.has_permission(ApiKeyScope.READ):
        raise AuthenticationException.insufficient_permissions(ApiKeyScope.WRITE.value)

    return user

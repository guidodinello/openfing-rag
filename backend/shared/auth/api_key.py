import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from shared.config import get_settings

settings = get_settings()

api_key_header = APIKeyHeader(
    name="X-API-Key",
    description="API key for authentication. Contact admin for access.",
    auto_error=False,
)

ApiKey = Annotated[str, Depends(api_key_header)]


@dataclass(frozen=True, slots=True)
class UserPermissions:
    admin: bool
    write: bool
    read: bool


@dataclass(frozen=True, slots=True)
class ApiKeyUserInfo:
    api_key: str
    permissions: UserPermissions
    authenticated: bool


class APIKeyAuth:
    @staticmethod
    def api_key_user(api_key: str) -> ApiKeyUserInfo:
        """Verify API key and return user info with permissions."""
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        valid_key = False
        for valid_api_key in settings.API_KEYS.all:
            if secrets.compare_digest(api_key, valid_api_key):
                valid_key = True
                break

        if not valid_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        return ApiKeyUserInfo(
            api_key=api_key,
            permissions=APIKeyAuth._get_permissions(api_key),
            authenticated=True,
        )

    @staticmethod
    def _get_permissions(api_key: str) -> UserPermissions:
        """Determine permissions based on API key type."""
        return UserPermissions(
            admin=api_key in settings.API_KEYS.ADMIN,
            read=api_key in settings.API_KEYS.all,
            write=api_key in (settings.API_KEYS.ADMIN + settings.API_KEYS.WRITE),
        )


# Dependency functions
def get_api_key_user(api_key: ApiKey) -> ApiKeyUserInfo:
    """Get authenticated user with required API key."""
    return APIKeyAuth.api_key_user(api_key)


APIKeyUser = Annotated[ApiKeyUserInfo, Depends(get_api_key_user)]


def require_read_permission(user: APIKeyUser) -> ApiKeyUserInfo:
    if not user.permissions.read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read permission required",
        )
    return user


def require_write_permission(user: APIKeyUser) -> ApiKeyUserInfo:
    if not user.permissions.write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write permission required",
        )
    return user


def require_admin_permission(user: APIKeyUser) -> ApiKeyUserInfo:
    if not user.permissions.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required",
        )
    return user


ReadUser = Annotated[ApiKeyUserInfo, Depends(require_read_permission)]
WriteUser = Annotated[ApiKeyUserInfo, Depends(require_write_permission)]
AdminUser = Annotated[ApiKeyUserInfo, Depends(require_admin_permission)]

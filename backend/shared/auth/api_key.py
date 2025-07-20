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
    auto_error=True,
)


@dataclass(frozen=True, slots=True)
class UserPermissions:
    admin: bool
    write: bool
    read: bool


@dataclass(frozen=True, slots=True)
class UserAuthInfo:
    api_key: str
    permissions: UserPermissions
    authenticated: bool


class APIKeyAuth:
    @staticmethod
    def verify_api_key(api_key: str) -> UserAuthInfo:
        """Verify API key and return user info with permissions."""
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

        return UserAuthInfo(
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
def get_api_key_user(api_key: str = Depends(api_key_header)) -> UserAuthInfo:
    """Get authenticated user with required API key."""
    return APIKeyAuth.verify_api_key(api_key)


def require_read_permission(
    user: UserAuthInfo = Depends(get_api_key_user),
) -> UserAuthInfo:
    if not user.permissions.read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read permission required",
        )
    return user


def require_write_permission(
    user: UserAuthInfo = Depends(get_api_key_user),
) -> UserAuthInfo:
    if not user.permissions.write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write permission required",
        )
    return user


def require_admin_permission(
    user: UserAuthInfo = Depends(get_api_key_user),
) -> UserAuthInfo:
    if not user.permissions.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required",
        )
    return user


# Type aliases for clean dependency injection
APIKeyUser = Annotated[dict, Depends(get_api_key_user)]
ReadUser = Annotated[dict, Depends(require_read_permission)]
WriteUser = Annotated[dict, Depends(require_write_permission)]
AdminUser = Annotated[dict, Depends(require_admin_permission)]

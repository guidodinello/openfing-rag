from fastapi import HTTPException, status

from shared.auth.api_key import ApiKey, APIKeyAuth
from shared.auth.oauth2_password_bearer import BearerToken, JwtAuthServiceDep


def require_api_key_or_jwt_read(
    auth_service: JwtAuthServiceDep,
    api_key: ApiKey,
    token: BearerToken,
) -> None:
    """Require either API key with read permissions or valid JWT token"""
    if api_key:
        try:
            user_info = APIKeyAuth.api_key_user(api_key)
            if user_info.permissions.read:
                return  # Success
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Read permission required")
        except HTTPException:
            pass

    if token:
        try:
            auth_service.get_current_user_from_token(token)
            return  # Success
        except HTTPException:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required: API key with read permissions or Bearer token",
        headers={"WWW-Authenticate": "ApiKey, Bearer"},
    )


def require_api_key_or_jwt_write(
    auth_service: JwtAuthServiceDep,
    api_key: ApiKey,
    token: BearerToken,
) -> None:
    """Require either API key with write permissions or valid JWT token"""
    if api_key:
        try:
            user_info = APIKeyAuth.api_key_user(api_key)
            if user_info.permissions.write:
                return  # Success
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write permission required")
        except HTTPException:
            pass

    if token:
        try:
            auth_service.get_current_user_from_token(token)
            return  # Success
        except HTTPException:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required: API key with write permissions or Bearer token",
        headers={"WWW-Authenticate": "ApiKey, Bearer"},
    )

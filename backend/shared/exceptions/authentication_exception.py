from typing import Self

from fastapi import status

from shared.enums.auth_error_codes import AuthErrorCodes


class AuthenticationException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: AuthErrorCodes = AuthErrorCodes.INVALID_CREDENTIALS,
        headers: dict[str, str] | None = None,
        details: dict | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.headers = headers or {}
        self.details = details or {}
        super().__init__(message)

    @classmethod
    def missing_auth(cls) -> Self:
        return cls(
            message="Authentication required",
            error_code=AuthErrorCodes.MISSING_AUTH,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "ApiKey, Bearer"},
        )

    @classmethod
    def missing_api_key(cls) -> Self:
        return cls(
            message="API key is required",
            error_code=AuthErrorCodes.MISSING_API_KEY,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "ApiKey"},
        )

    @classmethod
    def missing_token(cls) -> Self:
        return cls(
            message="JWT token is required",
            error_code=AuthErrorCodes.MISSING_TOKEN,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @classmethod
    def invalid_credentials(cls) -> Self:
        return cls(
            message="Incorrect username or password",
            error_code=AuthErrorCodes.INVALID_CREDENTIALS,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @classmethod
    def expired_token(cls) -> Self:
        return cls(
            message="Authentication token has expired",
            error_code=AuthErrorCodes.TOKEN_EXPIRED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @classmethod
    def invalid_token(cls) -> Self:
        return cls(
            message="Invalid authentication token",
            error_code=AuthErrorCodes.INVALID_TOKEN,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @classmethod
    def insufficient_permissions(cls, required_permission: str = "") -> Self:
        message = "Insufficient permissions"
        if required_permission:
            message += f": {required_permission} required"

        return cls(
            message=message,
            error_code=AuthErrorCodes.INSUFFICIENT_PERMISSIONS,
            status_code=status.HTTP_403_FORBIDDEN,
            details={"required_permission": required_permission},
        )

    @classmethod
    def invalid_api_key(cls) -> Self:
        return cls(
            message="Invalid API key",
            error_code=AuthErrorCodes.INVALID_API_KEY,
            status_code=status.HTTP_403_FORBIDDEN,
            headers={"WWW-Authenticate": "ApiKey"},
        )

    @classmethod
    def expired_api_key(cls) -> Self:
        return cls(
            message="API key has expired",
            error_code=AuthErrorCodes.API_KEY_EXPIRED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "ApiKey"},
        )

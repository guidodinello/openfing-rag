from typing import Self

from shared.enums.auth_error_codes import AuthErrorCodes


class AuthenticationException(Exception):
    def __init__(
        self,
        message: str,
        error_code: AuthErrorCodes = AuthErrorCodes.INVALID_CREDENTIALS,
        status_code: int = 401,
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
    def invalid_credentials(cls) -> Self:
        return cls(
            message="Incorrect username or password",
            error_code=AuthErrorCodes.INVALID_CREDENTIALS,
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @classmethod
    def token_expired(cls) -> Self:
        return cls(
            message="Authentication token has expired",
            error_code=AuthErrorCodes.TOKEN_EXPIRED,
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )

    @classmethod
    def invalid_token(cls) -> Self:
        return cls(
            message="Invalid authentication token",
            error_code=AuthErrorCodes.INVALID_TOKEN,
            status_code=401,
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
            status_code=403,
            details={"required_permission": required_permission},
        )

    @classmethod
    def invalid_api_key(cls) -> Self:
        return cls(
            message="Invalid API key",
            error_code=AuthErrorCodes.INVALID_API_KEY,
            status_code=401,
            headers={"WWW-Authenticate": "ApiKey"},
        )

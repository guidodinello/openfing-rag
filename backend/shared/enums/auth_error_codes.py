from enum import StrEnum


class AuthErrorCodes(StrEnum):
    # Authentication errors
    INVALID_CREDENTIALS = "invalid_credentials"
    INVALID_TOKEN = "invalid_token"
    TOKEN_EXPIRED = "token_expired"
    MISSING_API_KEY = "missing_api_key"
    INVALID_API_KEY = "invalid_api_key"
    USER_NOT_FOUND = "user_not_found"

    # Authorization errors
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    ACCESS_DENIED = "access_denied"

from enum import StrEnum


class AuthErrorCodes(StrEnum):
    MISSING_AUTH = "authentication_required"

    MISSING_TOKEN = "missing_token"
    INVALID_CREDENTIALS = "invalid_credentials"
    INVALID_TOKEN = "invalid_token"
    TOKEN_EXPIRED = "token_expired"

    MISSING_API_KEY = "missing_api_key"
    INVALID_API_KEY = "invalid_api_key"
    API_KEY_EXPIRED = "api_key_expired"

    USER_NOT_FOUND = "user_not_found"

    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"

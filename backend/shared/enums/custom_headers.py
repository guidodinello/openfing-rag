from enum import StrEnum


class CustomHeaders(StrEnum):
    """Standard HTTP headers used across the application."""

    # Authentication headers
    API_KEY = "X-API-Key"
    AUTHORIZATION = "Authorization"

    # Request tracking headers
    REQUEST_ID = "X-Request-ID"
    PROCESS_TIME = "X-Process-Time"

    # Session and chat context headers
    SESSION_TYPE = "X-Session-Type"
    SESSION_ID = "X-Session-ID"
    CONVERSATION_ID = "X-Conversation-ID"
    USER_CONTEXT = "X-User-Context"

    # Common proxy headers (for IP detection)
    FORWARDED_FOR = "X-Forwarded-For"
    REAL_IP = "X-Real-IP"
    USER_AGENT = "User-Agent"


class HeaderGroups:
    TRACKING = [
        CustomHeaders.REQUEST_ID,
        CustomHeaders.PROCESS_TIME,
    ]

    CHAT_SESSION = [
        CustomHeaders.SESSION_TYPE,
        CustomHeaders.SESSION_ID,
        CustomHeaders.CONVERSATION_ID,
        CustomHeaders.USER_CONTEXT,
    ]

    AUTH = [
        CustomHeaders.API_KEY,
        CustomHeaders.AUTHORIZATION,
    ]

    # Headers to expose in CORS
    EXPOSE_HEADERS = TRACKING + CHAT_SESSION

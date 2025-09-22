import json
import re
import secrets
import time
from dataclasses import asdict, dataclass
from enum import StrEnum

from fastapi import Request, Response

from shared.enums import CustomHeaders
from shared.logging import get_logger
from shared.middlewares.utils import CallNext, safe_int_parse

logger = get_logger(__name__)

CHAT_ENDPOINTS = {
    "/api/v1/services/generator/chat",
}

SESSION_ID_PATTERN = re.compile(r"^anon_[A-Za-z0-9_-]{16,32}_\d{10}$")


def generate_session_id() -> str:
    return f"anon_{secrets.token_urlsafe(16)}_{int(time.time())}"


def validate_session_id(session_id: str | None) -> str:
    """
    Validate and sanitize session ID.
    Returns a valid session ID (existing if valid, new if invalid/missing).
    """
    if not session_id:
        return generate_session_id()

    if not SESSION_ID_PATTERN.match(session_id):
        logger.warning(f"Invalid session ID format received: {session_id[:50]}... - generating new one")
        return generate_session_id()

    return session_id


class SessionType(StrEnum):
    ANONYMOUS = "anonymous"
    JWT = "jwt_token"
    API_KEY = "api_key"


def determine_session_type(request: Request) -> SessionType:
    """Determine the type of session based on authentication headers."""
    api_key = request.headers.get(CustomHeaders.API_KEY)
    auth_header = request.headers.get(CustomHeaders.AUTHORIZATION)

    if api_key:
        return SessionType.API_KEY
    elif auth_header and auth_header.startswith("Bearer "):
        return SessionType.JWT
    else:
        return SessionType.ANONYMOUS


@dataclass(frozen=True, slots=True)
class ChatSessionContext:
    session_id: str
    session_type: SessionType
    conversation_id: int | None = None


async def chat_session_middleware(request: Request, call_next: CallNext) -> Response:
    """
    Middleware to track chat sessions with user context.
    Handles session ID generation and validation for anonymous users.
    """
    is_chat_endpoint = any(request.url.path.startswith(endpoint) for endpoint in CHAT_ENDPOINTS)
    if not is_chat_endpoint:
        return await call_next(request)

    conversation_id_header = request.headers.get(CustomHeaders.CONVERSATION_ID)
    conversation_id = safe_int_parse(conversation_id_header) if conversation_id_header else None

    session_id_header = request.headers.get(CustomHeaders.SESSION_ID)
    session_type = determine_session_type(request)

    if session_type == SessionType.ANONYMOUS:
        session_id = validate_session_id(session_id_header)
    else:
        session_id = session_id_header or f"auth_{getattr(request.state, 'request_id', 'unknown')}"

    chat_context = ChatSessionContext(
        session_id=session_id,
        session_type=session_type,
        conversation_id=conversation_id,
    )
    request.state.chat_context = chat_context

    logger.info(
        f"Chat session initialized: {
            json.dumps(
                {
                    'request_id': getattr(request.state, 'request_id', 'unknown'),
                    'endpoint': request.url.path,
                    **asdict(chat_context),
                }
            )
        }",
    )

    response = await call_next(request)

    response.headers[CustomHeaders.SESSION_TYPE] = chat_context.session_type
    response.headers[CustomHeaders.SESSION_ID] = chat_context.session_id
    if chat_context.conversation_id:
        response.headers[CustomHeaders.CONVERSATION_ID] = str(chat_context.conversation_id)

    return response

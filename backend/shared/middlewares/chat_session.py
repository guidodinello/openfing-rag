import json

from fastapi import Request, Response

from shared.enums import CustomHeaders
from shared.logging import get_logger
from shared.middlewares.utils import CallNext

logger = get_logger(__name__)

CHAT_ENDPOINTS = {
    "/api/v1/services/generator/chat",
}


async def chat_session_middleware(request: Request, call_next: CallNext) -> Response:
    """Middleware to track chat sessions with user context."""
    is_chat_endpoint = any(request.url.path.startswith(endpoint) for endpoint in CHAT_ENDPOINTS)
    if not is_chat_endpoint:
        return await call_next(request)

    conversation_id_header = request.headers.get(CustomHeaders.CONVERSATION_ID)
    conversation_id = safe_int_parse(conversation_id_header) if conversation_id_header else None

    api_key = request.headers.get(CustomHeaders.API_KEY)
    auth_header = request.headers.get(CustomHeaders.AUTHORIZATION)

    session_id = request.headers.get(CustomHeaders.SESSION_ID, f"anon_{request.state.request_id}")
    if not session_id:
        session_id = f"session_{getattr(request.state, 'request_id', 'unknown')}"

    session_type = "anonymous"
    if api_key:
        session_type = "api_key"
    elif auth_header and auth_header.startswith("Bearer "):
        session_type = "jwt_token"

    request.state.chat_context = {
        "session_id": session_id,
        "conversation_id": conversation_id,
        "session_type": session_type,
    }

    logger.info(
        f"Chat session initialized: {
            json.dumps(
                {
                    'request_id': getattr(request.state, 'request_id', 'unknown'),
                    'session_type': session_type,
                    'session_id': session_id,
                    'conversation_id': conversation_id,
                    'endpoint': request.url.path,
                    'method': request.method,
                }
            )
        }",
    )

    response = await call_next(request)

    response.headers[CustomHeaders.SESSION_TYPE] = session_type
    response.headers[CustomHeaders.SESSION_ID] = session_id

    if conversation_id:
        response.headers[CustomHeaders.CONVERSATION_ID] = str(conversation_id)

    return response


def safe_int_parse(val: str) -> int | None:
    """Safely parse string to integer, returning None for invalid values."""
    if val is None:
        return None

    try:
        return int(val)
    except (TypeError, ValueError):
        logger.warning(f"Invalid integer format: '{val}' - returning None")
        return None

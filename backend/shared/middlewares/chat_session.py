import json

from fastapi import Request, Response

from shared.enums import CustomHeaders
from shared.logging import get_logger
from shared.middlewares.utils import CallNext

logger = get_logger(__name__)


async def chat_session_middleware(request: Request, call_next: CallNext) -> Response:
    """Enhanced middleware to track chat sessions with user context."""
    if not request.url.path.startswith("/api/v1/services/generator/chat"):
        return await call_next(request)

    user_id = None
    session_type = "anonymous"

    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.id
        session_type = "authenticated"

    conversation_id = request.headers.get(CustomHeaders.CONVERSATION_ID)
    session_id = request.headers.get("X-Session-ID", f"anon_{request.state.request_id}")

    request.state.chat_context = {
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": conversation_id,
        "session_type": session_type,
        "is_authenticated": user_id is not None,
    }

    logger.info(
        f"Chat session: {
            json.dumps(
                {
                    'request_id': getattr(request.state, 'request_id', 'unknown'),
                    'session_type': session_type,
                    'user_id': user_id,
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
        response.headers[CustomHeaders.CONVERSATION_ID] = conversation_id
    if user_id:
        response.headers[CustomHeaders.USER_CONTEXT] = "authenticated"

    return response

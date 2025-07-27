import hashlib
import json
import uuid
from typing import Any

from fastapi import Request, Response

from shared.enums import CustomHeaders
from shared.logging import get_logger
from shared.middlewares.utils import CallNext, get_client_ip

logger = get_logger(__name__)


async def request_logging_middleware(request: Request, call_next: CallNext) -> Response:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    logger.info(
        f"Request {request_id} started: {
            json.dumps(
                {
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'query_params': str(request.query_params) if request.query_params else None,
                    'client_ip': get_client_ip(request),
                    'user_agent': request.headers.get(CustomHeaders.USER_AGENT),
                    **_extract_auth_context(request),
                },
                default=str,
            )
        }",
    )

    response = await call_next(request)

    logger.info(
        f"Request {request_id} completed: {
            json.dumps(
                {
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                },
                default=str,
            )
        }",
    )

    response.headers[CustomHeaders.REQUEST_ID] = request_id
    return response


def _extract_auth_context(request: Request) -> dict[str, Any]:
    """Extract authentication context for logging (without validation)."""
    context: dict[str, Any] = {"auth_type": None}

    if api_key := request.headers.get(CustomHeaders.API_KEY):
        context.update(
            {
                "auth_type": "api_key",
                "api_key_hash": _hash_sensitive_data(api_key),
            },
        )

    elif auth_header := request.headers.get(CustomHeaders.AUTHORIZATION):
        if auth_header.startswith("Bearer "):
            context.update(
                {
                    "auth_type": "bearer_token",
                    "token_hash": _hash_sensitive_data(auth_header.replace("Bearer ", "")),
                },
            )

    return context


def _hash_sensitive_data(data: str) -> str:
    """Create a safe, loggable hash"""
    return hashlib.sha256(data.encode()).hexdigest()[:16]

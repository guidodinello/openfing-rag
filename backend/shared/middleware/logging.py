import hashlib
import json
import uuid
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from shared.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request details and timing."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            f"Request {request_id} started: {
                json.dumps(
                    {
                        'request_id': request_id,
                        'method': request.method,
                        'path': request.url.path,
                        'client_ip': self._get_client_ip(request),
                        'user_agent': request.headers.get('user-agent'),
                        **self._extract_auth_context(request),
                    },
                    default=str,
                )
            }",
        )

        try:
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

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            logger.error(
                f"Request {request_id} failed: {
                    json.dumps(
                        {
                            'request_id': request_id,
                            'method': request.method,
                            'path': request.url.path,
                            'error': str(e),
                            'error_type': type(e).__name__,
                        },
                        default=str,
                    )
                }",
                exc_info=True,
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP considering proxies."""
        if forwarded_for := request.headers.get("X-Forwarded-For"):
            return forwarded_for.split(",")[0].strip()
        if real_ip := request.headers.get("X-Real-IP"):
            return real_ip
        return request.client.host if request.client else "unknown"

    def _extract_auth_context(self, request: Request) -> dict[str, Any]:
        """Extract authentication context for logging (without validation)."""
        context: dict[str, Any] = {"auth_type": None}

        if api_key := request.headers.get("X-API-Key"):
            context.update(
                {
                    "auth_type": "api_key",
                    "api_key_hash": self._hash_api_key(api_key),
                },
            )

        elif auth_header := request.headers.get("Authorization"):
            if auth_header.startswith("Bearer "):
                context.update(
                    {
                        "auth_type": "bearer_token",
                        "token_hash": self._hash_token(auth_header),
                    },
                )

        return context

    def _hash_api_key(self, api_key: str) -> str:
        """Create a safe, loggable hash of the API key."""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

    def _hash_token(self, auth_header: str) -> str:
        """Create a safe, loggable hash of the bearer token."""
        token = auth_header.replace("Bearer ", "")
        return hashlib.sha256(token.encode()).hexdigest()[:16]

import hashlib
import json
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from shared.auth.api_key import APIKeyAuth, UserAuthInfo, UserPermissions
from shared.logging.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request details and timing."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = str(uuid.uuid4())

        # Attach request_id to request state
        request.state.request_id = request_id

        # Extract user context if available
        user_context = self._extract_user_context(request)

        # Store user context in request state for use in endpoints
        request.state.user_context = user_context

        request_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            **user_context,
        }
        logger.info(f"Request {request_id} started {json.dumps(request_data, default=str)}")

        try:
            response = await call_next(request)

            response_data = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                **user_context,
            }
            logger.info(f"Request {request_id} completed {json.dumps(response_data, default=str)}")

            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            error_data = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "error_type": type(e).__name__,
                **user_context,
            }
            logger.error(f"Request {request_id} failed {json.dumps(error_data, default=str)}", exc_info=True)
            raise

    def _extract_user_context(self, request: Request) -> dict:
        """Extract user identification from request."""
        if not (api_key := request.headers.get("X-API-Key")):
            return {
                "api_key_hash": None,
                "permissions": None,
                "authenticated": False,
            }

        try:
            user_info = APIKeyAuth.verify_api_key(api_key)
        except Exception:
            user_info = UserAuthInfo(
                api_key=api_key,
                permissions=UserPermissions(admin=False, read=False, write=False),
                authenticated=False,
            )

        return {
            "api_key_hash": self._hash_api_key(api_key),
            "permissions": user_info.permissions,
            "authenticated": user_info.authenticated,
        }

    def _hash_api_key(self, api_key: str) -> str:
        """Create a safe, loggable hash of the API key."""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP considering proxies."""
        if forwarded_for := request.headers.get("X-Forwarded-For"):
            return forwarded_for.split(",")[0].strip()

        if real_ip := request.headers.get("X-Real-IP"):
            return real_ip

        return request.client.host if request.client else "unknown"

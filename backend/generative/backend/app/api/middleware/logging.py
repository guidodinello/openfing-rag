import time
import uuid

from app.utils.logger import get_logger
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request details and timing."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Attach request_id to request state for potential use in route handlers
        request.state.request_id = request_id

        # Log the incoming request
        logger.info(
            f"Request {request_id} started: {request.method} {request.url.path}"
            f" - Client: {request.client.host if request.client else 'Unknown'}"
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate and log processing time
            process_time = (time.time() - start_time) * 1000
            formatted_process_time = "{0:.2f}".format(process_time)

            logger.info(
                f"Request {request_id} completed: {request.method} {request.url.path}"
                f" - Status: {response.status_code}"
                f" - Took: {formatted_process_time}ms"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            logger.exception(
                f"Request {request_id} failed: {request.method} {request.url.path}"
                f" - Error: {str(e)}"
            )
            raise

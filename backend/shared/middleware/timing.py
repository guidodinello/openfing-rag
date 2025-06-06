import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.logging.logger import get_logger

logger = get_logger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request processing time."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)

            process_time = (time.time() - start_time) * 1000
            formatted_process_time = f"{process_time:.2f}"

            # Add timing header to response
            response.headers["X-Process-Time"] = formatted_process_time

            logger.debug(
                f"Request processed: {request.method} {request.url.path} - Took: {formatted_process_time}ms",
            )

            return response

        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            formatted_process_time = f"{process_time:.2f}"

            logger.error(
                f"Request failed: {request.method} {request.url.path}"
                f" - Took: {formatted_process_time}ms"
                f" - Error: {str(e)}",
            )
            raise

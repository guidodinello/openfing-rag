import time

from app.utils.logger import get_logger
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = get_logger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request processing time."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and track timing information."""
        start_time = time.time()

        try:
            # Process the request and get response
            response = await call_next(request)

            # Calculate processing time
            process_time = (time.time() - start_time) * 1000
            formatted_process_time = "{0:.2f}".format(process_time)

            # Add timing header to response
            response.headers["X-Process-Time"] = formatted_process_time

            # Log timing information
            logger.debug(
                f"Request processed: {request.method} {request.url.path}"
                f" - Took: {formatted_process_time}ms"
            )

            return response

        except Exception as e:
            # Log error and processing time even if request fails
            process_time = (time.time() - start_time) * 1000
            formatted_process_time = "{0:.2f}".format(process_time)

            logger.error(
                f"Request failed: {request.method} {request.url.path}"
                f" - Took: {formatted_process_time}ms"
                f" - Error: {str(e)}"
            )
            raise

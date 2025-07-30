import time

from fastapi import Request, Response

from shared.enums import CustomHeaders
from shared.logging import get_logger
from shared.middlewares.utils import CallNext

logger = get_logger(__name__)


async def timing_middleware(request: Request, call_next: CallNext) -> Response:
    """Timing middleware to measure FastAPI processing time."""
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = (time.perf_counter() - start_time) * 1000
    formatted_process_time = f"{process_time:.2f}"

    response.headers[CustomHeaders.PROCESS_TIME] = formatted_process_time

    logger.debug(
        f"FastAPI processed: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Took: {formatted_process_time}ms",
    )

    return response

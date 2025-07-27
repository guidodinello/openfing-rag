from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from shared.config import get_settings
from shared.enums import CustomHeaders
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Unified handler for both FastAPI and Starlette HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    level_logger = logger.warning if 400 <= exc.status_code < 500 else logger.error

    level_logger(
        f"HTTP {exc.status_code} in request {request_id}: {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": str(exc.detail),
            "path": request.url.path,
            "method": request.method,
            "client_error": True,
            "exception_source": "starlette" if type(exc).__module__.startswith("starlette") else "fastapi",
        },
    )

    detail = exc.detail
    if not isinstance(detail, (str, dict, list)):
        detail = str(detail)

    response_content = {
        "detail": detail,
        "status_code": exc.status_code,
        "request_id": request_id,
    }

    if settings.APP.ENV == "local":
        response_content.update(
            {
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__,
                "exception_module": type(exc).__module__,
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
        headers={CustomHeaders.REQUEST_ID: request_id},
    )

from fastapi import Request
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.enums import CustomHeaders
from shared.exceptions.authentication_exception import AuthenticationException
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def authentication_exception_handler(request: Request, exc: AuthenticationException) -> JSONResponse:
    """Handle custom authentication exceptions with proper HTTP details."""
    request_id = getattr(request.state, "request_id", "unknown")

    log_level = logger.warning if exc.status_code == 401 else logger.error

    log_level(
        f"Authentication error in request {request_id}: {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "user_agent": request.headers.get(CustomHeaders.USER_AGENT),
        },
    )

    response_content = {
        "detail": exc.message,
        "error_code": exc.error_code,
        "request_id": request_id,
    }

    if exc.details:
        response_content["details"] = exc.details

    if settings.APP.ENV == "local":
        response_content.update(
            {
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
        headers={
            CustomHeaders.REQUEST_ID: request_id,
            **exc.headers,
        },
    )

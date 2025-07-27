from fastapi import Request
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.enums import CustomHeaders
from shared.exceptions.validation_exception import ValidationException
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def validation_exception_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """Handle custom validation exceptions with structured field errors."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        f"Custom validation error in request {request_id}: {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code,
            "field_errors": exc.field_errors,
        },
    )

    response_content = {
        "detail": exc.message,
        "message": "Validation failed. Please check the errors below.",
        "errors": exc.field_errors,
        "error_code": exc.error_code,
        "request_id": request_id,
    }

    if settings.APP.ENV == "local":
        response_content.update(
            {
                "path": request.url.path,
                "method": request.method,
            },
        )

    return JSONResponse(
        status_code=400,
        content=response_content,
        headers={CustomHeaders.REQUEST_ID: request_id},
    )

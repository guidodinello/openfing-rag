from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.enums import CustomHeaders
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors (422) with user-friendly messages."""
    request_id = getattr(request.state, "request_id", "unknown")

    errors = exc.errors()
    logger.warning(
        f"Validation error in request {request_id}: {len(errors)} validation failures",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "validation_error_count": len(errors),
            "validation_details": errors,
        },
    )

    formatted_errors = []
    for error in errors:
        field_path = []
        for loc in error["loc"]:
            if loc not in ("body", "query", "path", "header"):
                field_path.append(str(loc))

        field_name = " -> ".join(field_path) if field_path else "unknown"

        formatted_error = {
            "field": field_name,
            "message": _get_user_friendly_message(error),
            "type": error["type"],
        }

        if "ctx" in error and _is_useful_context(error["ctx"]):
            formatted_error["context"] = error["ctx"]

        formatted_errors.append(formatted_error)

    response_content = {
        "detail": "Validation error",
        "message": "The request contains invalid data. Please check the errors below.",
        "errors": formatted_errors,
        "request_id": request_id,
    }

    if settings.APP.ENV == "local":
        response_content.update(
            {
                "path": request.url.path,
                "method": request.method,
                "raw_errors": errors,
            },
        )

    return JSONResponse(
        status_code=422,
        content=response_content,
        headers={CustomHeaders.REQUEST_ID: request_id},
    )


def _get_user_friendly_message(error: dict) -> str:
    """Convert technical validation messages to user-friendly ones."""
    error_type = error["type"]
    msg = error["msg"]

    # Map common technical messages to user-friendly ones
    friendly_messages = {
        "missing": "This field is required",
        "value_error.missing": "This field is required",
        "type_error.missing": "This field is required",
        "string_too_short": "This field must be at least {min_length} characters long",
        "value_error.any_str.min_length": "This field must be at least {limit_value} characters long",
        "string_too_long": "This field cannot exceed {max_length} characters",
        "value_error.any_str.max_length": "This field cannot exceed {limit_value} characters",
        "value_error.email": "Please enter a valid email address",
        "value_error.url": "Please enter a valid URL",
        "int_parsing": "This field must be a valid number",
        "type_error.integer": "This field must be a valid number",
        "float_parsing": "This field must be a valid decimal number",
        "type_error.float": "This field must be a valid decimal number",
        "bool_parsing": "This field must be true or false",
        "type_error.bool": "This field must be true or false",
        "too_short": "At least {min_length} items are required",
        "value_error.list.min_items": "At least {limit_value} items are required",
        "too_long": "No more than {max_length} items are allowed",
        "value_error.list.max_items": "No more than {limit_value} items are allowed",
        "value_error.datetime": "Please enter a valid date and time",
        "value_error.date": "Please enter a valid date",
        "value_error.time": "Please enter a valid time",
        "enum": "This field must be one of: {permitted}",
        "type_error.enum": "Invalid choice. Please select a valid option",
        "json_invalid": "Invalid JSON format",
        "value_error.jsondecode": "Invalid JSON format",
        "greater_than": "This field must be greater than {gt}",
        "greater_than_equal": "This field must be greater than or equal to {ge}",
        "less_than": "This field must be less than {lt}",
        "less_than_equal": "This field must be less than or equal to {le}",
    }

    if error_type in friendly_messages:
        template = friendly_messages[error_type]
        # Format with context if available
        if "ctx" in error:
            try:
                return template.format(**error["ctx"])
            except (KeyError, ValueError):
                pass
        return template

    cleaned_msg = msg.replace("ensure this value", "this field").replace("field required", "this field is required")
    return cleaned_msg.capitalize() if cleaned_msg else "Invalid value"


def _is_useful_context(ctx: dict) -> bool:
    """Determine if context information is useful for the user."""
    useful_keys = {
        "limit_value",
        "min_length",
        "max_length",
        "gt",
        "ge",
        "lt",
        "le",
        "permitted",
        "given",
    }
    return any(key in ctx for key in useful_keys)

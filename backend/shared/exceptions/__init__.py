from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .authentication_exception import AuthenticationException
from .handlers.authentication_handler import authentication_exception_handler
from .handlers.global_handler import global_exception_handler
from .handlers.http_handler import http_exception_handler
from .handlers.request_validation_handler import request_validation_exception_handler
from .handlers.validation_handler import validation_exception_handler
from .validation_exception import ValidationException


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup all exception handlers for the application."""
    app.exception_handler(ValidationException)(validation_exception_handler)
    app.exception_handler(AuthenticationException)(authentication_exception_handler)

    app.exception_handler(RequestValidationError)(request_validation_exception_handler)

    app.exception_handler(StarletteHTTPException)(http_exception_handler)

    app.exception_handler(Exception)(global_exception_handler)

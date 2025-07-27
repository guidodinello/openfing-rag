from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings
from shared.enums.custom_headers import HeaderGroups

from .logging import request_logging_middleware
from .timing import timing_middleware

settings = get_settings()


def setup_middlewares(app: FastAPI) -> None:
    """Configure middleware for applications behind Nginx reverse proxy."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.APP.ENV == "local" else [str(settings.FRONTEND_URL)],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=HeaderGroups.EXPOSE_HEADERS,
    )

    app.middleware("http")(request_logging_middleware)

    app.middleware("http")(timing_middleware)

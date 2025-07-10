from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import get_settings

from .logging import RequestLoggingMiddleware
from .timing import TimingMiddleware

settings = get_settings()


def setup_middlewares(app: FastAPI) -> None:
    """Configure all middleware for the application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.APP.ENV == "local" else [settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TimingMiddleware)

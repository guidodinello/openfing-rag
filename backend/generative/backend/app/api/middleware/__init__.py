from app.api.middleware.logging import RequestLoggingMiddleware
from app.api.middleware.timing import TimingMiddleware
from app.core.config import get_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

settings = get_settings()


def setup_middlewares(app: FastAPI) -> None:
    """Configure all middleware for the application."""
    if settings.DEBUG:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[settings.FRONTEND_URL],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TimingMiddleware)

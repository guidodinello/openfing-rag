import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import APIRouter, FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from shared.api.v1.endpoints import auth, health
from shared.config import get_settings
from shared.database.api.router import crud_router
from shared.database.repository_dependencies import get_embedder
from shared.database.session import engine
from shared.exceptions import setup_exception_handlers
from shared.logging import get_logger
from shared.middlewares import setup_middlewares

from services.generator.api.router import generator_router
from services.scraper.api.router import scraper_router
from services.transcriber.api.router import transcriber_router

settings = get_settings()
logger = get_logger(__name__)


def init_sentry():
    """Initialize Sentry with proper error handling."""
    settings = get_settings()

    if settings.SENTRY.DSN and str(settings.SENTRY.DSN) != "http://127.0.0.1":
        try:
            sentry_sdk.init(
                dsn=str(settings.SENTRY.DSN),
                environment=settings.APP.ENV,
                release=f"{settings.APP.NAME}@{settings.APP.VERSION}",
                # Integrations
                integrations=[
                    StarletteIntegration(transaction_style="endpoint"),
                    FastApiIntegration(transaction_style="endpoint"),
                    SqlalchemyIntegration(),
                    LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
                ],
                # Performance
                traces_sample_rate=1.0 if settings.APP.ENV == "local" else 0.1,
                profiles_sample_rate=1.0 if settings.APP.ENV == "local" else 0.1,
                # Privacy
                send_default_pii=True,
                # Error filtering
                ignore_errors=[
                    KeyboardInterrupt,
                    "ConnectionResetError",
                ],
            )
            logger.info(f"Sentry initialized for {settings.APP.ENV} environment")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
    else:
        logger.warning("Sentry DSN not configured, skipping initialization")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: preload models on startup."""
    logger.info("Application startup")

    init_sentry()

    try:
        _ = get_embedder().model  # pre load embeddings model to cache
        logger.debug("Models preloaded successfully")
    except Exception as e:
        logger.error(f"Failed to preload models: {e}")
        raise

    yield

    logger.info("Application shutdown")
    try:
        engine.dispose()  # dispose database connection pool
        logger.debug("Database pool disposed successfully")
    except Exception as e:
        logger.error(f"Error disposing database pool: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP.NAME,
        description=settings.APP.DESCRIPTION,
        version=settings.APP.VERSION,
        root_path=settings.API_URL,
        openapi_url=settings.OPENAPI_URL,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        lifespan=lifespan,
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    setup_exception_handlers(app)
    setup_middlewares(app)

    app.include_router(health.routers.include_in(APIRouter()), tags=["health"])
    app.include_router(auth.routers.include_in(APIRouter()), prefix="/v1/auth", tags=["authentication"])

    for service_router in (scraper_router, generator_router, transcriber_router):
        app.include_router(service_router, prefix="/v1/services")

    app.include_router(crud_router, prefix="/v1")
    return app


app = create_app()

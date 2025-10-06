from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: preload models on startup."""
    logger.info("Application startup")
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
    app.include_router(auth.routers.include_in(APIRouter()), prefix="/v1", tags=["authentication"])

    for service_router in (scraper_router, generator_router, transcriber_router):
        app.include_router(service_router, prefix="/v1/services")

    app.include_router(crud_router, prefix="/v1")
    return app


app = create_app()

from fastapi import FastAPI

from services.generator.api.router import generator_router
from services.scraper.api.router import scraper_router
from services.transcriber.api.router import transcriber_router
from shared.api.v1.endpoints import health, list_routes
from shared.config import get_settings
from shared.middleware import setup_middlewares

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP.NAME,
        description=settings.APP.DESCRIPTION,
        version=settings.APP.VERSION,
        root_path=settings.API_URL,
        openapi_url=settings.OPENAPI_URL,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    setup_middlewares(app)

    for service_router in (scraper_router, generator_router, transcriber_router):
        app.include_router(service_router, prefix="/v1")

    app.include_router(health.public_router, tags=["health"])
    app.include_router(list_routes.debug_router, tags=["debug"])
    return app


app = create_app()

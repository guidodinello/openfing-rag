from fastapi import FastAPI

from generator.api.router import api_router as generator_router
from scraper.api.router import api_router as scraper_router
from shared.config import get_settings
from shared.middleware import setup_middlewares
from transcriber.api.router import api_router as transcriber_router

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP.NAME,
        description=settings.APP.DESCRIPTION,
        version=settings.APP.VERSION,
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
        app.include_router(service_router, prefix=settings.API_V1_URL)
    return app


app = create_app()

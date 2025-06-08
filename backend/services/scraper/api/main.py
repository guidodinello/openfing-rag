from fastapi import FastAPI

from scraper.api.router import api_router
from shared.config.config import get_settings
from shared.middleware import setup_middlewares

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Scraper Service",
        description="API for scraping courses and lessons from OpenFIng",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    setup_middlewares(app)

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


app = create_app()

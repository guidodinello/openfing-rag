from fastapi import FastAPI

from generator.api.router import api_router
from shared.config.config import get_settings
from shared.middleware import setup_middlewares

settings = get_settings()


def create_app() -> FastAPI:
    """Factory pattern for creating FastAPI app with all configurations"""
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
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

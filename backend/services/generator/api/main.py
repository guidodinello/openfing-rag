from fastapi import FastAPI

from generator.api.router import api_router
from shared.config.config import get_settings
from shared.middleware import setup_middlewares

settings = get_settings()


def create_app() -> FastAPI:
    """Factory pattern for creating FastAPI app with all configurations"""
    service_base_url = f"{settings.API_V1_STR}/generator"

    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        openapi_url=f"{service_base_url}/openapi.json",
        docs_url=f"{service_base_url}/docs",
        redoc_url=f"{service_base_url}/redoc",
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    setup_middlewares(app)

    app.include_router(api_router, prefix=service_base_url)
    return app


app = create_app()

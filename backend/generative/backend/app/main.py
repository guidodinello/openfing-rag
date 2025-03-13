from app.api.middleware import setup_middlewares
from app.api.router import api_router
from app.core.config import get_settings
from fastapi import FastAPI

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

    # # Database initialization if needed
    # # TODO: maybe create here and pass dependency. maybe not needed as we have singleton modules
    # @app.on_event("startup")
    # async def init_db():
    #     # Add your database initialization here if needed
    #     pass

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app


app = create_app()

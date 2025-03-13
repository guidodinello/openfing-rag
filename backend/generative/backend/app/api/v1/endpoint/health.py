from app.core.config import get_settings
from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

settings = get_settings()


@router.get(
    "",
    summary="Health Check",
    description="Returns the health status of the API and its environment",
    response_description="Health status information",
)
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production",
    }

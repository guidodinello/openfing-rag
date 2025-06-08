from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from shared.config.config import get_settings

settings = get_settings()

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable"},
    },
)


class HealthStatus(BaseModel):
    service: str
    version: str
    environment: str
    timestamp: str


@router.get(
    "",
    summary="Health check",
    description="Returns the health status of the scraper service and its dependencies",
)
async def health_check() -> HealthStatus:
    return HealthStatus(
        service="scraper",
        version="1.0.0",
        environment="development" if settings.DEBUG else "production",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

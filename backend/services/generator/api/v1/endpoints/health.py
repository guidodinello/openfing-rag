from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from shared.config import get_settings

settings = get_settings()

public_router = APIRouter()


class HealthStatus(BaseModel):
    service: str
    version: str
    environment: str
    timestamp: str


@public_router.get(
    settings.HEALTH_URL,
    summary="Health check",
    description="Returns the health status of the generator service",
)
async def health_check():
    return HealthStatus(
        service="generator",
        version=settings.APP.VERSION,
        environment=settings.APP.ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

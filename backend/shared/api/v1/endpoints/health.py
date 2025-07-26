from datetime import datetime, timezone

from fastapi import status
from pydantic import BaseModel

from shared.api.router import AuthRouters
from shared.config import get_settings

settings = get_settings()

routers = AuthRouters.create()


class HealthStatus(BaseModel):
    service: str
    version: str
    environment: str
    timestamp: str


@routers.public.get(settings.HEALTH_URL, summary="Health check", status_code=status.HTTP_200_OK)
async def health_check() -> HealthStatus:
    return HealthStatus(
        service=settings.APP.NAME,
        version=settings.APP.VERSION,
        environment=settings.APP.ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

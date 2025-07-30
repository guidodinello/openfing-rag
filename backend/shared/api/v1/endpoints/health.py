from datetime import datetime, timezone

from fastapi import status
from pydantic import BaseModel

from shared.api.router import AuthRouters
from shared.api.v1.schemas import ApiResponse
from shared.config import get_settings

settings = get_settings()

routers = AuthRouters.create()


class HealthStatus(BaseModel):
    service: str
    version: str
    environment: str
    timestamp: str


class HealthStatusResponse(ApiResponse[HealthStatus]): ...


@routers.public.get(settings.HEALTH_URL, summary="Health check", status_code=status.HTTP_200_OK)
async def health_check() -> HealthStatusResponse:
    return HealthStatusResponse.success_response(
        message="Healthy",
        data=HealthStatus(
            service=settings.APP.NAME,
            version=settings.APP.VERSION,
            environment=settings.APP.ENV,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )

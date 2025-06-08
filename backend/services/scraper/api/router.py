from fastapi import APIRouter

from .v1.endpoints import health, scraping

api_router = APIRouter()

api_router.include_router(scraping.router, tags=["scraping"])
api_router.include_router(health.router, tags=["health"])

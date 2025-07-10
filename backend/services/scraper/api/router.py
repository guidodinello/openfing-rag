from fastapi import APIRouter

from .v1.endpoints import health, scraping

api_router = APIRouter(prefix="/scraper", tags=["scraper"])

api_router.include_router(scraping.admin_router)
api_router.include_router(scraping.read_router)
api_router.include_router(scraping.write_router)
api_router.include_router(health.public_router, tags=["health"])

from fastapi import APIRouter

from services.scraper.api.v1.endpoints import scraping

scraper_router = APIRouter(prefix="/scraper", tags=["scraper"])

scraping.routers.include_in(scraper_router)

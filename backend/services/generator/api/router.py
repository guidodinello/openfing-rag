from fastapi import APIRouter

from generator.api.v1.endpoints import chat, health

api_router = APIRouter(prefix="/generator", tags=["generator"])

api_router.include_router(chat.read_router)
api_router.include_router(health.public_router, tags=["health"])

from app.api.v1.endpoint import chat, health
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(health.router, tags=["health"])

from fastapi import APIRouter

from services.generator.api.v1.endpoints import chat

generator_router = APIRouter(prefix="/generator", tags=["generator"])

chat.routers.include_in(generator_router)

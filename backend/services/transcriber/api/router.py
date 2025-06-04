from fastapi import APIRouter

from transcriber.api.v1.endpoints import health, transcription

api_router = APIRouter()

api_router.include_router(transcription.router, tags=["transcription"])
api_router.include_router(health.router, tags=["health"])

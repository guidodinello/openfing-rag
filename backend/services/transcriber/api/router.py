from fastapi import APIRouter

from transcriber.api.v1.endpoints import health, transcription

api_router = APIRouter(prefix="/transcriber", tags=["transcriber"])

api_router.include_router(transcription.admin_router)
api_router.include_router(transcription.read_router)
api_router.include_router(transcription.write_router)
api_router.include_router(health.public_router, tags=["health"])

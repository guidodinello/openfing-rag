from fastapi import APIRouter

from services.transcriber.api.v1.endpoints import transcription

transcriber_router = APIRouter(prefix="/transcriber", tags=["transcriber"])

transcription.routers.include_in(transcriber_router)

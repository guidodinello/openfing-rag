from fastapi import APIRouter

from shared.database.api.v1.endpoints import courses, transcriptions

crud_router = APIRouter(tags=["CRUD"])

courses.routers.include_in(crud_router)
transcriptions.routers.include_in(crud_router)

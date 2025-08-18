from fastapi import APIRouter

from shared.database.api.v1.endpoints import conversations, courses, transcriptions, users

crud_router = APIRouter(tags=["CRUD"])

conversations.routers.include_in(crud_router)
courses.routers.include_in(crud_router)
transcriptions.routers.include_in(crud_router)
users.routers.include_in(crud_router)

from fastapi import APIRouter, Depends, FastAPI
from pydantic import BaseModel

from shared.auth.api_key import require_admin_permission

debug_router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    dependencies=[Depends(require_admin_permission)],
)


class RouteModel(BaseModel):
    path: str
    methods: list[str]
    name: str
    tags: list | str


class MountModel(BaseModel):
    path: str
    type: str


class RoutesResponse(BaseModel):
    routes: list[RouteModel | MountModel]


def get_app() -> FastAPI:
    from api import app

    return app


@debug_router.get("/routes")
async def list_routes(app: FastAPI = Depends(get_app)) -> RoutesResponse:
    routes = []
    for route in app.routes:
        if hasattr(route, "methods"):
            routes.append(
                RouteModel(
                    path=route.path,
                    methods=list(route.methods),
                    name=getattr(route, "name", "unnamed"),
                    tags=getattr(route, "tags", "unnamed"),
                ),
            )
        else:
            routes.append(MountModel(path=route.path, type="mount"))

    return RoutesResponse(routes=routes)

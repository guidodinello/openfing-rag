from collections.abc import Iterator
from dataclasses import dataclass

from fastapi import APIRouter, Depends

from shared.auth.api_key import (
    require_admin_permission,
    require_read_permission,
    require_write_permission,
)


@dataclass(frozen=True, slots=True)
class AuthRouters:
    admin: APIRouter
    read: APIRouter
    write: APIRouter
    public: APIRouter

    def __iter__(self) -> Iterator[APIRouter]:
        return iter([self.admin, self.read, self.write, self.public])

    def include_in(self, parent_router: APIRouter) -> None:
        for router in self:
            parent_router.include_router(router)


def create_auth_routers(**kwargs) -> AuthRouters:
    return AuthRouters(
        admin=APIRouter(dependencies=[Depends(require_admin_permission)], **kwargs),
        read=APIRouter(dependencies=[Depends(require_read_permission)], **kwargs),
        write=APIRouter(dependencies=[Depends(require_write_permission)], **kwargs),
        public=APIRouter(**kwargs),
    )

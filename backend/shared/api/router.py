from collections.abc import Iterator
from dataclasses import dataclass
from typing import Self

from fastapi import APIRouter, Depends

from shared.auth.api_key import require_admin_permission, require_read_permission, require_write_permission
from shared.auth.mixed_auth import require_api_key_or_jwt_read, require_api_key_or_jwt_write
from shared.auth.oauth2_password_bearer import require_jwt_user


@dataclass(frozen=True, slots=True)
class ApiKeyAuthedRouters:
    admin: APIRouter
    read: APIRouter
    write: APIRouter

    def __iter__(self) -> Iterator[APIRouter]:
        return iter([self.admin, self.read, self.write])


@dataclass(frozen=True, slots=True)
class JwtAuthedRouters:
    bearer: APIRouter

    def __iter__(self) -> Iterator[APIRouter]:
        return iter([self.bearer])


@dataclass(frozen=True, slots=True)
class MixedAuthedRouters:
    api_key_or_jwt_read: APIRouter
    api_key_or_jwt_write: APIRouter

    def __iter__(self) -> Iterator[APIRouter]:
        return iter([self.api_key_or_jwt_read, self.api_key_or_jwt_write])


@dataclass(frozen=True, slots=True)
class AuthRouters:
    api_key: ApiKeyAuthedRouters
    jwt: JwtAuthedRouters
    mixed: MixedAuthedRouters
    public: APIRouter

    def __iter__(self) -> Iterator[APIRouter]:
        yield from self.api_key
        yield from self.jwt
        yield from self.mixed
        yield self.public

    def include_in(self, parent_router: APIRouter) -> APIRouter:
        for router in self:
            parent_router.include_router(router)
        return parent_router

    @classmethod
    def create(cls, **kwargs) -> Self:
        """Factory method to create all routers with dependencies"""
        return cls(
            api_key=ApiKeyAuthedRouters(
                admin=APIRouter(dependencies=[Depends(require_admin_permission)], **kwargs),
                read=APIRouter(dependencies=[Depends(require_read_permission)], **kwargs),
                write=APIRouter(dependencies=[Depends(require_write_permission)], **kwargs),
            ),
            jwt=JwtAuthedRouters(
                bearer=APIRouter(dependencies=[Depends(require_jwt_user)], **kwargs),
            ),
            mixed=MixedAuthedRouters(
                api_key_or_jwt_read=APIRouter(dependencies=[Depends(require_api_key_or_jwt_read)], **kwargs),
                api_key_or_jwt_write=APIRouter(dependencies=[Depends(require_api_key_or_jwt_write)], **kwargs),
            ),
            public=APIRouter(**kwargs),
        )

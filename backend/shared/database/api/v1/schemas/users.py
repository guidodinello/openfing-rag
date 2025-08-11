from typing import Self

from pydantic import BaseModel

from shared.api.v1.schemas import ApiResponse
from shared.database.models import User as UseModel


class User(BaseModel):
    id: int
    email: str
    username: str

    @classmethod
    def from_model(cls, user: UseModel) -> Self:
        return cls(id=user.id, email=user.email, username=user.username)


class UserResponse(ApiResponse[User]): ...

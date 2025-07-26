# Schemas
from typing import Self

from pydantic import BaseModel, EmailStr

from shared.api.v1.schemas import ApiResponse
from shared.database.models import User as UseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class User(BaseModel):
    id: int
    email: str
    username: str

    @classmethod
    def from_model(cls, user: UseModel) -> Self:
        return cls(id=user.id, email=user.email, username=user.username)


class UserResponse(ApiResponse[User]): ...

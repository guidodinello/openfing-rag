from typing import Generic, Self, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Human-readable message")
    data: T | None = Field(default=None, description="Response data")

    @classmethod
    def success_response(cls, message: str, data: T) -> Self:
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(cls, message: str, data: None = None) -> Self:
        return cls(success=False, message=message, data=data)


class ApiListResponse(BaseModel, Generic[T]):
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Human-readable message")
    data: list[T] = Field(default_factory=list, description="List of items")
    total: int = Field(description="Total number of items")

    @classmethod
    def success_response(cls, message: str, data: list[T], total: int | None = None) -> Self:
        calculated_total = total if total is not None else len(data)
        return cls(success=True, message=message, data=data, total=calculated_total)

    @classmethod
    def error_response(cls, message: str, data: list[T] | None = None) -> Self:
        items = data if data is not None else []
        return cls(success=False, message=message, data=items, total=0)

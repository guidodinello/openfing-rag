from dataclasses import dataclass
from typing import Generic, Iterable, Self, TypeVar

# Generic type variable for the result data
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    """Result class for service operations."""

    success: bool
    message: str
    item: T | None = None

    @classmethod
    def success_result(cls, message: str, item: T | None = None) -> Self:
        return cls(success=True, message=message, item=item)

    @classmethod
    def failure_result(cls, message: str, item: T | None = None) -> Self:
        return cls(success=False, message=message, item=item)


@dataclass(frozen=True, slots=True)
class ListResult(Generic[T]):
    """Rsult for list operations with metadata."""

    success: bool
    message: str
    items: Iterable[T]

    @classmethod
    def success_result(cls, message: str, items: Iterable[T]) -> Self:
        return cls(success=True, message=message, items=items)

    @classmethod
    def failure_result(cls, message: str, items: Iterable[T] = []) -> Self:
        # TODO: [] is that bad here?
        return cls(success=False, message=message, items=items)

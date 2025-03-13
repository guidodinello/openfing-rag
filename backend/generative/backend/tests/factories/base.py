# app/database/factories/base.py
from typing import Any, Generic, Type, TypeVar

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseFactory(Generic[ModelType]):
    """Base factory class for generating test data."""

    # TODO: update type
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
        self.faker = Faker()

    async def create(self, **kwargs: dict[str, Any]) -> ModelType:
        """Create a single instance with override values."""
        attrs = {**self.get_default_attributes(), **kwargs}
        instance = self.model(**attrs)
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def create_batch(self, count: int, **kwargs) -> list[ModelType]:
        """Create multiple instances with override values."""
        instances = []
        for _ in range(count):
            instance = await self.create(**kwargs)
            instances.append(instance)
        return instances

    def get_default_attributes(self) -> dict[str, Any]:
        """Override this method to provide default attributes."""
        raise NotImplementedError

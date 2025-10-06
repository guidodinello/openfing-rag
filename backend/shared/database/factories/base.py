from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from faker import Faker
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseFactory(ABC, Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db
        self.faker = Faker()

    def create(self, **kwargs: dict[str, Any]) -> ModelType:
        """Create a single instance with override values."""
        attrs = {**self.get_default_attributes(), **kwargs}
        instance = self.model(**attrs)
        self.db.add(instance)
        self.db.flush()  # Sync version
        self.db.refresh(instance)
        return instance

    def create_batch(self, count: int, **kwargs) -> list[ModelType]:
        """Create multiple instances with override values."""
        return [self.create(**kwargs) for _ in range(count)]

    def build(self, **kwargs: dict[str, Any]) -> ModelType:
        """Build instance without saving to database."""
        return self.model(**self.get_default_attributes(), **kwargs)

    def build_batch(self, count: int, **kwargs) -> list[ModelType]:
        """Build multiple instances without saving."""
        return [self.build(**kwargs) for _ in range(count)]

    @abstractmethod
    def get_default_attributes(self) -> dict[str, Any]:
        """Override this method to provide default attributes."""
        ...

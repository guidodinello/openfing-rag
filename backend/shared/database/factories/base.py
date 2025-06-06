from typing import Any, Generic, TypeVar

from faker import Faker
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseFactory(Generic[ModelType]):
    """Base factory class for generating test data using sync pattern."""

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
        instances = []
        for _ in range(count):
            instance = self.create(**kwargs)
            instances.append(instance)
        return instances

    def get_default_attributes(self) -> dict[str, Any]:
        """Override this method to provide default attributes."""
        raise NotImplementedError

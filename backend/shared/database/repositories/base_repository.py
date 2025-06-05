from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: type[T], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> T | None:
        return self.db.get(self.model, id)

    def get_by(self, **criteria) -> T | None:
        """Get single record by criteria."""
        conditions = [getattr(self.model, key) == value for key, value in criteria.items()]
        return self.db.execute(select(self.model).where(*conditions)).scalar_one_or_none()

    def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Get all records with pagination."""
        return self.db.execute(select(self.model).limit(limit).offset(offset)).scalars().all()

    def create(self, **data) -> T:
        """Create new record."""
        instance = self.model(**data)
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def update_or_create(self, defaults: dict[str, Any], **criteria) -> tuple[T, bool]:
        """
        Update existing record or create new one.
        Returns (instance, created_flag)
        """
        instance = self.get_by(**criteria)

        if instance:
            # Update existing
            for key, value in defaults.items():
                if hasattr(instance, key):
                    # Handle metadata fields specially
                    if key.endswith("_metadata") and hasattr(instance, key):
                        existing_metadata = getattr(instance, key) or {}
                        new_metadata = value or {}
                        setattr(instance, key, {**existing_metadata, **new_metadata})
                    else:
                        setattr(instance, key, value)
            self.db.flush()
            self.db.refresh(instance)
            return instance, False
        else:
            # Create new
            instance_data = {**criteria, **defaults}
            return self.create(**instance_data), True

    def delete(self, instance: T) -> None:
        """Delete record."""
        self.db.delete(instance)
        self.db.flush()

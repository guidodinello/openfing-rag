from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models"""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    def as_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TimestampedModel(Base):
    """Base model with timestamp fields."""

    __abstract__ = True

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

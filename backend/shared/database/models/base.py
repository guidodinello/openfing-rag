from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models"""

    __abstract__ = True

    def as_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        """Generic repr showing ClassName(attr1=value1, attr2=value2)"""
        table = self.__table__

        attrs = []
        for column in table.columns:
            value = getattr(self, column.name, None)
            attrs.append(f"{column.name}={value!r}")

        attrs_str = " ".join(attrs)

        return f"{self.__class__.__name__}({attrs_str})"

    def __str__(self) -> str:
        return self.__repr__()


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

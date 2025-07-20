from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declared_attr

from shared.database.models import TimestampedModel


class User(TimestampedModel):
    """User model for authentication and authorization."""

    @declared_attr
    def __tablename__(cls) -> str:
        return "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    def __repr__(self):
        return f"User({self.id=} {self.username=} {self.email=})"

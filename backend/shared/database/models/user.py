from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declared_attr

from shared.database.models.base import TimestampedModel


class User(TimestampedModel):
    """User model for authentication and authorization."""

    @declared_attr
    def __tablename__(cls) -> str:
        return "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

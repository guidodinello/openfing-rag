from datetime import datetime, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, Self

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, relationship

from shared.database.models import TimestampedModel

if TYPE_CHECKING:
    from shared.database.models import User


class ApiKeyScope(StrEnum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

    def has_permission_level_of(self, other: Self) -> bool:
        hierarchy = {
            ApiKeyScope.READ: 1,
            ApiKeyScope.WRITE: 2,
            ApiKeyScope.ADMIN: 3,
        }
        return hierarchy[self] >= hierarchy[other]


class ApiKey(TimestampedModel):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_api_keys_user_id", "user_id"),
        Index("idx_api_keys_key_hash", "key_hash", unique=True),
        {
            "extend_existing": True,
            "comment": "API keys for user authentication",
        },
    )

    id: Mapped[int] = Column(Integer, primary_key=True)

    user_id: Mapped[int] = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="User who owns this API key",
    )

    name: Mapped[str] = Column(
        String(100),
        nullable=False,
        comment="Human-readable name for the API key",
    )

    key_hash: Mapped[str] = Column(
        String(256),
        nullable=False,
        unique=True,
        comment="Hashed version of the API key",
    )

    scope: Mapped[ApiKeyScope] = Column(
        Enum(
            ApiKeyScope,
            native_enum=False,
            length=32,
            validate_strings=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ApiKeyScope.READ,
        comment="Permission scope for this API key",
    )

    last_used_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this API key was used",
    )

    expires_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this API key expires (NULL = never)",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys",
    )

    @property
    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_expired

    def has_permission(self, required_scope: ApiKeyScope) -> bool:
        """Check if this API key has the required permission level."""
        return self.scope.has_permission_level_of(required_scope)

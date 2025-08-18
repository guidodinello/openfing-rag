"""create_api_keys_table

Revision ID: bd49a3e0fa26
Revises: 2bb7effc5d5c
Create Date: 2025-07-28 05:12:45.644362+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from shared.database.migrations.helpers import (
    add_id_column,
    add_timestamp_trigger,
    add_timestamps,
    create_btree_index,
    drop_btree_index,
    drop_timestamp_trigger,
)
from shared.database.models.api_key import ApiKeyScope

revision: str = "bd49a3e0fa26"
down_revision: str | None = "2bb7effc5d5c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        add_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="User who owns this API key",
        ),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
            comment="Human-readable name for the API key",
        ),
        sa.Column(
            "key_hash",
            sa.String(256),
            nullable=False,
            unique=True,
            comment="Hashed version of the API key",
        ),
        sa.Column(
            "scope",
            sa.String(32),
            nullable=False,
            server_default="read",
            comment="Permission scope for this API key",
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last time this API key was used",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When this API key expires (NULL = never)",
        ),
        *add_timestamps(),
        comment="API keys for user authentication",
    )

    # Create indexes
    create_btree_index("api_keys", ["user_id"])
    create_btree_index("api_keys", ["key_hash"], unique=True)

    # Add check constraints
    scopes = "', '".join([role.value for role in ApiKeyScope])
    op.create_check_constraint(
        "ck_api_keys_scope",
        "api_keys",
        sa.text(f"scope IN ('{scopes}')"),
    )

    # Add timestamp trigger
    add_timestamp_trigger("api_keys")


def downgrade() -> None:
    # Drop trigger
    drop_timestamp_trigger("api_keys")

    # Drop constraints
    op.drop_constraint("ck_api_keys_scope", "api_keys")

    # Drop indexes
    drop_btree_index("api_keys", ["key_hash"])
    drop_btree_index("api_keys", ["user_id"])

    # Drop table
    op.drop_table("api_keys")

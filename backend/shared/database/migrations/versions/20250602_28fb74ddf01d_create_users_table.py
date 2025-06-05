"""create_users_table

Revision ID: 28fb74ddf01d
Revises: 001_initial
Create Date: 2025-06-02 04:41:34.639951+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from shared.database.migrations.helpers import (
    add_id_column,
    add_timestamp_trigger,
    add_timestamps,
    create_btree_index,
    create_gin_index,
    drop_btree_index,
    drop_gin_index,
    drop_timestamp_trigger,
)

revision: str = "28fb74ddf01d"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        add_id_column(),
        sa.Column(
            "email",
            sa.String(),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column(
            "username",
            sa.String(50),
            unique=True,
            nullable=False,
        ),
        sa.Column("hashed_password", sa.String(), nullable=False, comment="Bcrypt hashed password"),
        *add_timestamps(),
        comment="User accounts for authentication and authorization",
    )

    # Create chat_history table for conversation history
    op.create_table(
        "chat_history",
        add_id_column(),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("message", postgresql.JSONB, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,  # Allow anonymous sessions for now
            comment="Reference to the user (nullable for anonymous chats)",
        ),
        *add_timestamps(),
        schema="public",
        comment="Chat message history for conversations",
    )

    create_btree_index("users", ["email"], unique=True)
    create_btree_index("users", ["username"], unique=True)

    create_btree_index("chat_history", ["session_id"])
    create_btree_index("chat_history", ["user_id"])
    create_gin_index("chat_history", "message")

    add_timestamp_trigger("users")
    add_timestamp_trigger("chat_history")


def downgrade() -> None:
    drop_timestamp_trigger("users")
    drop_timestamp_trigger("chat_history")

    drop_gin_index("chat_history", "message")
    drop_btree_index("chat_history", ["user_id"])
    drop_btree_index("chat_history", ["session_id"])

    drop_btree_index("users", ["username"])
    drop_btree_index("users", ["email"])

    op.drop_table("chat_history")
    op.drop_table("users")

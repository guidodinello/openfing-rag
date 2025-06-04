"""create_users_table

Revision ID: 28fb74ddf01d
Revises: 001_initial
Create Date: 2025-06-02 04:41:34.639951+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "28fb74ddf01d"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, comment="Unique identifier for the user"),
        sa.Column(
            "email",
            sa.String(),
            unique=True,
            nullable=False,
            index=True,
            comment="User's email address (unique)",
        ),
        sa.Column(
            "username",
            sa.String(50),
            unique=True,
            nullable=False,
            comment="User's username (unique, max 50 chars)",
        ),
        sa.Column("hashed_password", sa.String(), nullable=False, comment="Bcrypt hashed password"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            default=True,
            nullable=False,
            comment="Whether the user account is active",
        ),
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            default=False,
            nullable=False,
            comment="Whether the user has admin privileges",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Timestamp when the user was created",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Timestamp when the user was last updated",
        ),
        comment="User accounts for authentication and authorization",
    )

    # Create chat_history table for conversation history
    op.create_table(
        "chat_history",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("message", postgresql.JSONB, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,  # Allow anonymous sessions for now
            comment="Reference to the user (nullable for anonymous chats)",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema="public",
        comment="Chat message history for conversations",
    )

    op.create_index("idx_chat_history_session_id", "chat_history", ["session_id"], postgresql_using="btree")
    op.create_index("idx_chat_history_user_id", "chat_history", ["user_id"], postgresql_using="btree")
    op.create_index("idx_chat_history_message", "chat_history", ["message"], postgresql_using="gin")

    op.create_index("idx_users_email", "users", ["email"], unique=True, postgresql_using="btree")
    op.create_index("idx_users_username", "users", ["username"], unique=True, postgresql_using="btree")

    op.execute(
        """
        CREATE TRIGGER update_users_timestamp
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
        """,
    )

    op.execute(
        """
        CREATE TRIGGER users_change_notify
        AFTER INSERT OR UPDATE OR DELETE ON users
        FOR EACH ROW EXECUTE FUNCTION notify_record_change();
        """,
    )


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_users_timestamp ON users")
    op.execute("DROP TRIGGER IF EXISTS users_change_notify ON users")

    op.drop_index("idx_chat_history_message", table_name="chat_history")
    op.drop_index("idx_chat_history_user_id", table_name="chat_history")
    op.drop_index("idx_chat_history_session_id", table_name="chat_history")

    op.drop_index("idx_users_username", table_name="users")
    op.drop_index("idx_users_email", table_name="users")

    op.drop_table("chat_history")
    op.drop_table("users")

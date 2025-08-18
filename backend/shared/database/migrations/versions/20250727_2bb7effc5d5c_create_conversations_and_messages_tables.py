"""create_conversations_and_messages_tables

Revision ID: 2bb7effc5d5c
Revises: 28fb74ddf01d
Create Date: 2025-07-27 23:30:21.563016+00:00

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
from shared.database.models.rag.conversations import MessageRole

revision: str = "2bb7effc5d5c"
down_revision: str | None = "28fb74ddf01d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create conversations table
    op.create_table(
        "conversations",
        add_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="User who owns this conversation",
        ),
        sa.Column(
            "title",
            sa.String(255),
            nullable=True,
            comment="Optional conversation title (auto-generated or user-defined)",
        ),
        *add_timestamps(),
        comment="User conversations for chat history",
    )

    # Create messages table
    roles = "', '".join([role.value for role in MessageRole])
    op.create_table(
        "messages",
        add_id_column(),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            comment="Conversation this message belongs to",
        ),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            comment=f"MessageRole enum values: {roles}",
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
            comment="Message content",
        ),
        sa.Column(
            "message_order",
            sa.Integer(),
            nullable=False,
            comment="Order of message in conversation (for proper sequencing)",
        ),
        *add_timestamps(),
        comment="Individual messages within conversations",
    )

    # Create message_sources table
    op.create_table(
        "message_sources",
        add_id_column(),
        sa.Column(
            "message_id",
            sa.Integer(),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
            comment="Message that used this source",
        ),
        sa.Column(
            "chunk_id",
            sa.UUID,
            nullable=False,
            comment="ID of the chunk that was used as source",
        ),
        sa.Column(
            "confidence_score",
            sa.Float(),
            nullable=False,
            comment="Similarity score for this chunk",
        ),
        sa.Column(
            "source_order",
            sa.Integer(),
            nullable=False,
            comment="Order of this source in the response (for ranking)",
        ),
        *add_timestamps(),
        comment="Relationship between messages and the chunks used as sources",
    )

    # Create indexes for conversations
    create_btree_index("conversations", ["user_id"])
    create_btree_index("conversations", ["user_id", "created_at"])

    # Create indexes for messages
    create_btree_index("messages", ["conversation_id"])
    create_btree_index("messages", ["conversation_id", "message_order"])
    create_btree_index("messages", ["role"])

    # Create indexes for message_sources
    create_btree_index("message_sources", ["message_id"])
    create_btree_index("message_sources", ["chunk_id"])
    create_btree_index("message_sources", ["message_id", "source_order"])
    create_btree_index("message_sources", ["confidence_score"])

    # Add unique constraint for message ordering within conversation
    op.create_unique_constraint(
        "uq_messages_order",  # Cambio de nombre
        "messages",
        ["conversation_id", "message_order"],
    )

    # Add unique constraint for source ordering within message
    op.create_unique_constraint(
        "uq_message_sources_order",
        "message_sources",
        ["message_id", "source_order"],
    )

    # Add check constraints
    op.create_check_constraint(
        "ck_messages_role",
        "messages",
        sa.text(f"role IN ('{roles}')"),
    )

    # Add timestamp triggers
    add_timestamp_trigger("conversations")
    add_timestamp_trigger("messages")
    add_timestamp_trigger("message_sources")


def downgrade() -> None:
    # Drop triggers
    drop_timestamp_trigger("message_sources")
    drop_timestamp_trigger("messages")
    drop_timestamp_trigger("conversations")

    # Drop constraints
    op.drop_constraint("ck_messages_role", "messages")
    op.drop_constraint("uq_message_sources_order", "message_sources", type_="unique")
    op.drop_constraint("uq_messages_order", "messages", type_="unique")

    # Drop indexes
    drop_btree_index("message_sources", ["confidence_score"])
    drop_btree_index("message_sources", ["message_id", "source_order"])
    drop_btree_index("message_sources", ["chunk_id"])
    drop_btree_index("message_sources", ["message_id"])

    drop_btree_index("messages", ["role"])
    drop_btree_index("messages", ["conversation_id", "message_order"])
    drop_btree_index("messages", ["conversation_id"])

    drop_btree_index("conversations", ["user_id", "created_at"])
    drop_btree_index("conversations", ["user_id"])

    # Drop tables
    op.drop_table("message_sources")
    op.drop_table("messages")
    op.drop_table("conversations")

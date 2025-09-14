"""remove_message_source_ordering

Revision ID: 6bf2ba541238
Revises: bd49a3e0fa26
Create Date: 2025-09-14 05:47:47.408713+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from shared.database.migrations.helpers import create_btree_index, drop_btree_index

revision: str = "6bf2ba541238"
down_revision: str | None = "bd49a3e0fa26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop constraints first
    op.drop_constraint("uq_message_sources_order", "message_sources", type_="unique")
    drop_btree_index("message_sources", ["message_id", "source_order"])

    # Remove the column
    op.drop_column("message_sources", "source_order")


def downgrade() -> None:
    # Add the column back
    op.add_column("message_sources", sa.Column("source_order", sa.Integer(), nullable=False))

    # Recreate constraints
    create_btree_index("message_sources", ["message_id", "source_order"])
    op.create_unique_constraint("uq_message_sources_order", "message_sources", ["message_id", "source_order"])

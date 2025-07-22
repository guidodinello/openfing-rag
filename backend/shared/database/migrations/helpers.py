from collections.abc import Iterable

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def add_timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )


def setup_timestamp_triggers() -> None:
    """Create the timestamp update function and triggers for all tables."""
    # Create the function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """,
    )


def add_timestamp_trigger(table_name: str, schema: str | None = None) -> None:
    """Add timestamp trigger to a specific table."""
    table_ref = f"{schema}.{table_name}" if schema else table_name
    op.execute(
        f"""
        CREATE TRIGGER update_{table_name}_timestamp
        BEFORE UPDATE ON {table_ref}
        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    """,
    )


def add_id_column() -> sa.Column:
    """Add standard auto-incrementing ID column."""
    return sa.Column(
        "id",
        sa.Integer(),
        sa.Identity(always=True),
        primary_key=True,
    )


def add_jsonb_metadata_column(column_name: str) -> sa.Column:
    """Add a JSONB metadata column with standard defaults."""
    return sa.Column(
        column_name,
        postgresql.JSONB(none_as_null=True),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )


def create_gin_index(
    table_name: str,
    column_name: str,
    schema: str | None = None,
) -> None:
    """Create a GIN index for JSONB columns."""
    op.create_index(
        f"idx_{table_name}_{column_name}",
        table_name,
        [column_name],
        unique=False,
        schema=schema,
        postgresql_using="gin",
    )


def create_btree_index(
    table_name: str,
    columns: Iterable[str],
    schema: str | None = None,
    unique: bool = False,
) -> None:
    """Create a B-tree index."""
    index_name = f"idx_{table_name}_{'_'.join(columns)}"
    op.create_index(
        index_name,
        table_name,
        columns,
        unique=unique,
        schema=schema,
        postgresql_using="btree",
    )


def drop_btree_index(
    table_name: str,
    columns: Iterable[str],
    schema: str | None = None,
) -> None:
    """Drop a B-tree index (matching the create_btree_index naming)."""
    index_name = f"idx_{table_name}_{'_'.join(columns)}"
    op.drop_index(index_name, table_name=table_name, schema=schema)


def drop_gin_index(
    table_name: str,
    column_name: str,
    schema: str | None = None,
) -> None:
    """Drop a GIN index (matching the create_gin_index naming)."""
    op.drop_index(
        f"idx_{table_name}_{column_name}",
        table_name=table_name,
        schema=schema,
    )


def drop_timestamp_trigger(table_name: str, schema: str | None = None) -> None:
    """Drop timestamp trigger from a specific table."""
    table_ref = f"{schema}.{table_name}" if schema else table_name
    op.execute(f"DROP TRIGGER IF EXISTS update_{table_name}_timestamp ON {table_ref}")


def cleanup_timestamp_triggers() -> None:
    """Drop the timestamp update function."""
    op.execute("DROP FUNCTION IF EXISTS update_timestamp()")

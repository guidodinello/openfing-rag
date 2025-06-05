"""initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2025-06-20 12:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from shared.config.config import get_settings
from shared.database.migrations.helpers import (
    add_id_column,
    add_jsonb_metadata_column,
    add_timestamp_trigger,
    add_timestamps,
    cleanup_timestamp_triggers,
    create_btree_index,
    create_gin_index,
    drop_btree_index,
    drop_gin_index,
    drop_timestamp_trigger,
    setup_timestamp_triggers,
)

settings = get_settings()

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create required extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    op.execute("CREATE SCHEMA IF NOT EXISTS rag")

    setup_timestamp_triggers()

    ## COURSES
    op.create_table(
        "courses",
        add_id_column(),
        sa.Column("code", sa.String(49), nullable=False, unique=True),
        sa.Column("name", sa.String(254), nullable=False),
        sa.Column("subtitle", sa.String(254), nullable=True),
        add_jsonb_metadata_column("course_metadata"),
        *add_timestamps(),
        schema="rag",
    )

    ## LESSONS
    op.create_table(
        "lessons",
        add_id_column(),
        sa.Column("title", sa.String(254), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("video_url", sa.String(254), nullable=True),
        add_jsonb_metadata_column("lesson_metadata"),
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("rag.courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *add_timestamps(),
        schema="rag",
    )

    # Unique constraints for LESSON WITHIN COURSE
    op.create_unique_constraint(
        "uq_lessons_course_title",
        "lessons",
        ["course_id", "title"],
        schema="rag",
    )
    op.create_unique_constraint(
        "uq_lessons_course_number",
        "lessons",
        ["course_id", "number"],
        schema="rag",
    )

    ## TRANSCRIPTIONS
    op.create_table(
        "transcriptions",
        add_id_column(),
        sa.Column("content", sa.Text(), nullable=False),
        add_jsonb_metadata_column("transcription_metadata"),
        sa.Column(
            "lesson_id",
            sa.Integer(),
            sa.ForeignKey("rag.lessons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *add_timestamps(),
        schema="rag",
    )

    create_btree_index("courses", ["code"], schema="rag")
    create_btree_index("lessons", ["course_id"], schema="rag")
    create_btree_index("lessons", ["course_id", "number"], schema="rag")
    create_btree_index("transcriptions", ["lesson_id"], schema="rag")

    # GIN indexes for JSONB columns
    for table, column in [
        ("courses", "course_metadata"),
        ("lessons", "lesson_metadata"),
        ("transcriptions", "transcription_metadata"),
    ]:
        create_gin_index(table, column, schema="rag")

    for table in ["courses", "lessons", "transcriptions"]:
        add_timestamp_trigger(table, schema="rag")


def downgrade() -> None:
    # Drop triggers
    for table in ["courses", "lessons", "transcriptions"]:
        drop_timestamp_trigger(table, schema="rag")

    # Drop functions
    cleanup_timestamp_triggers()

    # Drop indexes
    for table, column in [
        ("transcriptions", "transcription_metadata"),
        ("lessons", "lesson_metadata"),
        ("courses", "course_metadata"),
    ]:
        drop_gin_index(table, column, schema="rag")

    drop_btree_index("transcriptions", ["lesson_id"], schema="rag")
    drop_btree_index("lessons", ["course_id", "number"], schema="rag")
    drop_btree_index("lessons", ["course_id"], schema="rag")
    drop_btree_index("courses", ["code"], schema="rag")

    # Drop unique constraints
    op.drop_constraint("uq_lessons_course_number", "lessons", schema="rag", type_="unique")
    op.drop_constraint("uq_lessons_course_title", "lessons", schema="rag", type_="unique")

    # Drop tables
    for table in ["transcriptions", "lessons", "courses"]:
        op.drop_table(table, schema="rag")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS rag CASCADE")

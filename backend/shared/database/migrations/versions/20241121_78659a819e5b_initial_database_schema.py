"""initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2025-06-20 12:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from shared.config.config import get_settings

settings = get_settings()

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create required extensions - we'll still need these
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS rag")

    # Create courses table
    op.create_table(
        "courses",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column("code", sa.String(49), nullable=False, unique=True),
        sa.Column("name", sa.String(254), nullable=False),
        sa.Column(
            "course_metadata",
            postgresql.JSONB(none_as_null=True),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
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
        schema="rag",
        comment="Educational courses containing lessons",
    )

    # Create lessons table
    op.create_table(
        "lessons",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column("title", sa.String(254), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("video_url", sa.String(254)),
        sa.Column(
            "lesson_metadata",
            postgresql.JSONB(none_as_null=True),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
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
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("rag.courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        schema="rag",
        comment="Lessons within courses containing video content",
    )

    # Create unique constraint for lesson title within course
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

    # Create transcriptions table
    op.create_table(
        "transcriptions",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "transcription_metadata",
            postgresql.JSONB(none_as_null=True),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
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
        sa.Column(
            "lesson_id",
            sa.Integer(),
            sa.ForeignKey("rag.lessons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        schema="rag",
        comment="Transcriptions of lesson content",
    )

    # Create indexes
    op.create_index(
        "idx_courses_code",
        "courses",
        ["code"],
        schema="rag",
        postgresql_using="btree",
    )
    op.create_index(
        "idx_lessons_course",
        "lessons",
        ["course_id"],
        schema="rag",
        postgresql_using="btree",
    )
    op.create_index(
        "idx_lessons_course_number",
        "lessons",
        ["course_id", "number"],
        schema="rag",
        postgresql_using="btree",
    )
    op.create_index(
        "idx_transcriptions_lesson",
        "transcriptions",
        ["lesson_id"],
        schema="rag",
        postgresql_using="btree",
    )

    # Create GIN indexes for JSONB columns
    for table, column in [
        ("courses", "course_metadata"),
        ("lessons", "lesson_metadata"),
        ("transcriptions", "transcription_metadata"),
    ]:
        op.create_index(
            f"idx_{table}_{column}",
            table,
            [column],
            unique=False,
            schema="rag",
            postgresql_using="gin",
        )

    # Create functions for timestamp management
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

    # Create triggers for timestamp updates
    for table in ["courses", "lessons", "transcriptions"]:
        op.execute(
            f"""
        CREATE TRIGGER update_{table}_timestamp
        BEFORE UPDATE ON rag.{table}
        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
        """,
        )

    # Create function to automatically notify changes
    op.execute(
        """
    CREATE OR REPLACE FUNCTION notify_record_change()
    RETURNS TRIGGER AS $$
    DECLARE
        payload TEXT;
    BEGIN
        payload := json_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_NAME,
            'id', CASE TG_OP WHEN 'DELETE' THEN OLD.id ELSE NEW.id END
        )::text;

        PERFORM pg_notify('record_changes', payload);
        RETURN NULL;
    END;
    $$ language 'plpgsql';
    """,
    )

    # Apply triggers for change notifications
    for table in ["courses", "lessons", "transcriptions"]:
        op.execute(
            f"""
        CREATE TRIGGER {table}_change_notify
        AFTER INSERT OR UPDATE OR DELETE ON rag.{table}
        FOR EACH ROW EXECUTE FUNCTION notify_record_change();
        """,
        )


def downgrade() -> None:
    # Drop triggers
    for table in ["courses", "lessons", "transcriptions"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_timestamp ON rag.{table}")
        op.execute(f"DROP TRIGGER IF EXISTS {table}_change_notify ON rag.{table}")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_timestamp()")
    op.execute("DROP FUNCTION IF EXISTS notify_record_change()")

    # Drop indexes
    for table, column in [
        ("courses", "course_metadata"),
        ("lessons", "lesson_metadata"),
        ("transcriptions", "transcription_metadata"),
    ]:
        op.drop_index(f"idx_{table}_{column}", table_name=table, schema="rag")

    op.drop_index(
        "idx_transcriptions_lesson",
        table_name="transcriptions",
        schema="rag",
    )
    op.drop_index("idx_lessons_course_number", table_name="lessons", schema="rag")
    op.drop_index("idx_lessons_course", table_name="lessons", schema="rag")
    op.drop_index("idx_courses_code", table_name="courses", schema="rag")

    # Drop tables
    for table in ["transcriptions", "lessons", "courses"]:
        op.drop_table(table, schema="rag")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS rag CASCADE")

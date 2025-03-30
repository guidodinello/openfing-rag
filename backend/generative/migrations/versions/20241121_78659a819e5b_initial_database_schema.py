"""initial database schema

Revision ID: 78659a819e5b
Revises:
Create Date: 2024-11-21 04:00:53.265542+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from app.core.config import get_settings
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

settings = get_settings()

# revision identifiers, used by Alembic.
revision: str = "78659a819e5b"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create required extensions
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

    # Create raw_transcriptions table
    op.create_table(
        "raw_transcriptions",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "raw_transcription_metadata",
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
            "lesson_id",
            sa.Integer(),
            sa.ForeignKey("rag.lessons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        schema="rag",
        comment="Raw transcriptions of lesson content",
    )

    # Create chunks table
    op.create_table(
        "chunks",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("start_time", sa.Integer(), nullable=False),
        sa.Column("end_time", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(settings.EMBEDDINGS.DIMENSION)),
        sa.Column(
            "chunk_metadata",
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
            "lesson_id",
            sa.Integer(),
            sa.ForeignKey("rag.lessons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "transcription_id",
            sa.Integer(),
            sa.ForeignKey("rag.raw_transcriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.CheckConstraint("start_time < end_time", name="ck_chunks_time_order"),
        schema="rag",
        comment="Processed chunks of transcription content",
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
        "idx_chunks_lesson",
        "chunks",
        ["lesson_id"],
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

    # Create vector index for embeddings
    op.execute(
        """
        CREATE INDEX idx_chunks_embedding ON rag.chunks 
        USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100)
        """
    )

    # Create GIN indexes for JSONB columns
    for table in ["chunks", "lessons", "courses", "raw_transcriptions"]:
        op.create_index(
            f"idx_{table}_metadata",
            table,
            [f"{table.rstrip('s')}_metadata"],
            unique=False,
            schema="rag",
            postgresql_using="gin",
        )


def downgrade() -> None:
    # Drop indexes
    for table in ["chunks", "lessons", "courses", "raw_transcriptions"]:
        op.drop_index(f"idx_{table}_metadata", table_name=table, schema="rag")

    op.drop_index("idx_lessons_course_number", table_name="lessons", schema="rag")
    op.drop_index("idx_chunks_embedding", table_name="chunks", schema="rag")
    op.drop_index("idx_chunks_lesson", table_name="chunks", schema="rag")
    op.drop_index("idx_lessons_course", table_name="lessons", schema="rag")
    op.drop_index("idx_courses_code", table_name="courses", schema="rag")

    # Drop tables
    for table in ["chunks", "raw_transcriptions", "lessons", "courses"]:
        op.drop_table(table, schema="rag")

    # Drop schema and extensions
    op.execute("DROP SCHEMA IF EXISTS rag CASCADE")
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
    op.execute("DROP EXTENSION IF EXISTS vector")

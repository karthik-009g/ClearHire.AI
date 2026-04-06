"""add pgvector retrieval columns and reconciliation metadata

Revision ID: 20260331_0006
Revises: 20260330_0005
Create Date: 2026-03-31 11:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260331_0006"
down_revision = "20260330_0005"
branch_labels = None
depends_on = None

EMBEDDING_DIMENSIONS = 384


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _add_vector_columns_postgresql() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        f"ALTER TABLE resume_versions ADD COLUMN embedding_vector vector({EMBEDDING_DIMENSIONS})"
    )
    op.execute(
        f"ALTER TABLE job_descriptions ADD COLUMN embedding_vector vector({EMBEDDING_DIMENSIONS})"
    )
    op.execute(
        f"ALTER TABLE job_postings ADD COLUMN embedding_vector vector({EMBEDDING_DIMENSIONS})"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resume_versions_embedding_vector "
        "ON resume_versions USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_job_descriptions_embedding_vector "
        "ON job_descriptions USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_job_postings_embedding_vector "
        "ON job_postings USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100)"
    )


def _add_vector_columns_fallback() -> None:
    # Non-PostgreSQL fallback keeps test/dev dialects operational.
    op.add_column("resume_versions", sa.Column("embedding_vector", sa.JSON(), nullable=True))
    op.add_column("job_descriptions", sa.Column("embedding_vector", sa.JSON(), nullable=True))
    op.add_column("job_postings", sa.Column("embedding_vector", sa.JSON(), nullable=True))


def _drop_vector_columns_postgresql() -> None:
    op.execute("DROP INDEX IF EXISTS ix_job_postings_embedding_vector")
    op.execute("DROP INDEX IF EXISTS ix_job_descriptions_embedding_vector")
    op.execute("DROP INDEX IF EXISTS ix_resume_versions_embedding_vector")

    op.execute("ALTER TABLE job_postings DROP COLUMN IF EXISTS embedding_vector")
    op.execute("ALTER TABLE job_descriptions DROP COLUMN IF EXISTS embedding_vector")
    op.execute("ALTER TABLE resume_versions DROP COLUMN IF EXISTS embedding_vector")


def _drop_vector_columns_fallback() -> None:
    op.drop_column("job_postings", "embedding_vector")
    op.drop_column("job_descriptions", "embedding_vector")
    op.drop_column("resume_versions", "embedding_vector")


def upgrade() -> None:
    if _is_postgresql():
        _add_vector_columns_postgresql()
    else:
        _add_vector_columns_fallback()

    op.add_column("match_results", sa.Column("retrieval_score", sa.Float(), nullable=True))
    op.add_column("match_results", sa.Column("retrieval_top_k", sa.Integer(), nullable=True))
    op.add_column("match_results", sa.Column("retrieved_context", sa.JSON(), nullable=True))
    op.add_column(
        "match_results",
        sa.Column("reconciliation_status", sa.String(length=32), nullable=False, server_default="not_checked"),
    )
    op.add_column("match_results", sa.Column("reconciliation_confidence", sa.Float(), nullable=True))
    op.add_column("match_results", sa.Column("reconciliation_notes", sa.Text(), nullable=True))
    op.add_column(
        "match_results",
        sa.Column("abstained", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("match_results", sa.Column("abstain_reason", sa.String(length=255), nullable=True))

    op.create_index(
        "ix_match_results_reconciliation_status",
        "match_results",
        ["reconciliation_status"],
        unique=False,
    )
    op.create_index(
        "ix_match_results_abstained",
        "match_results",
        ["abstained"],
        unique=False,
    )

    op.alter_column("match_results", "reconciliation_status", server_default=None)
    op.alter_column("match_results", "abstained", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_match_results_abstained", table_name="match_results")
    op.drop_index("ix_match_results_reconciliation_status", table_name="match_results")

    op.drop_column("match_results", "abstain_reason")
    op.drop_column("match_results", "abstained")
    op.drop_column("match_results", "reconciliation_notes")
    op.drop_column("match_results", "reconciliation_confidence")
    op.drop_column("match_results", "reconciliation_status")
    op.drop_column("match_results", "retrieved_context")
    op.drop_column("match_results", "retrieval_top_k")
    op.drop_column("match_results", "retrieval_score")

    if _is_postgresql():
        _drop_vector_columns_postgresql()
    else:
        _drop_vector_columns_fallback()
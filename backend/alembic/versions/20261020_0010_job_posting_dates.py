"""Persist source-provided job posting dates separately from fetch times.

Revision ID: 20261020_0010
Revises: 20260403_0009
Create Date: 2026-10-20
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20261020_0010"
down_revision = "20260403_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_postings",
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_job_postings_posted_at", "job_postings", ["posted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_postings_posted_at", table_name="job_postings")
    op.drop_column("job_postings", "posted_at")

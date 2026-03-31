"""add embeddings, scheduler fields, and application autofill

Revision ID: 20260329_0004
Revises: 20260329_0003
Create Date: 2026-03-29 15:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260329_0004"
down_revision = "20260329_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resume_versions", sa.Column("embedding", sa.JSON(), nullable=True))
    op.add_column("job_postings", sa.Column("embedding", sa.JSON(), nullable=True))

    op.add_column("applications", sa.Column("application_url", sa.String(length=1024), nullable=True))
    op.add_column("applications", sa.Column("autofill_payload", sa.JSON(), nullable=True))

    op.add_column("user_preferences", sa.Column("selected_sources_csv", sa.Text(), nullable=True))
    op.add_column(
        "user_preferences",
        sa.Column("auto_schedule_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "user_preferences",
        sa.Column("schedule_time", sa.String(length=5), nullable=False, server_default="09:00"),
    )
    op.add_column(
        "user_preferences",
        sa.Column("schedule_timezone", sa.String(length=64), nullable=False, server_default="Asia/Kolkata"),
    )
    op.add_column(
        "user_preferences",
        sa.Column("auto_scrape_on_login", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "user_preferences",
        sa.Column("auto_email_after_scrape", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("user_preferences", "auto_email_after_scrape")
    op.drop_column("user_preferences", "auto_scrape_on_login")
    op.drop_column("user_preferences", "schedule_timezone")
    op.drop_column("user_preferences", "schedule_time")
    op.drop_column("user_preferences", "auto_schedule_enabled")
    op.drop_column("user_preferences", "selected_sources_csv")

    op.drop_column("applications", "autofill_payload")
    op.drop_column("applications", "application_url")

    op.drop_column("job_postings", "embedding")
    op.drop_column("resume_versions", "embedding")

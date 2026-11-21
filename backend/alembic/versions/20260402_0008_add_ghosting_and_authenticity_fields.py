"""add ghosting risk, authenticity, and candidate preferences

Revision ID: 20260402_0008
Revises: 20260401_0007
Create Date: 2026-04-02 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260402_0008"
down_revision = "20260401_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to job_postings
    op.add_column("job_postings", sa.Column("source_type", sa.String(length=64), nullable=False, server_default="job_board"))
    op.add_column("job_postings", sa.Column("ghosting_risk", sa.String(length=16), nullable=False, server_default="medium"))
    op.add_column("job_postings", sa.Column("authenticity_score", sa.Float(), nullable=False, server_default="50.0"))
    op.add_column("job_postings", sa.Column("is_direct_employer", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("job_postings", sa.Column("is_evergreen", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("job_postings", sa.Column("applicant_count_estimate", sa.Integer(), nullable=True))
    op.add_column("job_postings", sa.Column("ats_provider", sa.String(length=64), nullable=True))
    op.add_column("job_postings", sa.Column("ghosting_signals", sa.JSON(), nullable=True))

    op.create_index("ix_job_postings_source_type", "job_postings", ["source_type"])
    op.create_index("ix_job_postings_ghosting_risk", "job_postings", ["ghosting_risk"])

    # Add columns to user_preferences
    op.add_column("user_preferences", sa.Column("target_companies_csv", sa.Text(), nullable=True))
    op.add_column("user_preferences", sa.Column("exclude_staffing_agencies", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("user_preferences", sa.Column("max_ghosting_risk", sa.String(length=16), nullable=False, server_default="medium_and_low"))
    op.add_column("user_preferences", sa.Column("direct_portals_only", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("user_preferences", sa.Column("max_post_age_days", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("user_preferences", sa.Column("notice_period_days", sa.Integer(), nullable=True))
    op.add_column("user_preferences", sa.Column("serving_notice", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("user_preferences", sa.Column("current_ctc_lpa", sa.Float(), nullable=True))
    op.add_column("user_preferences", sa.Column("expected_ctc_lpa", sa.Float(), nullable=True))
    op.add_column("user_preferences", sa.Column("work_mode", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("user_preferences", "work_mode")
    op.drop_column("user_preferences", "expected_ctc_lpa")
    op.drop_column("user_preferences", "current_ctc_lpa")
    op.drop_column("user_preferences", "serving_notice")
    op.drop_column("user_preferences", "notice_period_days")
    op.drop_column("user_preferences", "max_post_age_days")
    op.drop_column("user_preferences", "direct_portals_only")
    op.drop_column("user_preferences", "max_ghosting_risk")
    op.drop_column("user_preferences", "exclude_staffing_agencies")
    op.drop_column("user_preferences", "target_companies_csv")

    op.drop_index("ix_job_postings_ghosting_risk", table_name="job_postings")
    op.drop_index("ix_job_postings_source_type", table_name="job_postings")
    op.drop_column("job_postings", "ghosting_signals")
    op.drop_column("job_postings", "ats_provider")
    op.drop_column("job_postings", "applicant_count_estimate")
    op.drop_column("job_postings", "is_evergreen")
    op.drop_column("job_postings", "is_direct_employer")
    op.drop_column("job_postings", "authenticity_score")
    op.drop_column("job_postings", "ghosting_risk")
    op.drop_column("job_postings", "source_type")

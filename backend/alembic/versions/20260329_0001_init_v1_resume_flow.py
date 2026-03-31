"""init v1 resume flow

Revision ID: 20260329_0001
Revises:
Create Date: 2026-03-29 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260329_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_path", sa.String(length=512), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("parsed_summary", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resumes_content_hash"), "resumes", ["content_hash"], unique=False)

    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("jd_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "resume_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.String(length=36), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_versions_resume_id"), "resume_versions", ["resume_id"], unique=False)

    op.create_table(
        "match_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.String(length=36), nullable=False),
        sa.Column("job_description_id", sa.Integer(), nullable=False),
        sa.Column("keyword_score", sa.Float(), nullable=False),
        sa.Column("embedding_score", sa.Float(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("gaps", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_description_id"], ["job_descriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_results_job_description_id"), "match_results", ["job_description_id"], unique=False)
    op.create_index(op.f("ix_match_results_resume_id"), "match_results", ["resume_id"], unique=False)
    op.create_index(op.f("ix_match_results_total_score"), "match_results", ["total_score"], unique=False)

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_description_id", sa.Integer(), nullable=False),
        sa.Column("resume_version_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_description_id"], ["job_descriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_version_id"], ["resume_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_applications_job_description_id"), "applications", ["job_description_id"], unique=False)
    op.create_index(op.f("ix_applications_resume_version_id"), "applications", ["resume_version_id"], unique=False)
    op.create_index(op.f("ix_applications_status"), "applications", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_applications_status"), table_name="applications")
    op.drop_index(op.f("ix_applications_resume_version_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_job_description_id"), table_name="applications")
    op.drop_table("applications")

    op.drop_index(op.f("ix_match_results_total_score"), table_name="match_results")
    op.drop_index(op.f("ix_match_results_resume_id"), table_name="match_results")
    op.drop_index(op.f("ix_match_results_job_description_id"), table_name="match_results")
    op.drop_table("match_results")

    op.drop_index(op.f("ix_resume_versions_resume_id"), table_name="resume_versions")
    op.drop_table("resume_versions")

    op.drop_table("job_descriptions")

    op.drop_index(op.f("ix_resumes_content_hash"), table_name="resumes")
    op.drop_table("resumes")

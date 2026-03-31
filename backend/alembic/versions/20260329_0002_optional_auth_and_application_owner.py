"""optional auth and application owner

Revision ID: 20260329_0002
Revises: 20260329_0001
Create Date: 2026-03-29 00:20:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260329_0002"
down_revision = "20260329_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.add_column("applications", sa.Column("user_id", sa.String(length=36), nullable=True))
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_applications_user_id"), table_name="applications")
    op.drop_column("applications", "user_id")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

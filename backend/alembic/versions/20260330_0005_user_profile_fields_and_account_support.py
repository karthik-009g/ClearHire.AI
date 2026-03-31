"""add user profile fields and updated timestamp

Revision ID: 20260330_0005
Revises: 20260329_0004
Create Date: 2026-03-30 20:35:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260330_0005"
down_revision = "20260329_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("headline", sa.String(length=160), nullable=True))
    op.add_column("users", sa.Column("location", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=40), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("profile_image_data_url", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_column("users", "updated_at")
    op.drop_column("users", "profile_image_data_url")
    op.drop_column("users", "bio")
    op.drop_column("users", "phone")
    op.drop_column("users", "location")
    op.drop_column("users", "headline")
    op.drop_column("users", "full_name")

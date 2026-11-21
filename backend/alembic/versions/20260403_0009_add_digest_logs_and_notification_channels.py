"""add digest logs and notification channel configurations

Revision ID: 20260403_0009
Revises: 20260402_0008
Create Date: 2026-04-03 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260403_0009"
down_revision = "20260402_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add notification channels to user_preferences
    op.add_column("user_preferences", sa.Column("telegram_chat_id", sa.String(length=64), nullable=True))
    op.add_column("user_preferences", sa.Column("whatsapp_number", sa.String(length=32), nullable=True))
    op.add_column("user_preferences", sa.Column("notification_channels_csv", sa.String(length=128), nullable=True, server_default="email"))

    # 2. Create digest_logs table
    op.create_table(
        "digest_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="email"),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metrics_snapshot", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="sent"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_digest_logs_user_id", "digest_logs", ["user_id"])
    op.create_index("ix_digest_logs_created_at", "digest_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_digest_logs_created_at", table_name="digest_logs")
    op.drop_index("ix_digest_logs_user_id", table_name="digest_logs")
    op.drop_table("digest_logs")

    op.drop_column("user_preferences", "notification_channels_csv")
    op.drop_column("user_preferences", "whatsapp_number")
    op.drop_column("user_preferences", "telegram_chat_id")

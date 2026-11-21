"""Job posting and user preference models for scraping + digest workflows."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.vector_type import EmbeddingVector
from app.utils.config import settings


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    embedding_vector: Mapped[list[float] | None] = mapped_column(
        EmbeddingVector(settings.embedding_dimensions),
        nullable=True,
    )
    scraped_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="job_board", index=True)
    ghosting_risk: Mapped[str] = mapped_column(String(16), nullable=False, default="medium", index=True)
    authenticity_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    is_direct_employer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_evergreen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    applicant_count_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ats_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ghosting_signals: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    preferred_email: Mapped[str] = mapped_column(String(255), nullable=False)
    target_role: Mapped[str] = mapped_column(String(255), nullable=False, default="Software Engineer")
    locations_csv: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords_csv: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_sources_csv: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_companies_csv: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclude_staffing_agencies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_ghosting_risk: Mapped[str] = mapped_column(String(16), nullable=False, default="medium_and_low")
    direct_portals_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_post_age_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    serving_notice: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    current_ctc_lpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_ctc_lpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    work_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    whatsapp_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notification_channels_csv: Mapped[str | None] = mapped_column(String(128), nullable=True, default="email")
    auto_schedule_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    schedule_time: Mapped[str] = mapped_column(String(5), nullable=False, default="09:00")
    schedule_timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Kolkata")
    auto_scrape_on_login: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_email_after_scrape: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class DigestLog(Base):
    __tablename__ = "digest_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="email")  # email, telegram, whatsapp, in_app
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="sent")  # sent, failed, simulated, skipped
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

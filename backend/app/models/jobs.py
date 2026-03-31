"""Job posting and user preference models for scraping + digest workflows."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


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
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    preferred_email: Mapped[str] = mapped_column(String(255), nullable=False)
    target_role: Mapped[str] = mapped_column(String(255), nullable=False, default="Software Engineer")
    locations_csv: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords_csv: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_sources_csv: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_schedule_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    schedule_time: Mapped[str] = mapped_column(String(5), nullable=False, default="09:00")
    schedule_timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Kolkata")
    auto_scrape_on_login: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_email_after_scrape: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

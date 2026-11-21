"""Schemas for jobs scraping, authenticity scoring, and candidate preferences."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field


class ScrapeJobsRequest(BaseModel):
    sources: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] | None = None
    target_companies: list[str] | None = None
    resume_id: str | None = None
    send_email: bool = False
    posted_within_hours: int | None = Field(default=None, ge=1, le=336)
    direct_portals_only: bool = False
    exclude_staffing_agencies: bool = True
    max_ghosting_risk: str | None = None  # "low_only", "medium_and_low", "all"


class JobItem(BaseModel):
    id: int
    source: str
    company: str
    title: str
    location: str | None = None
    url: str
    description: str | None = None
    scraped_at: datetime | None = None
    posted_at: datetime | None = None
    score: float | None = None
    score_components: dict[str, float] | None = None
    score_weights: dict[str, float] | None = None
    score_availability: dict[str, bool] | None = None
    score_formula: str | None = None
    source_type: str = "job_board"
    ghosting_risk: str = "medium"
    authenticity_score: float = 50.0
    is_direct_employer: bool = False
    is_evergreen: bool = False
    applicant_count_estimate: int | None = None
    ats_provider: str | None = None
    ghosting_signals: dict[str, Any] | None = None
    is_expired: bool = False
    fallback_career_url: str | None = None
    liveness_verified: bool = True


class VerifyJobUrlRequest(BaseModel):
    url: str
    company: str | None = None


class VerifyJobUrlResponse(BaseModel):
    url: str
    is_live: bool
    is_expired: bool
    status_code: int = 200
    reason: str = "ok"
    final_url: str | None = None
    fallback_career_url: str


class ScrapeJobsResponse(BaseModel):
    scraped_count: int
    jobs: list[JobItem]
    top_matches: list[JobItem] = Field(default_factory=list)
    mail_sent_to: str | None = None


class PreferencesRequest(BaseModel):
    preferred_email: EmailStr
    target_role: str = "Software Engineer"
    locations: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    selected_sources: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    exclude_staffing_agencies: bool = True
    max_ghosting_risk: str = "medium_and_low"
    direct_portals_only: bool = False
    max_post_age_days: int = 3
    notice_period_days: int | None = None
    serving_notice: bool = False
    current_ctc_lpa: float | None = None
    expected_ctc_lpa: float | None = None
    work_mode: str | None = None
    auto_schedule_enabled: bool = False
    schedule_time: str = "09:00"
    schedule_timezone: str = "Asia/Kolkata"
    auto_scrape_on_login: bool = False
    auto_email_after_scrape: bool = False


class PreferencesResponse(BaseModel):
    preferred_email: str
    target_role: str
    locations: list[str]
    keywords: list[str]
    selected_sources: list[str]
    target_companies: list[str] = Field(default_factory=list)
    exclude_staffing_agencies: bool = True
    max_ghosting_risk: str = "medium_and_low"
    direct_portals_only: bool = False
    max_post_age_days: int = 3
    notice_period_days: int | None = None
    serving_notice: bool = False
    current_ctc_lpa: float | None = None
    expected_ctc_lpa: float | None = None
    work_mode: str | None = None
    auto_schedule_enabled: bool
    schedule_time: str
    schedule_timezone: str
    auto_scrape_on_login: bool
    auto_email_after_scrape: bool


class DigestRequest(BaseModel):
    resume_id: str | None = None
    target_email: EmailStr | None = None
    top_n: int = Field(default=20, ge=1, le=50)


class DigestResponse(BaseModel):
    recipient: str
    sent: bool
    job_count: int
    top_matches: list[JobItem]

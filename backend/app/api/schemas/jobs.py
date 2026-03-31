"""Schemas for jobs scraping and digest endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class ScrapeJobsRequest(BaseModel):
    sources: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    resume_id: str | None = None
    send_email: bool = False


class JobItem(BaseModel):
    id: int
    source: str
    company: str
    title: str
    location: str | None = None
    url: str
    score: float | None = None


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
    auto_schedule_enabled: bool = False
    schedule_time: str = "09:00"
    schedule_timezone: str = "Asia/Kolkata"
    auto_scrape_on_login: bool = True
    auto_email_after_scrape: bool = True


class PreferencesResponse(BaseModel):
    preferred_email: str
    target_role: str
    locations: list[str]
    keywords: list[str]
    selected_sources: list[str]
    auto_schedule_enabled: bool
    schedule_time: str
    schedule_timezone: str
    auto_scrape_on_login: bool
    auto_email_after_scrape: bool


class DigestRequest(BaseModel):
    resume_id: str
    preferred_email: EmailStr | None = None
    sources: list[str] = Field(default_factory=list)


class DigestResponse(BaseModel):
    sent_to: str
    jobs_count: int
    top_titles: list[str]

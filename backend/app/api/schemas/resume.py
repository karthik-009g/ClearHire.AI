"""Pydantic request/response schemas for resume APIs."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    resume_id: str
    original_filename: str
    created_at: datetime
    expires_at: datetime
    parsed_summary: dict


class MatchRequest(BaseModel):
    resume_id: str
    jd_text: str = Field(min_length=20)
    title: str | None = None
    company: str | None = None
    source: str | None = None


class MatchResponse(BaseModel):
    match_id: int
    keyword_score: float
    embedding_score: float
    total_score: float
    missing_keywords: list[str]
    explanation: dict


class ResumeDetailResponse(BaseModel):
    id: str
    original_filename: str
    created_at: datetime
    expires_at: datetime
    parsed_summary: dict
    latest_version: int


class CleanupResponse(BaseModel):
    deleted_records: int
    deleted_files: int


class ResumeVersionItem(BaseModel):
    id: int
    version_no: int
    created_at: datetime


class ResumeVersionsResponse(BaseModel):
    resume_id: str
    versions: list[ResumeVersionItem]


class TailorRequest(BaseModel):
    resume_id: str
    jd_text: str = Field(min_length=20)
    source_version_no: int = 1
    role: str | None = None
    company: str | None = None
    source: str | None = None
    candidate_name: str = "Candidate"
    include_cover_letter: bool = False


class TailorResponse(BaseModel):
    resume_id: str
    based_on_version: int
    version_no: int
    keyword_score: float
    embedding_score: float
    total_score: float
    tailored_resume_text: str
    cover_letter_text: str | None = None
    change_summary: dict
    apply_ready_package: dict


class TailorPackageResponse(BaseModel):
    resume_id: str
    based_on_version: int
    version_no: int
    package_filename: str

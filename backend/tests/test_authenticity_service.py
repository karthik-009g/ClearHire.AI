from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.authenticity_service import AuthenticityService


def test_detect_direct_greenhouse_ats():
    service = AuthenticityService()
    url = "https://boards.greenhouse.io/postman/jobs/5234567"
    provider, source_type = service._detect_ats_provider(url)

    assert provider == "greenhouse"
    assert source_type == "direct_ats"


def test_detect_direct_lever_ats():
    service = AuthenticityService()
    url = "https://jobs.lever.co/urbancompany/abc-123"
    provider, source_type = service._detect_ats_provider(url)

    assert provider == "lever"
    assert source_type == "direct_ats"


def test_detect_direct_ashby_ats():
    service = AuthenticityService()
    url = "https://jobs.ashbyhq.com/perplexity/def-456"
    provider, source_type = service._detect_ats_provider(url)

    assert provider == "ashby"
    assert source_type == "direct_ats"


def test_detect_darwinbox_ats():
    service = AuthenticityService()
    url = "https://careers.darwinbox.in/jobs/789"
    provider, source_type = service._detect_ats_provider(url)

    assert provider == "darwinbox"
    assert source_type == "direct_ats"


def test_detect_staffing_agency_by_name():
    service = AuthenticityService()
    is_agency, signals = service._detect_agency(
        company="Randstad India",
        description="Senior Backend Engineer role at a leading technology firm",
    )

    assert is_agency is True
    assert any("Randstad" in s for s in signals)


def test_detect_staffing_agency_by_phrase():
    service = AuthenticityService()
    is_agency, signals = service._detect_agency(
        company="ABC Consultants",
        description="We are hiring for our client which is a tier-1 product MNC in Bengaluru",
    )

    assert is_agency is True
    assert len(signals) >= 1


def test_authenticity_analysis_direct_employer_fresh():
    service = AuthenticityService()
    analysis = service.analyze(
        title="Senior Software Engineer, Backend",
        company="Razorpay",
        url="https://boards.greenhouse.io/razorpay/jobs/998877",
        description="Build scalable distributed payments infrastructure using Go and AWS. Minimum 4 years of experience.",
        posted_at=datetime.now(timezone.utc) - timedelta(hours=12),
        applicant_count=25,
    )

    assert analysis.is_direct_employer is True
    assert analysis.ats_provider == "greenhouse"
    assert analysis.source_type == "direct_ats"
    assert analysis.ghosting_risk == "low"
    assert analysis.authenticity_score >= 80.0
    assert analysis.is_evergreen is False


def test_authenticity_analysis_agency_repost_high_ghosting():
    service = AuthenticityService()
    analysis = service.analyze(
        title="Software Engineer - Urgent requirement",
        company="TeamLease Staffing Solutions",
        url="https://www.naukri.com/job-listings-urgent-hiring-123456",
        description="Hiring for client. Immediate joiners only.",
        posted_at=datetime.now(timezone.utc) - timedelta(days=45),
        applicant_count=350,
    )

    assert analysis.is_direct_employer is False
    assert analysis.ghosting_risk == "high"
    assert analysis.is_evergreen is True
    assert analysis.authenticity_score < 40.0

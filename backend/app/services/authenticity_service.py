"""Heuristic source and listing-signal analyzer.

Signals cover URL source, freshness, description detail, agency markers, and applicant
counts when available. They are not probabilities and do not predict employer response.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urlparse

ATS_DOMAINS: dict[str, str] = {
    "greenhouse.io": "greenhouse",
    "boards.greenhouse.io": "greenhouse",
    "lever.co": "lever",
    "jobs.lever.co": "lever",
    "ashbyhq.com": "ashby",
    "jobs.ashbyhq.com": "ashby",
    "myworkdayjobs.com": "workday",
    "smartrecruiters.com": "smartrecruiters",
    "jobs.smartrecruiters.com": "smartrecruiters",
    "darwinbox.in": "darwinbox",
    "careers.darwinbox.in": "darwinbox",
    "keka.com": "keka",
    "careers.keka.com": "keka",
    "bamboohr.com": "bamboohr",
    "taleo.net": "taleo",
    "jobvite.com": "jobvite",
    "workable.com": "workable",
}

AGENCY_KEYWORDS: set[str] = {
    "hiring for our client",
    "hiring for client",
    "client of",
    "confidential client",
    "tier 1 it client",
    "leading it services client",
    "reputed client",
    "staffing solutions",
    "manpower solutions",
    "placement consultancy",
    "executive search",
    "talent acquisition partner",
    "hr consultancy",
    "recruitment agency",
    "recruitment partner",
    "contract to hire",
    "third party payroll",
    "c2h",
}

KNOWN_STAFFING_AGENCIES: set[str] = {
    "adecco",
    "randstad",
    "kelly services",
    "allegis",
    "teamlease",
    "quess",
    "quess corp",
    "michael page",
    "robert half",
    "abc consultants",
    "ciel hr",
    "collabera",
    "mancer",
    "careernet",
    "careernet consulting",
    "headhunters",
    "manpowergroup",
    "experis",
    "teksystems",
    "hays",
    "apeiron",
    "nlb services",
}


@dataclass
class AuthenticityAnalysis:
    authenticity_score: float
    ghosting_risk: str  # Legacy API field: listing-signal band, not response likelihood.
    source_type: str  # "direct_ats", "company_career_page", "curated_startup", "linkedin_direct", "job_board"
    is_direct_employer: bool
    is_evergreen: bool
    ats_provider: str | None
    ghosting_signals: dict[str, Any]


class AuthenticityService:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _detect_ats_provider(url: str) -> tuple[str | None, str]:
        """Detect ATS provider and categorize source type based on URL."""
        if not url:
            return None, "job_board"

        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            path = parsed.path or ""

            for domain, ats_name in ATS_DOMAINS.items():
                if host == domain or host.endswith("." + domain):
                    return ats_name, "direct_ats"

            if "wellfound.com" in host or "instahyre.com" in host:
                return None, "curated_startup"

            if "linkedin.com" in host:
                return None, "linkedin_direct"

            if (
                "careers." in host
                or "jobs." in host
                or "/careers" in path
                or "/jobs" in path
                or "/job/" in path
            ):
                return None, "company_career_page"

            return None, "job_board"
        except Exception:
            return None, "job_board"

    @staticmethod
    def _detect_agency(company: str, description: str | None) -> tuple[bool, list[str]]:
        """Identify if a posting originates from a staffing or recruiting agency."""
        detected_signals: list[str] = []
        comp_lower = (company or "").strip().lower()
        desc_lower = (description or "").lower()

        for agency in KNOWN_STAFFING_AGENCIES:
            if agency == comp_lower or f" {agency} " in f" {comp_lower} ":
                detected_signals.append(f"Identified recruitment agency: {company}")
                return True, detected_signals

        for keyword in AGENCY_KEYWORDS:
            if keyword in comp_lower:
                detected_signals.append(f"Agency marker in company: '{keyword}'")
                return True, detected_signals
            if keyword in desc_lower:
                detected_signals.append(f"Agency disclaimer in description: '{keyword}'")
                return True, detected_signals

        if re.search(r"\b(client of\s+[A-Za-z0-9]+)\b", comp_lower):
            detected_signals.append("Posting lists 'client of' intermediary")
            return True, detected_signals

        return False, detected_signals

    def analyze(
        self,
        title: str,
        company: str,
        url: str,
        description: str | None = None,
        source: str = "generic",
        posted_at: datetime | None = None,
        applicant_count: int | None = None,
    ) -> AuthenticityAnalysis:
        ats_provider, source_type = self._detect_ats_provider(url)
        is_agency, agency_signals = self._detect_agency(company, description)
        # A recognized ATS or likely careers-page source is stronger evidence;
        # absence of an agency marker on a generic job board is not enough to call it direct.
        is_direct_employer = source_type == "direct_ats" and not is_agency

        score = 50.0
        positive_signals: list[str] = []
        risk_factors: list[str] = []

        # 1. Source directness evaluation
        if source_type == "direct_ats" and ats_provider:
            score += 35.0
            positive_signals.append(f"Recognized public ATS board domain ({ats_provider.title()})")
        elif source_type == "company_career_page":
            score += 25.0
            positive_signals.append("URL resembles a careers page; employer ownership is not verified")
        elif source_type == "curated_startup":
            score += 20.0
            positive_signals.append("Job platform source; listing owner is not independently confirmed")
        elif source_type == "linkedin_direct":
            score += 5.0
            positive_signals.append("Direct LinkedIn company listing")

        # 2. Staffing agency penalty
        if is_agency:
            score -= 40.0
            risk_factors.extend(agency_signals)
            risk_factors.append("Staffing/consultancy markers detected; confirm the employer and payroll arrangement.")

        # 3. Freshness vs Staleness evaluation
        now = datetime.now(timezone.utc)
        post_age_hours: float | None = None
        is_evergreen = False

        if posted_at:
            dt = posted_at if posted_at.tzinfo else posted_at.replace(tzinfo=timezone.utc)
            post_age_hours = max(0.0, (now - dt).total_seconds() / 3600.0)

            if post_age_hours <= 48.0:
                score += 15.0
                positive_signals.append(f"Fresh posting ({round(post_age_hours, 1)} hours ago)")
            elif post_age_hours <= 168.0:  # <= 7 days
                score += 5.0
                positive_signals.append(f"Recent opening ({int(post_age_hours // 24)} days ago)")
            elif post_age_hours >= 720.0:  # >= 30 days
                score -= 25.0
                is_evergreen = True
                risk_factors.append("Listing date is at least 30 days old; recheck current availability")
            elif post_age_hours >= 360.0:  # >= 15 days
                score -= 10.0
                risk_factors.append("Older listing (> 15 days old)")

        # 4. Description depth check
        desc_len = len(description or "")
        if desc_len < 120:
            score -= 15.0
            risk_factors.append("Extremely sparse job description (often indicates placeholder or repost)")
        elif desc_len > 400:
            score += 5.0
            positive_signals.append("Detailed role description and concrete requirements")

        # 5. Competition saturation check
        if applicant_count is not None:
            if applicant_count > 150:
                score -= 15.0
                risk_factors.append(f"High applicant saturation ({applicant_count}+ applicants already submitted)")
            elif applicant_count < 40:
                score += 10.0
                positive_signals.append("Low reported applicant count; the data may be incomplete")

        final_score = max(5.0, min(100.0, score))

        if final_score >= 70.0 and is_direct_employer:
            ghosting_risk = "low"
        elif final_score >= 42.0 and not is_agency:
            ghosting_risk = "medium"
        else:
            ghosting_risk = "high"

        return AuthenticityAnalysis(
            authenticity_score=round(final_score, 1),
            ghosting_risk=ghosting_risk,
            source_type=source_type,
            is_direct_employer=is_direct_employer,
            is_evergreen=is_evergreen,
            ats_provider=ats_provider,
            ghosting_signals={
                "authenticity_score": round(final_score, 1),
                "ghosting_risk": ghosting_risk,
                "interpretation": "heuristic listing signals; not a probability or response prediction",
                "source_type": source_type,
                "ats_provider": ats_provider,
                "is_direct_employer": is_direct_employer,
                "is_staffing_agency": is_agency,
                "is_evergreen": is_evergreen,
                "positive_signals": positive_signals,
                "risk_factors": risk_factors,
                "applicant_count": applicant_count,
                "post_age_hours": round(post_age_hours, 1) if post_age_hours is not None else None,
            },
        )

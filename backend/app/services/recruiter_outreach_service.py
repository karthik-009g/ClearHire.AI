"""AI Recruiter & Hiring Manager Outreach Drafter.

Generates high-converting, personalized LinkedIn InMails, connection notes, and follow-ups
tailored to specific direct job openings and candidate verified achievements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.jobs import UserPreference


@dataclass
class OutreachPackage:
    hiring_manager_inmail: str
    linkedin_connection_note: str
    follow_up_email: str
    target_role: str
    target_company: str
    grounded_highlights: list[str]


class RecruiterOutreachService:
    def __init__(self) -> None:
        pass

    def generate_outreach(
        self,
        company: str,
        role: str,
        job_url: str | None = None,
        candidate_name: str = "Candidate",
        parsed_summary: dict | None = None,
        preferences: UserPreference | None = None,
    ) -> OutreachPackage:
        raw_skills = (parsed_summary or {}).get("skills") or []
        top_skills = [s for s in raw_skills if isinstance(s, str)][:4]
        skills_phrase = ", ".join(top_skills) if top_skills else "distributed systems and backend architecture"

        notice_days = getattr(preferences, "notice_period_days", 30) if preferences else 30
        if notice_days is None:
            notice_days = 30
        serving = getattr(preferences, "serving_notice", False) if preferences else False

        notice_phrase = "currently serving notice and available for early onboarding" if serving else f"with a {notice_days}-day notice period"

        highlights = [
            f"Target role: {role} at {company}",
            f"Core technical competencies: {skills_phrase}",
            f"Availability: {notice_phrase}",
        ]

        # 1. High-Impact Hiring Manager InMail / Email (~120 words)
        inmail = (
            f"Hi [Hiring Manager / Recruiter Name],\n\n"
            f"I recently came across the {role} opening at {company} and wanted to reach out directly. "
            f"With hands-on experience specializing in {skills_phrase}, I've focused on building high-reliability, "
            f"scalable services and driving measurable system performance improvements.\n\n"
            f"Given {company}'s current technical milestones, I believe my background aligns closely with the team's engineering roadmap. "
            f"I am {notice_phrase} and would love to connect for a brief 10-minute conversation to see how my experience can add value.\n\n"
            f"Best regards,\n{candidate_name}"
        )

        # 2. LinkedIn Connection Request Note (Strictly under 300 characters)
        conn_note = (
            f"Hi [Name], I saw the {role} role at {company}. "
            f"I specialize in {skills_phrase} and am {notice_phrase}. "
            f"Would love to connect and explore how my background could contribute to the team!"
        )
        if len(conn_note) > 295:
            short_skill = top_skills[0] if top_skills else "backend engineering"
            short_role = role[:35] + "..." if len(role) > 38 else role
            short_company = company[:30] + "..." if len(company) > 33 else company
            conn_note = (
                f"Hi [Name], I applied for the {short_role} role at {short_company}. "
                f"I specialize in {short_skill}. Would love to connect to discuss fit!"
            )
        if len(conn_note) > 295:
            conn_note = conn_note[:292] + "..."

        # 3. 7-Day Respectful Follow-Up
        follow_up = (
            f"Hi [Hiring Manager / Recruiter Name],\n\n"
            f"Hope you are having a productive week. Following up on my application for the {role} position at {company}.\n\n"
            f"I remain enthusiastic about the opportunity to contribute my expertise in {skills_phrase} to the team. "
            f"Please let me know if there are any additional work samples, technical details, or references I can provide.\n\n"
            f"Thank you for your time and consideration,\n{candidate_name}"
        )

        return OutreachPackage(
            hiring_manager_inmail=inmail,
            linkedin_connection_note=conn_note,
            follow_up_email=follow_up,
            target_role=role,
            target_company=company,
            grounded_highlights=highlights,
        )

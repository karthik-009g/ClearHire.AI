"""Local AI service compatibility layer.

Kept for project structure parity with API-based tutorials.
This free version performs local, deterministic optimization logic.
"""

from __future__ import annotations

from services.resume_analyzer_service import analyze_resume


def optimize_resume_locally(resume_text: str, jd_text: str = "", target_role: str = "Software Engineer") -> dict:
    """Return optimization insights without any external API call."""
    return analyze_resume(
        resume_text=resume_text,
        jd_text=jd_text,
        target_role=target_role,
        mode="Balanced",
    )

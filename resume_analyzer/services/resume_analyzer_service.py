"""Free, offline resume analyzer and optimizer logic.

This module intentionally avoids paid APIs and works with local heuristics.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from utils.config import MAX_MISSING_KEYWORDS, SECTION_HINTS

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "you", "your", "from", "are",
    "have", "has", "was", "were", "will", "would", "can", "could", "should", "about",
    "into", "onto", "their", "them", "they", "our", "out", "all", "any", "who",
    "how", "why", "when", "where", "job", "role", "work", "using", "used", "use",
    "years", "year", "months", "month", "a", "an", "to", "of", "in", "on", "at",
    "is", "it", "as", "or", "by", "be", "if", "not", "we", "i"
}

ACTION_VERBS = {
    "built", "designed", "developed", "implemented", "optimized", "led", "improved",
    "delivered", "automated", "created", "launched", "managed", "reduced", "increased",
    "engineered", "analyzed", "collaborated", "streamlined", "scaled", "deployed"
}


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\+\#\.\-]{1,}", lowered)
    return [token for token in tokens if token not in STOPWORDS]


def _extract_keywords(text: str, top_k: int = 40) -> list[str]:
    tokens = _tokenize(text)
    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(top_k)]


def _extract_bullet_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    bullets = []
    for line in lines:
        if not line:
            continue
        if re.match(r"^(\-|\*|\u2022|\d+\.)\s+", line):
            bullets.append(re.sub(r"^(\-|\*|\u2022|\d+\.)\s+", "", line).strip())
    return bullets


def _contact_score(text_lower: str) -> int:
    score = 0
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text_lower):
        score += 35
    if re.search(r"\+?\d[\d\s\-]{7,}\d", text_lower):
        score += 35
    if "linkedin" in text_lower or "github" in text_lower:
        score += 30
    return min(score, 100)


def _section_score(text_lower: str) -> int:
    found = 0
    for hints in SECTION_HINTS.values():
        if any(hint in text_lower for hint in hints):
            found += 1
    return int((found / len(SECTION_HINTS)) * 100)


def _impact_score(text: str) -> int:
    text_lower = text.lower()
    action_hits = sum(1 for verb in ACTION_VERBS if verb in text_lower)
    action_score = min(60, action_hits * 6)

    metric_hits = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))
    metric_score = min(40, metric_hits * 4)
    return min(100, action_score + metric_score)


def _keyword_match_score(resume_text: str, jd_text: str) -> tuple[int, list[str], list[str]]:
    resume_keywords = set(_extract_keywords(resume_text, top_k=120))
    jd_keywords = _extract_keywords(jd_text, top_k=80)

    if not jd_keywords:
        return 50, [], []

    matched = [kw for kw in jd_keywords if kw in resume_keywords]
    missing = [kw for kw in jd_keywords if kw not in resume_keywords]
    match_ratio = len(matched) / len(jd_keywords)
    return int(match_ratio * 100), matched[:20], missing[:MAX_MISSING_KEYWORDS]


def _rewrite_bullet(bullet: str, mode: str) -> str:
    compact = _normalize_whitespace(bullet)
    if len(compact) < 30:
        return f"Improved {compact} by applying best practices and measurable outcomes."

    prefix = {
        "Conservative": "Enhanced",
        "Balanced": "Optimized",
        "Aggressive": "Transformed",
    }.get(mode, "Optimized")

    if not re.search(r"\b\d+(?:\.\d+)?%?\b", compact):
        return f"{prefix} {compact.lower()} resulting in [X%] improvement in [business metric]."

    return f"{prefix} {compact.lower()} to strengthen delivery speed, quality, and measurable impact."


def _generate_summary(resume_text: str, jd_text: str, target_role: str) -> str:
    resume_top = _extract_keywords(resume_text, top_k=8)
    jd_top = _extract_keywords(jd_text, top_k=8)

    resume_focus = ", ".join(resume_top[:5]) if resume_top else "software development"
    jd_focus = ", ".join(jd_top[:5]) if jd_top else "core role requirements"

    return (
        f"Results-driven {target_role} with strong exposure to {resume_focus}. "
        f"Aligned to target opportunities emphasizing {jd_focus}. "
        "Demonstrates execution ownership, cross-functional collaboration, and measurable business impact."
    )


def analyze_resume(
    resume_text: str,
    jd_text: str = "",
    target_role: str = "Software Engineer",
    mode: str = "Balanced",
) -> dict[str, Any]:
    """Analyze resume text and return ATS-like score plus optimization suggestions."""
    cleaned_resume = resume_text.strip()
    cleaned_jd = jd_text.strip()

    if not cleaned_resume:
        raise ValueError("Resume text is empty.")

    resume_lower = cleaned_resume.lower()

    contact = _contact_score(resume_lower)
    structure = _section_score(resume_lower)
    impact = _impact_score(cleaned_resume)
    keyword_score, matched_keywords, missing_keywords = _keyword_match_score(cleaned_resume, cleaned_jd)

    overall = int(
        0.20 * contact
        + 0.25 * structure
        + 0.30 * impact
        + 0.25 * keyword_score
    )

    bullets = _extract_bullet_lines(cleaned_resume)
    rewritten = [_rewrite_bullet(b, mode) for b in bullets[:6]]

    strengths = []
    if contact >= 70:
        strengths.append("Contact information appears complete and ATS-readable.")
    if impact >= 65:
        strengths.append("Resume includes action-focused language and measurable details.")
    if structure >= 70:
        strengths.append("Resume has common ATS-friendly sections.")

    gaps = []
    if contact < 70:
        gaps.append("Add or verify email, phone number, and professional profile links.")
    if structure < 70:
        gaps.append("Use clear section headers: Summary, Skills, Experience, Projects, Education.")
    if impact < 65:
        gaps.append("Add quantifiable outcomes (percentages, counts, time savings, revenue impact).")
    if cleaned_jd and keyword_score < 65:
        gaps.append("Increase job-description keyword alignment in skills and experience bullets.")

    return {
        "ats_score": overall,
        "component_scores": {
            "contact": contact,
            "structure": structure,
            "impact": impact,
            "keyword_match": keyword_score,
        },
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "strengths": strengths,
        "gaps": gaps,
        "optimized_summary": _generate_summary(cleaned_resume, cleaned_jd, target_role),
        "rewritten_bullets": rewritten,
    }

"""Deterministic resume tailoring service for V1 controlled edits."""

from __future__ import annotations

import re
from typing import Any


class ResumeTailorService:
    @staticmethod
    def _normalize_spaces(text: str) -> str:
        return re.sub(r"[ \t]+", " ", text).strip()

    @staticmethod
    def _split_lines(text: str) -> list[str]:
        return [line.rstrip() for line in text.splitlines()]

    @staticmethod
    def _inject_missing_keywords(resume_text: str, missing_keywords: list[str]) -> str:
        if not missing_keywords:
            return resume_text

        top_keywords = missing_keywords[:8]
        section_title = "\n\nTargeted Skills\n"
        section_body = ", ".join(top_keywords)

        if "targeted skills" in resume_text.lower():
            return resume_text

        return f"{resume_text.strip()}{section_title}{section_body}\n"

    def _tighten_bullets(self, resume_text: str) -> str:
        lines = self._split_lines(resume_text)
        improved: list[str] = []

        for line in lines:
            stripped = line.strip()
            if re.match(r"^(\-|\*|\u2022|\d+\.)\s+", stripped):
                bullet_body = re.sub(r"^(\-|\*|\u2022|\d+\.)\s+", "", stripped)
                bullet_body = self._normalize_spaces(bullet_body)
                if len(bullet_body) > 0 and not re.search(r"\b\d+(?:\.\d+)?%?\b", bullet_body):
                    bullet_body = f"{bullet_body}; delivered measurable impact in quality or speed"
                improved.append(f"- {bullet_body}")
            else:
                improved.append(line)

        return "\n".join(improved).strip()

    @staticmethod
    def generate_cover_letter(
        candidate_name: str,
        company: str | None,
        role: str | None,
        matched_keywords: list[str],
    ) -> str:
        company_name = company or "the company"
        role_name = role or "the role"
        highlights = ", ".join(matched_keywords[:6]) if matched_keywords else "relevant technical and delivery skills"

        return (
            f"Dear Hiring Team at {company_name},\n\n"
            f"I am excited to apply for {role_name}. My background aligns strongly with your requirements, "
            f"especially in {highlights}.\n\n"
            "I focus on delivering reliable outcomes, clear communication, and measurable results. "
            "I would value the opportunity to contribute to your team.\n\n"
            f"Sincerely,\n{candidate_name}"
        )

    def tailor_resume(
        self,
        resume_text: str,
        jd_text: str,
        missing_keywords: list[str],
        matched_keywords: list[str],
        candidate_name: str = "Candidate",
        role: str | None = None,
        company: str | None = None,
        include_cover_letter: bool = False,
    ) -> dict[str, Any]:
        tailored = resume_text
        tailored = self._inject_missing_keywords(tailored, missing_keywords)
        tailored = self._tighten_bullets(tailored)

        result: dict[str, Any] = {
            "tailored_resume_text": tailored,
            "change_summary": {
                "keywords_added": missing_keywords[:8],
                "bullet_improvements": True,
                "controlled_style": "v1-deterministic",
            },
            "apply_ready_package": {
                "files": [
                    "tailored_resume.txt",
                    "match_explanation.txt",
                ]
            },
            "match_explanation_text": (
                "Resume was tailored with controlled edits based on JD gaps. "
                f"Top aligned keywords: {', '.join(matched_keywords[:8]) or 'N/A'}."
            ),
        }

        if include_cover_letter:
            cover_letter = self.generate_cover_letter(
                candidate_name=candidate_name,
                company=company,
                role=role,
                matched_keywords=matched_keywords,
            )
            result["cover_letter_text"] = cover_letter
            result["apply_ready_package"]["files"].append("cover_letter.txt")

        return result

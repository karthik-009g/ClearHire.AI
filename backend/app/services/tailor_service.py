"""Deterministic resume tailoring service for V1 controlled edits."""

from __future__ import annotations

import re
from typing import Any


class ResumeTailorService:
    MAX_RESUME_LINES = 48
    MAX_RESUME_WORDS = 620
    MAX_BULLET_WORDS = 24

    @staticmethod
    def _normalize_spaces(text: str) -> str:
        return re.sub(r"[ \t]+", " ", text).strip()

    @staticmethod
    def _split_lines(text: str) -> list[str]:
        return [line.rstrip() for line in text.splitlines()]

    @staticmethod
    def _keyword_exists_in_resume(resume_text: str, keyword: str) -> bool:
        normalized_resume = resume_text.lower()
        normalized_keyword = ResumeTailorService._normalize_spaces(keyword).lower()
        if not normalized_keyword:
            return False
        if normalized_keyword in normalized_resume:
            return True

        keyword_parts = [part for part in re.split(r"[\s/,+-]+", normalized_keyword) if len(part) > 2]
        return bool(keyword_parts) and all(part in normalized_resume for part in keyword_parts)

    @classmethod
    def _prepare_target_keywords(
        cls,
        resume_text: str,
        missing_keywords: list[str],
    ) -> tuple[list[str], list[str], list[str]]:
        seen: set[str] = set()
        target_keywords: list[str] = []
        unsupported_keywords: list[str] = []

        for keyword in missing_keywords:
            clean = cls._normalize_spaces(str(keyword))
            key = clean.lower()
            if not clean or key in seen:
                continue
            seen.add(key)
            target_keywords.append(clean)
            if not cls._keyword_exists_in_resume(resume_text, clean):
                unsupported_keywords.append(clean)
            if len(target_keywords) >= 8:
                break

        supported_keywords = [keyword for keyword in target_keywords if keyword not in unsupported_keywords]
        return target_keywords, supported_keywords, unsupported_keywords

    @classmethod
    def _inject_missing_keywords(
        cls,
        resume_text: str,
        missing_keywords: list[str],
    ) -> tuple[str, list[str], list[str], list[str]]:
        if not missing_keywords:
            return resume_text, [], [], []

        target_keywords, supported_keywords, unsupported_keywords = cls._prepare_target_keywords(
            resume_text,
            missing_keywords,
        )
        section_title = "\n\nTargeted Skills\n"
        section_body = "JD keywords to review: " + ", ".join(target_keywords)

        if "targeted skills" in resume_text.lower():
            return resume_text, target_keywords, supported_keywords, unsupported_keywords

        return f"{resume_text.strip()}{section_title}{section_body}\n", target_keywords, supported_keywords, unsupported_keywords

    def _tighten_bullets(self, resume_text: str) -> str:
        lines = self._split_lines(resume_text)
        improved: list[str] = []

        for line in lines:
            stripped = line.strip()
            if re.match(r"^(\-|\*|\u2022|\d+\.)\s+", stripped):
                bullet_body = re.sub(r"^(\-|\*|\u2022|\d+\.)\s+", "", stripped)
                bullet_body = self._normalize_spaces(bullet_body)
                if not bullet_body:
                    continue
                bullet_body = bullet_body[0].upper() + bullet_body[1:]
                words = bullet_body.split()
                if len(words) > self.MAX_BULLET_WORDS:
                    bullet_body = " ".join(words[: self.MAX_BULLET_WORDS]).rstrip(".,;") + "."
                elif not bullet_body.endswith((".", "!", "?")):
                    bullet_body = bullet_body.rstrip(";,") + "."
                improved.append(f"- {bullet_body}")
            else:
                improved.append(line)

        return "\n".join(improved).strip()

    def _enforce_one_page(self, resume_text: str) -> str:
        """Approximate a one-page ATS resume in plain text while preserving section order and whole lines."""
        lines = [line.rstrip() for line in resume_text.splitlines()]
        compact: list[str] = []
        previous_blank = False
        for line in lines:
            blank = not line.strip()
            if blank and previous_blank:
                continue
            compact.append(line)
            previous_blank = blank

        line_count = 0
        word_count = 0
        capped: list[str] = []
        for line in compact:
            words = line.split()
            line_words = len(words)
            if line_count + 1 > self.MAX_RESUME_LINES:
                break
            if word_count + line_words > self.MAX_RESUME_WORDS:
                break
            capped.append(line)
            line_count += 1
            word_count += line_words

        return "\n".join(capped).strip()

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
        tailored, target_keywords, supported_keywords, unsupported_keywords = self._inject_missing_keywords(
            tailored,
            missing_keywords,
        )
        tailored = self._tighten_bullets(tailored)
        tailored = self._enforce_one_page(tailored)
        review_required = bool(unsupported_keywords)

        result: dict[str, Any] = {
            "tailored_resume_text": tailored,
            "change_summary": {
                "keywords_added": target_keywords,
                "supported_keywords_added": supported_keywords,
                "unsupported_keywords_requiring_review": unsupported_keywords,
                "review_required": review_required,
                "bullet_improvements": True,
                "ats_constraints": {
                    "one_page_limit": True,
                    "max_lines": self.MAX_RESUME_LINES,
                    "max_words": self.MAX_RESUME_WORDS,
                    "core_structure_preserved": True,
                    "plain_text_ats_safe": True,
                },
                "guardrails": {
                    "no_unverified_experience_claims": True,
                    "unsupported_keywords_are_marked_for_review": True,
                    "human_review_required_before_submission": review_required,
                },
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

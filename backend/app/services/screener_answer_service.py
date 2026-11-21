"""Candidate-grounded drafts for common job-application screening questions."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.jobs import UserPreference


@dataclass
class ScreenerAnswerResult:
    answer: str
    detected_intent: str
    confidence_score: float
    grounded_facts: list[str] = field(default_factory=list)


class ScreenerAnswerService:
    @staticmethod
    def _detect_intent(question: str) -> str:
        q = (question or "").lower()
        if any(term in q for term in ("notice", "how soon", "when can you join", "joining date", "serving notice", "availability")):
            return "notice_period"
        if any(term in q for term in ("ctc", "salary", "compensation", "expected salary", "current salary", "remuneration")):
            return "compensation"
        if any(term in q for term in ("relocate", "relocation", "remote", "hybrid", "in-office", "work from office", "wfo", "commute")):
            return "work_mode_location"
        if any(term in q for term in ("work authorization", "authorized to work", "visa", "sponsorship", "citizen", "eligible to work")):
            return "work_authorization"
        if any(term in q for term in ("why do you want", "why work at", "why our company", "why this role", "what attracted you", "why join")):
            return "motivation"
        if any(term in q for term in ("describe a challenge", "project", "experience with", "how do you design", "architecture", "scale", "concurrency", "distributed", "database")):
            return "technical_experience"
        return "general_qualification"

    @staticmethod
    def _extract_skills(parsed_summary: dict | None) -> list[str]:
        if not isinstance(parsed_summary, dict):
            return []
        skills = parsed_summary.get("skills") or []
        if not isinstance(skills, list):
            return []
        return [str(skill).strip() for skill in skills if str(skill).strip()]

    @staticmethod
    def _needs_confirmation(intent: str, answer: str) -> ScreenerAnswerResult:
        return ScreenerAnswerResult(answer, intent, 0.0, [])

    @staticmethod
    def _limit_words(answer: str, max_words: int) -> str:
        limit = max(1, min(int(max_words), 500))
        words = answer.split()
        return answer if len(words) <= limit else " ".join(words[:limit])

    def answer_question(
        self,
        question: str,
        company: str | None = None,
        role: str | None = None,
        resume_text: str | None = None,
        parsed_summary: dict | None = None,
        preferences: UserPreference | None = None,
        max_words: int = 150,
    ) -> ScreenerAnswerResult:
        intent = self._detect_intent(question)
        company_name = (company or "").strip()
        role_name = (role or "").strip()
        skills = self._extract_skills(parsed_summary)
        skills_text = ", ".join(skills[:5])

        if intent == "notice_period":
            days = getattr(preferences, "notice_period_days", None) if preferences else None
            if days is None:
                return self._needs_confirmation(intent, "Please enter your notice period and confirm your earliest joining date before using an answer.")
            facts = [f"Saved notice period: {days} days"]
            if getattr(preferences, "serving_notice", False):
                answer = f"For the role at {company_name or 'this company'}, I am currently serving my notice period; my saved notice period is {days} days."
            else:
                answer = f"My saved notice period is {days} days. Please confirm your earliest joining date before submitting."
            return ScreenerAnswerResult(self._limit_words(answer, max_words), intent, 0.9, facts)

        if intent == "compensation":
            current = getattr(preferences, "current_ctc_lpa", None) if preferences else None
            expected = getattr(preferences, "expected_ctc_lpa", None) if preferences else None
            q = (question or "").lower()
            asks_current = any(
                term in q
                for term in ("current salary", "current ctc", "current compensation", "present salary", "present ctc")
            )
            asks_expectations = any(term in q for term in ("expect", "desired", "looking for"))

            if asks_current:
                value = current
                label = "current CTC"
                if value is None:
                    return self._needs_confirmation(intent, "Please enter and confirm your current CTC before using an answer.")
                facts = [f"Saved current CTC: {value} LPA"]
                answer = f"For {company_name or 'this role'}, my saved current CTC is {value} LPA. Please confirm before submitting."
            elif asks_expectations and current is not None and expected is not None:
                facts = [f"Saved current CTC: {current} LPA", f"Saved expected CTC: {expected} LPA"]
                answer = (
                    f"For {company_name or 'this role'}, my saved current CTC is {current} LPA and my expected CTC is "
                    f"{expected} LPA. Please confirm both figures before submitting."
                )
            else:
                value = expected
                if value is None:
                    return self._needs_confirmation(intent, "Please enter and confirm your expected CTC before using an answer.")
                facts = [f"Saved expected CTC: {value} LPA"]
                answer = f"For {company_name or 'this role'}, my saved expected CTC is {value} LPA. Please confirm before submitting."
            return ScreenerAnswerResult(self._limit_words(answer, max_words), intent, 0.9, facts)

        if intent == "work_mode_location":
            mode = getattr(preferences, "work_mode", None) if preferences else None
            if not mode:
                return self._needs_confirmation(intent, "Please confirm your preferred work mode and whether you can meet this role's location requirements.")
            facts = [f"Saved work-mode preference: {mode}"]
            answer = f"My saved work-mode preference is {mode}. Please confirm it fits this role's location and onsite requirements."
            return ScreenerAnswerResult(self._limit_words(answer, max_words), intent, 0.85, facts)

        if intent == "work_authorization":
            return self._needs_confirmation(intent, "Please confirm your work authorization and whether you need sponsorship before answering this question.")

        context_facts = []
        if role_name:
            context_facts.append(f"Role context: {role_name}")
        if company_name:
            context_facts.append(f"Company context: {company_name}")

        if intent == "motivation":
            if skills_text:
                facts = context_facts + [f"Skills listed in resume: {skills_text}"]
                answer = (
                    f"Draft only—confirm it reflects your view: I am interested in the {role_name or 'role'} "
                    f"at {company_name or 'this company'}. My resume lists {skills_text}. "
                    "Add one specific company reason and one verified experience example before sending."
                )
                confidence = 0.55
            else:
                facts = context_facts
                answer = (
                    f"Draft only—confirm it reflects your view: I am interested in the {role_name or 'role'} "
                    f"at {company_name or 'this company'}. Add a specific company reason and a verified experience example before sending."
                )
                confidence = 0.25
            return ScreenerAnswerResult(self._limit_words(answer, max_words), intent, confidence, facts)

        if skills_text:
            facts = [f"Skills listed in resume: {skills_text}"]
            answer = (
                f"Draft only—confirm before use: My resume lists {skills_text}. "
                "Add a specific project, your contribution, and a result that directly answers this question."
            )
            confidence = 0.35
        else:
            facts = []
            answer = "I do not have verified experience details for this answer. Add a specific example from your resume before using it."
            confidence = 0.0
        return ScreenerAnswerResult(self._limit_words(answer, max_words), intent, confidence, facts)

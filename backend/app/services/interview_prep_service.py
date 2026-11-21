"""Build a resume-grounded interview preparation pack for one application."""

from __future__ import annotations

import re
from typing import Any


_SKILL_TERMS = (
    "generative ai", "large language models", "machine learning", "deep learning",
    "natural language processing", "computer vision", "reinforcement learning",
    "retrieval augmented generation", "rag", "vector database", "prompt engineering",
    "model evaluation", "model monitoring", "feature engineering", "data engineering",
    "data science", "data analysis", "statistics", "experimentation", "a/b testing",
    "python", "sql", "java", "javascript", "typescript", "c++", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "numpy", "spark", "pyspark", "airflow", "dbt",
    "kafka", "postgresql", "mongodb", "redis", "elasticsearch", "fastapi", "django",
    "flask", "react", "node.js", "docker", "kubernetes", "aws", "azure", "gcp",
    "terraform", "ci/cd", "microservices", "distributed systems", "system design",
    "etl", "data pipelines", "mlops", "llmops", "computer science",
)

_BEHAVIORAL_PROMPTS = (
    "Tell me about a difficult problem you solved. What did you own, what trade-off did you make, and what changed?",
    "Describe a time you received critical feedback. What did you do differently afterward?",
    "Tell me about a disagreement on a team and how you reached a workable decision.",
    "Describe a project that did not go as planned. What would you change if you repeated it?",
)


def _contains_term(text: str, term: str) -> bool:
    return re.search(r"(?<![\w])" + re.escape(term) + r"(?![\w])", text, flags=re.IGNORECASE) is not None


def _snippet(text: str, term: str, limit: int = 260) -> str | None:
    match = re.search(r"(?<![\w])" + re.escape(term) + r"(?![\w])", text, flags=re.IGNORECASE)
    if not match:
        return None
    start = max(text.rfind("\n", 0, match.start()), text.rfind(".", 0, match.start())) + 1
    ends = [position for position in (text.find("\n", match.end()), text.find(".", match.end())) if position >= 0]
    end = min(ends) + 1 if ends else len(text)
    excerpt = " ".join(text[start:end].split())
    if len(excerpt) > limit:
        excerpt = excerpt[: limit - 1].rstrip() + "…"
    return excerpt or None


class InterviewPrepService:
    """Create preparation prompts without inventing candidate experience."""

    def build_pack(
        self,
        *,
        role: str | None,
        company: str | None,
        job_description: str,
        resume_text: str,
        resume_version: int,
        preferences: Any | None = None,
    ) -> dict[str, Any]:
        jd = job_description or ""
        resume = resume_text or ""
        jd_terms = [term for term in _SKILL_TERMS if _contains_term(jd, term)][:12]

        evidence = []
        requirements_to_prepare = []
        technical_prompts = []
        for term in jd_terms:
            job_excerpt = _snippet(jd, term)
            resume_excerpt = _snippet(resume, term)
            item = {
                "requirement": term,
                "resume_status": "mentioned_in_resume" if resume_excerpt else "not_found_in_resume_text",
                "job_description_excerpt": job_excerpt,
                "resume_excerpt": resume_excerpt,
            }
            if resume_excerpt:
                evidence.append(item)
                question = (
                    f"Choose a specific example where you used {term}. What was the problem, your personal contribution, "
                    "one trade-off, and the measurable result?"
                )
                coaching = "The excerpt is a search anchor only. Add project, ownership, and outcome details you can substantiate."
            else:
                requirements_to_prepare.append(item)
                question = (
                    f"The job description mentions {term}, which was not found in the saved resume text. "
                    "If you have relevant experience, explain it with a truthful example; otherwise describe how you would approach the topic and what you still need to learn."
                )
                coaching = "Do not claim experience based only on the job description."
            technical_prompts.append({"requirement": term, "question": question, "coaching": coaching})

        if not technical_prompts:
            technical_prompts.append({
                "requirement": None,
                "question": f"Walk through one technical project relevant to {role or 'this role'}: the goal, your contribution, a design decision, and the result.",
                "coaching": "The saved job description did not contain a supported technical term for a more specific prompt.",
            })

        notice_days = getattr(preferences, "notice_period_days", None) if preferences else None
        # Keep an unknown profile value distinct from an explicit "No".
        serving_notice = getattr(preferences, "serving_notice", None) if preferences else None
        current_ctc = getattr(preferences, "current_ctc_lpa", None) if preferences else None
        expected_ctc = getattr(preferences, "expected_ctc_lpa", None) if preferences else None
        locations_csv = getattr(preferences, "locations_csv", None) if preferences else None
        work_mode = getattr(preferences, "work_mode", None) if preferences else None

        india_context = {
            "notice_period_days": notice_days,
            "serving_notice": serving_notice,
            "current_ctc_lpa": current_ctc,
            "expected_ctc_lpa": expected_ctc,
            "work_mode": work_mode,
            "preferred_locations": [item.strip() for item in (locations_csv or "").split(",") if item.strip()],
            "confirm_before_sharing": True,
            "guidance": "Use saved India-specific values only after checking they are current. Leave unanswered fields blank rather than guessing.",
        }

        return {
            "application_context": {
                "role": role or "Role not set",
                "company": company or "Company not set",
                "resume_version": resume_version,
            },
            "grounding_note": (
                "Prompts are derived from the saved job description and resume text. A phrase found in a resume is not independently verified experience. "
                "Review every prompt and provide your own truthful examples."
            ),
            "method": "Deterministic job-description term matching and resume excerpt retrieval; no experience claims are generated.",
            "resume_evidence": evidence,
            "requirements_to_prepare": requirements_to_prepare,
            "technical_questions": technical_prompts,
            "behavioral_questions": list(_BEHAVIORAL_PROMPTS),
            "recruiter_screen_india": india_context,
            "company_research_prompts": [
                "What product, customer problem, or engineering challenge makes this company interesting to you? Add one verified source before answering.",
                "Why does this role fit your next learning and contribution goals? Use your own reasons; the pack does not infer motivation.",
            ],
            "practice_steps": [
                "Pick two resume excerpts and add your project, personal contribution, and outcome.",
                "Prepare one honest response for each job requirement that was not found in the resume text.",
                "Practice one behavioral prompt with Situation, Task, Action, and Result, then check every detail is accurate.",
                "Confirm notice period, serving status, CTC, work mode, and location before sharing them with a recruiter.",
            ],
        }

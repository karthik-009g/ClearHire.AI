from app.services.tailor_service import ResumeTailorService


def test_tailor_adds_targeted_skills_and_cover_letter():
    service = ResumeTailorService()
    resume_text = """
    Experience
    - Built APIs for internal platforms
    """

    result = service.tailor_resume(
        resume_text=resume_text,
        jd_text="Need Kubernetes and AWS experience",
        missing_keywords=["kubernetes", "aws"],
        matched_keywords=["python", "fastapi"],
        candidate_name="Alex",
        role="Backend Engineer",
        company="Acme",
        include_cover_letter=True,
    )

    assert "Targeted Skills" in result["tailored_resume_text"]
    assert "kubernetes" in result["tailored_resume_text"].lower()
    assert result["change_summary"]["review_required"] is True
    assert result["change_summary"]["guardrails"]["no_unverified_experience_claims"] is True
    assert "cover_letter_text" in result
    assert "Dear Hiring Team" in result["cover_letter_text"]


def test_tailor_keeps_resume_to_one_page_plain_text_limit():
    service = ResumeTailorService()
    resume_text = "\n".join(
        ["Candidate Name", "Skills", "Python, FastAPI", "Experience"]
        + [f"- Built backend platform feature number {idx} for internal users without metrics" for idx in range(80)]
    )

    result = service.tailor_resume(
        resume_text=resume_text,
        jd_text="Need Python, FastAPI, PostgreSQL, Docker, Kubernetes and AWS for backend APIs.",
        missing_keywords=["postgresql", "docker", "kubernetes", "aws"],
        matched_keywords=["python", "fastapi"],
    )

    tailored = result["tailored_resume_text"]
    assert len(tailored.splitlines()) <= service.MAX_RESUME_LINES
    assert len(tailored.split()) <= service.MAX_RESUME_WORDS
    assert result["change_summary"]["ats_constraints"]["one_page_limit"] is True


def test_tailor_marks_unsupported_keywords_for_review_without_claiming_experience():
    service = ResumeTailorService()
    resume_text = """
    Candidate Name
    Skills
    Python, FastAPI
    Experience
    - Built APIs for internal tools
    """

    result = service.tailor_resume(
        resume_text=resume_text,
        jd_text="Need Python, FastAPI, Kubernetes and AWS.",
        missing_keywords=["kubernetes", "aws"],
        matched_keywords=["python", "fastapi"],
    )

    tailored = result["tailored_resume_text"].lower()
    assert "jd keywords to review: kubernetes, aws" in tailored
    assert "kubernetes experience" not in tailored
    assert "delivered measurable impact" not in tailored
    assert result["change_summary"]["unsupported_keywords_requiring_review"] == ["kubernetes", "aws"]
    assert result["change_summary"]["review_required"] is True

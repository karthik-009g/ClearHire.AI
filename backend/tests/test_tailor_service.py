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
    assert "cover_letter_text" in result
    assert "Dear Hiring Team" in result["cover_letter_text"]

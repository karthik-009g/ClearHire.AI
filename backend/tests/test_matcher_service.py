from app.services.matcher_service import ResumeMatcherService


def test_match_scores_and_missing_keywords():
    matcher = ResumeMatcherService()
    resume = "Python FastAPI PostgreSQL Docker CI/CD"
    jd = "Looking for Python, PostgreSQL, Kubernetes and AWS experience"

    result = matcher.match(resume, jd)

    assert result["total_score"] >= 0
    assert "keyword_score" in result
    assert "embedding_score" in result
    assert isinstance(result["missing_keywords"], list)


def test_build_resume_context_preserves_structured_sections():
    matcher = ResumeMatcherService()
    resume = "Experience\nBuilt APIs"
    parsed = {
        "skills": ["python", "fastapi"],
        "sections": {
            "projects": ["Job Automation Platform"],
            "experience": ["Built resilient backend services"],
        },
    }

    context = matcher.build_resume_context(resume, parsed_summary=parsed)

    assert "skills:" in context.lower()
    assert "job automation platform" in context.lower()
    assert "built resilient backend services" in context.lower()


def test_fallback_embedding_uses_consistent_dimension():
    matcher = ResumeMatcherService(embedding_dimensions=384)
    matcher.model = None

    vector = matcher.embed_text("Python FastAPI PostgreSQL Kubernetes")

    assert len(vector) == 384
    assert any(value != 0.0 for value in vector)

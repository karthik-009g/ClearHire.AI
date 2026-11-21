from app.services.matcher_service import ResumeMatcherService


def test_match_scores_and_missing_keywords():
    matcher = ResumeMatcherService(load_embedding_model=False)
    resume = "Python FastAPI PostgreSQL Docker CI/CD"
    jd = "Looking for Python, PostgreSQL, Kubernetes and AWS experience"

    result = matcher.match(resume, jd)

    assert result["total_score"] >= 0
    assert "keyword_score" in result
    assert "embedding_score" in result
    assert isinstance(result["missing_keywords"], list)


def test_build_resume_context_preserves_structured_sections():
    matcher = ResumeMatcherService(load_embedding_model=False)
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
    matcher = ResumeMatcherService(embedding_dimensions=384, load_embedding_model=False)

    vector = matcher.embed_text("Python FastAPI PostgreSQL Kubernetes")

    assert len(vector) == 384
    assert any(value != 0.0 for value in vector)


def test_keyword_overlap_ignores_generic_hiring_language():
    matcher = ResumeMatcherService(load_embedding_model=False)
    resume = "Python FastAPI PostgreSQL Docker"
    jd = "We are looking for a strong candidate with Python, Kubernetes, AWS, and Docker experience."

    result = matcher.match(resume, jd)

    assert "python" in result["matched_keywords"]
    assert "docker" in result["matched_keywords"]
    assert "kubernetes" in result["missing_keywords"]
    assert "aws" in result["missing_keywords"]
    assert "looking" not in result["missing_keywords"]
    assert "candidate" not in result["missing_keywords"]
    assert "experience" not in result["missing_keywords"]
    assert "need" not in result["missing_keywords"]
    assert result["explanation"]["keyword_details"]["required_terms_count"] >= 4
    assert result["explanation"]["score_band"]["label"] in {"weak", "moderate", "strong"}


def test_keyword_overlap_normalizes_common_skill_aliases():
    matcher = ResumeMatcherService(load_embedding_model=False)
    resume = "Built REST API services with PostgreSQL and Python"
    jd = "Need Python, Postgres, and RESTful API experience"

    result = matcher.match(resume, jd)

    assert "python" in result["matched_keywords"]
    assert "postgresql" in result["matched_keywords"]
    assert "rest api" in result["matched_keywords"]
    assert "need" not in result["missing_keywords"]

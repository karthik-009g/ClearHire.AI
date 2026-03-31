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

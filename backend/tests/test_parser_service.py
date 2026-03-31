from app.services.parser_service import ResumeParserService


def test_parse_resume_sections_and_skills():
    parser = ResumeParserService()
    text = """
    Skills
    Python, FastAPI, PostgreSQL

    Experience
    3 years building APIs for fintech workflows.

    Projects
    Job Matching Platform
    """

    parsed = parser.parse_resume(text)

    assert "skills" in parsed
    assert "experience" in parsed["sections"]
    assert "projects" in parsed["sections"]
    assert any(skill in parsed["skills"] for skill in ["python", "fastapi", "postgresql"])

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


def test_parse_student_resume_counts_projects_and_sets_zero_without_experience_section():
    parser = ResumeParserService()
    text = """
    Kartik Gubba

    SUMMARY
    Aspiring AI Engineer with hands-on experience in machine learning, data analytics, and building AI-powered applications.

    SKILLS
    Programming Python, SQL, Java
    Frameworks & Libraries Scikit-learn, Pandas, NumPy, FastAPI, LangChain
    Databases MySQL, PostgreSQL, Vector Databases (Pinecone)
    Tools Git, GitHub, Jupyter Notebook, Streamlit

    EDUCATION
    2023 - 2027 B.Tech in Computer Science

    PROJECTS
    ClearHire.AI - RAG-based Resume Intelligence & Job Matching System GitHub
    - Developed an AI-powered platform to match resumes with relevant job opportunities.
    Telecom Churn Prediction (Machine Learning System) GitHub
    - Built classification models to predict customer churn.
    Industrial Equipment Analytics System (Data Pipeline + BI) GitHub
    - Built an end-to-end data analytics pipeline.
    """

    parsed = parser.parse_resume(text)

    assert parsed["experience_years_estimate"] == 0
    assert parsed["projects_count_estimate"] >= 3
    assert any(skill in parsed["skills"] for skill in ["python", "langchain", "fastapi", "postgresql", "streamlit"])
    assert len(parsed["sections"]["projects"]) >= 5


def test_parse_wrapped_pdf_text_counts_project_titles_correctly():
    parser = ResumeParserService()
    text = """
    Summary
    Aspiring AI Engineer with hands-on experience in machine learning.

    Skills
    Programming Python, SQL, Java
    Frameworks & Libraries Scikit-learn, Pandas, NumPy, FastAPI , LangChain , Hugging Face
    Data & Analytics EDA, Data Visualization, Power BI
    Databases MySQL, PostgreSQL, Vector Databases (Pinecone)
    Tools Git, GitHub, Jupyter Notebook, Streamlit
    Education
    2023 - 2027 B.Tech in Computer Science

    Projects
    ClearHire.AI - RAG-based Resume Intelligence & Job Matching SystemGitHub
    •Developed an AI-powered platform to match resumes with relevant job opportunities using semantic search
    and LLMs
    Telecom Churn Prediction (Machine Learning System)GitHub
    •Built classification models to predict customer churn using feature engineering
    Industrial Equipment Analytics System (Data Pipeline + BI)GitHub
    •Built an end-to-end data analytics pipeline
    """

    parsed = parser.parse_resume(text)

    assert "Education" not in parsed["sections"]["skills"]
    assert parsed["projects_count_estimate"] == 3
    assert parsed["experience_years_estimate"] == 0


def test_extract_skills_from_section_lines_beyond_static_keywords():
    parser = ResumeParserService()
    text = """
    Skills
    Programming Python, SQL, Java
    AI/ML & Deep Learning Machine Learning, Model Evaluation, Feature Engineering
    Data & Analytics EDA, Data Cleaning, Data Visualization, KPI reporting
    Tools Git, GitHub, Jupyter Notebook, Anaconda, Streamlit
    """

    parsed = parser.parse_resume(text)

    assert "anaconda" in parsed["skills"]
    assert "model evaluation" in parsed["skills"]
    assert "feature engineering" in parsed["skills"]
    assert "data cleaning" in parsed["skills"]


def test_normalize_extracted_text_merges_wrapped_lines_and_hyphen_breaks():
    raw = """
    Projects
    •Built a data preprocessing tech-
    niques pipeline
    and validated outputs
    """

    normalized = ResumeParserService._normalize_extracted_text(raw)

    assert "techniques pipeline and validated outputs" in normalized

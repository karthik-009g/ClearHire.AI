from __future__ import annotations

import io
from PyPDF2 import PdfReader

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import resumes
from app.database import Base, get_db
from app.services.pdf_generator_service import PdfGeneratorService
from app.utils.config import settings


def test_pdf_generator_service_compiles_valid_ats_pdf():
    service = PdfGeneratorService()

    sample_resume = """
## TECHNICAL SKILLS
Languages: Python, Go, TypeScript, SQL
Frameworks: FastAPI, React, Docker, Kubernetes, PostgreSQL, Redis

## EXPERIENCE
Senior Software Engineer - Razorpay (2023 - Present)
- Designed and built distributed payment webhook gateway handling 15,000 req/sec.
- Optimized database indexing and query plans, reducing p99 latency by 35%.
- Implemented automated circuit breakers and retry policies for downstream bank gateways.

Software Engineer - InMobi (2021 - 2023)
- Built ad-targeting pipeline in Python and Kafka processing 50M events daily.
- Integrated automated Prometheus monitoring and Grafana alerting dashboards.

## EDUCATION
B.Tech in Computer Science - NIT Karnataka (2017 - 2021)
    """

    pdf_bytes = service.generate_ats_pdf(
        resume_text=sample_resume,
        candidate_name="Alex Sharma",
        contact_line="Email: alex@clearhire.ai | Bengaluru, India | LinkedIn: alexsharma",
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000

    # Verify that the PDF is readable and contains the text stream
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1  # 1-page budget guarantee

    extracted_text = "".join(page.extract_text() for page in reader.pages)
    assert "Alex Sharma" in extracted_text
    assert "Razorpay" in extracted_text
    assert "FastAPI" in extracted_text or "Python" in extracted_text


def test_export_pdf_endpoint():
    app = FastAPI()
    app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
    client = TestClient(app)

    response = client.post(
        "/api/resumes/export-pdf",
        json={
            "resume_text": "## SKILLS\nPython, FastAPI, SQL\n\n## EXPERIENCE\nBuilt web app with 99.9% uptime.",
            "candidate_name": "Priya Verma",
            "contact_line": "priya@example.com | Hyderabad",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")

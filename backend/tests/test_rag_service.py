from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import JobPosting, Resume, ResumeVersion
from app.services.matcher_service import ResumeMatcherService
from app.services.rag_service import ReconciledRAGService


def _build_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def _seed_resume(db) -> tuple[Resume, ResumeVersion]:
    resume = Resume(
        user_id=None,
        original_filename="resume.docx",
        stored_path="storage/resumes/test.docx",
        content_hash="hash",
        parsed_summary={"skills": ["python", "fastapi", "postgresql"]},
        expires_at=datetime.utcnow() + timedelta(days=10),
    )
    db.add(resume)
    db.flush()

    matcher = ResumeMatcherService(load_embedding_model=False)
    text = "Python FastAPI PostgreSQL backend engineer with APIs and deployment experience"
    embedding = matcher.embed_text(text)
    version = ResumeVersion(
        resume_id=resume.id,
        version_no=1,
        content_text=text,
        embedding=embedding,
        embedding_vector=embedding,
    )
    db.add(version)
    db.commit()
    db.refresh(resume)
    db.refresh(version)
    return resume, version


def test_rag_service_abstains_when_no_evidence():
    db = _build_session()
    resume, version = _seed_resume(db)
    service = ReconciledRAGService(matcher_service=ResumeMatcherService(load_embedding_model=False))

    result = service.run_reconciled_match(
        db=db,
        resume=resume,
        resume_version=version,
        jd_text="Looking for Golang networking engineer with distributed systems and kernel experience",
        requested_title="Backend Engineer",
        requested_company="Acme",
    )

    assert result["abstained"] is True
    assert result["status"] == "no_match"
    assert result["abstain_reason"] == "No strong match found"


def test_rag_service_marks_conflicting_evidence_as_ambiguous():
    db = _build_session()
    resume, version = _seed_resume(db)
    matcher = ResumeMatcherService(load_embedding_model=False)
    service = ReconciledRAGService(matcher_service=matcher)

    common_text = "Python FastAPI PostgreSQL backend engineer building scalable APIs"
    embedding = matcher.embed_text(common_text)
    db.add(
        JobPosting(
            source="naukri",
            company="Alpha",
            title="Backend Engineer",
            location="Remote",
            url="https://jobs.example/alpha",
            description=common_text,
            embedding=embedding,
            embedding_vector=embedding,
            scraped_at=datetime.utcnow(),
        )
    )
    db.add(
        JobPosting(
            source="linkedin",
            company="Beta",
            title="Backend Engineer",
            location="Remote",
            url="https://jobs.example/beta",
            description=common_text,
            embedding=embedding,
            embedding_vector=embedding,
            scraped_at=datetime.utcnow(),
        )
    )
    db.commit()

    result = service.run_reconciled_match(
        db=db,
        resume=resume,
        resume_version=version,
        jd_text=common_text,
        requested_title="Backend Engineer",
        requested_company="Gamma",
        top_k=5,
    )

    assert result["abstained"] is True
    assert result["status"] == "ambiguous"
    assert result["abstain_reason"] == "Ambiguous match, needs review"


def test_rag_service_abstains_when_skill_evidence_is_too_thin():
    db = _build_session()
    resume, version = _seed_resume(db)
    matcher = ResumeMatcherService(load_embedding_model=False)
    service = ReconciledRAGService(matcher_service=matcher)

    thin_skill_text = "Python backend engineer building APIs and production deployments"
    embedding = matcher.embed_text(thin_skill_text)
    db.add(
        JobPosting(
            source="linkedin",
            company="Acme",
            title="Backend Engineer",
            location="Remote",
            url="https://jobs.example/backend",
            description=thin_skill_text,
            embedding=embedding,
            embedding_vector=embedding,
            scraped_at=datetime.utcnow(),
        )
    )
    db.commit()

    result = service.run_reconciled_match(
        db=db,
        resume=resume,
        resume_version=version,
        jd_text=thin_skill_text,
        requested_title="Backend Engineer",
        requested_company="Acme",
        top_k=3,
    )

    assert result["abstained"] is True
    assert result["status"] == "insufficient_skill_evidence"
    assert result["abstain_reason"] == "Insufficient skill evidence, needs review"
    assert result["skill_overlap"] == ["python"]
    assert result["evidence_quality"]["min_skill_overlap_ratio"] == 0.5
    assert result["reconciliation_reasons"] == ["skill_overlap_below_threshold"]

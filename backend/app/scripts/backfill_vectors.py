"""Backfill embedding vectors for retrieval-ready columns."""

from __future__ import annotations

from dataclasses import dataclass

from app.database import SessionLocal
from app.models import JobDescription, JobPosting, ResumeVersion
from app.services.matcher_service import ResumeMatcherService
from app.utils.config import settings


@dataclass
class BackfillSummary:
    updated_resume_versions: int = 0
    updated_job_descriptions: int = 0
    updated_job_postings: int = 0
    dimension_mismatches: int = 0


def _valid_dimension(vector: list[float] | None, expected_dimension: int) -> bool:
    return vector is not None and len(vector) == expected_dimension


def run_backfill() -> BackfillSummary:
    db = SessionLocal()
    matcher = ResumeMatcherService(embedding_model_name=settings.embedding_model_name)
    runtime_dimension = len(matcher.embed_text("dimension-probe"))
    summary = BackfillSummary()

    resume_versions = db.query(ResumeVersion).all()
    for row in resume_versions:
        vector = row.embedding
        if not _valid_dimension(vector, runtime_dimension):
            vector = matcher.embed_text(row.content_text)
            row.embedding = vector

        if _valid_dimension(vector, runtime_dimension):
            row.embedding_vector = vector
            summary.updated_resume_versions += 1
        else:
            summary.dimension_mismatches += 1

    job_descriptions = db.query(JobDescription).all()
    for row in job_descriptions:
        vector = row.embedding_vector
        if not _valid_dimension(vector, runtime_dimension):
            vector = matcher.embed_text(row.jd_text)

        if _valid_dimension(vector, runtime_dimension):
            row.embedding_vector = vector
            summary.updated_job_descriptions += 1
        else:
            summary.dimension_mismatches += 1

    job_postings = db.query(JobPosting).all()
    for row in job_postings:
        vector = row.embedding_vector or row.embedding
        if not _valid_dimension(vector, runtime_dimension):
            vector = matcher.embed_text(f"{row.title}\n{row.description or ''}")
            row.embedding = vector

        if _valid_dimension(vector, runtime_dimension):
            row.embedding_vector = vector
            summary.updated_job_postings += 1
        else:
            summary.dimension_mismatches += 1

    db.commit()
    db.close()
    return summary


def main() -> None:
    summary = run_backfill()
    print("Vector backfill complete")
    print(
        {
            "updated_resume_versions": summary.updated_resume_versions,
            "updated_job_descriptions": summary.updated_job_descriptions,
            "updated_job_postings": summary.updated_job_postings,
            "dimension_mismatches": summary.dimension_mismatches,
        }
    )


if __name__ == "__main__":
    main()

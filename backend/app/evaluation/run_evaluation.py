"""Run reconciled RAG evaluation over a labeled dataset."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.evaluation.metrics import compute_metrics
from app.models import JobPosting, Resume, ResumeVersion
from app.services.matcher_service import ResumeMatcherService
from app.services.rag_service import ReconciledRAGService


def _tokenize(text_value: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z][a-zA-Z\+\#\.-]{1,}", text_value.lower()))


def _build_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def _seed_jobs(db, jobs: list[dict[str, Any]], in_scope_ids: list[int], matcher: ResumeMatcherService) -> None:
    if not in_scope_ids:
        return

    selected = [job for job in jobs if int(job["id"]) in set(in_scope_ids)]
    for item in selected:
        embedding = matcher.embed_text(f"{item['title']}\n{item['description']}")
        db.add(
            JobPosting(
                id=int(item["id"]),
                source=item.get("source", "seed"),
                company=item["company"],
                title=item["title"],
                location=item.get("location"),
                url=item.get("url", f"https://example.com/jobs/{item['id']}"),
                description=item["description"],
                embedding=embedding,
                embedding_vector=embedding,
                scraped_at=datetime.utcnow(),
            )
        )
    db.commit()


def _seed_resume(db, sample: dict[str, Any], matcher: ResumeMatcherService) -> tuple[Resume, ResumeVersion]:
    resume = Resume(
        user_id=None,
        original_filename=f"{sample['sample_id']}.txt",
        stored_path=f"storage/resumes/{sample['sample_id']}.txt",
        content_hash=sample["sample_id"],
        parsed_summary={"skills": sample.get("resume_skills", [])},
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(resume)
    db.flush()

    embedding = matcher.embed_text(sample["resume_text"])
    version = ResumeVersion(
        resume_id=resume.id,
        version_no=1,
        content_text=sample["resume_text"],
        embedding=embedding,
        embedding_vector=embedding,
    )
    db.add(version)
    db.commit()
    db.refresh(resume)
    db.refresh(version)
    return resume, version


def _precision_at_k(evidence: list[dict[str, Any]], relevant_ids: list[int], top_k: int) -> float:
    if top_k <= 0:
        return 0.0

    relevant = set(int(value) for value in relevant_ids)
    posting_ids = [
        int(item["source_id"])
        for item in evidence
        if item.get("source_table") == "job_postings"
    ][:top_k]

    if not relevant:
        return 1.0 if not posting_ids else 0.0

    hits = sum(1 for item_id in posting_ids if item_id in relevant)
    return round(hits / top_k, 4)


def _hallucinated(answer: str | None, context_text: str, monitored_terms: set[str]) -> bool:
    if not answer:
        return False

    answer_terms = _tokenize(answer)
    context_terms = _tokenize(context_text)
    mentioned_monitored = {term for term in answer_terms if term in monitored_terms}
    unsupported = [term for term in mentioned_monitored if term not in context_terms]
    return len(unsupported) > 0


def run(dataset_path: Path, output_path: Path, print_samples: bool) -> dict[str, Any]:
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    jobs = payload["jobs"]
    samples = payload["samples"]
    top_k = int(payload.get("top_k", 5))
    monitored_terms = set(payload.get("hallucination_terms", []))

    matcher = ResumeMatcherService()
    matcher.model = None
    service = ReconciledRAGService(matcher_service=matcher)

    records: list[dict[str, Any]] = []
    for sample in samples:
        db = _build_session()
        scope_ids = sample.get("job_ids_in_scope")
        if scope_ids is None:
            scope_ids = [int(job["id"]) for job in jobs]

        _seed_jobs(db, jobs, scope_ids, matcher)
        resume, version = _seed_resume(db, sample, matcher)

        result = service.run_reconciled_match(
            db=db,
            resume=resume,
            resume_version=version,
            jd_text=sample["jd_text"],
            requested_title=sample.get("title"),
            requested_company=sample.get("company"),
            top_k=top_k,
        )

        evidence = result["evidence"]
        context_text = "\n".join([
            sample["resume_text"],
            sample["jd_text"],
            " ".join(item.get("snippet", "") for item in evidence),
            " ".join((item.get("title") or "") for item in evidence),
            " ".join((item.get("company") or "") for item in evidence),
        ])

        precision = _precision_at_k(evidence, sample.get("relevant_job_ids", []), top_k)
        hallucinated = _hallucinated(result.get("answer"), context_text, monitored_terms)

        record = {
            "sample_id": sample["sample_id"],
            "expected_status": sample["expected_status"],
            "predicted_status": result["status"],
            "is_correct": result["status"] == sample["expected_status"],
            "precision_at_k": precision,
            "abstained": bool(result["abstained"]),
            "hallucinated": hallucinated,
            "latency_ms": int(result["latency_ms"]),
            "retrieval_score": result.get("retrieval_score"),
            "confidence": result.get("confidence"),
        }
        records.append(record)
        db.close()

    metrics = compute_metrics(records)
    report = {
        "dataset": str(dataset_path),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sample_count": len(records),
        "top_k": top_k,
        "metrics": metrics,
        "records": records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Evaluation complete")
    print(json.dumps(metrics, indent=2))
    if print_samples:
        print(json.dumps(records, indent=2))

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reconciled RAG evaluation")
    parser.add_argument(
        "--dataset",
        default="app/evaluation/datasets/reconciled_match_eval_20.json",
        help="Path to evaluation dataset JSON",
    )
    parser.add_argument(
        "--output",
        default="app/evaluation/reports/latest_metrics.json",
        help="Path for output metrics report JSON",
    )
    parser.add_argument(
        "--print-samples",
        action="store_true",
        help="Print per-sample records in addition to aggregate metrics",
    )

    args = parser.parse_args()
    run(Path(args.dataset), Path(args.output), print_samples=args.print_samples)


if __name__ == "__main__":
    main()

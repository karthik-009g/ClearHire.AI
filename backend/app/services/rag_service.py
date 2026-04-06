"""RAG retrieval + truth reconciliation service for resume matching."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from time import perf_counter
import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import JobDescription, JobPosting, MatchResult, Resume, ResumeVersion
from app.services.matcher_service import ResumeMatcherService
from app.utils.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievedEvidence:
    source_table: str
    source_id: int
    title: str | None
    company: str | None
    similarity: float
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_table": self.source_table,
            "source_id": self.source_id,
            "title": self.title,
            "company": self.company,
            "similarity": round(self.similarity, 4),
            "snippet": self.snippet,
        }


class ReconciledRAGService:
    def __init__(self, matcher_service: ResumeMatcherService | None = None) -> None:
        self.matcher = matcher_service or ResumeMatcherService(embedding_model_name=settings.embedding_model_name)

    @staticmethod
    def _vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"

    @staticmethod
    def _snippet(text_value: str | None, max_len: int = 260) -> str:
        compact = re.sub(r"\s+", " ", (text_value or "")).strip()
        if len(compact) <= max_len:
            return compact
        return compact[: max_len - 3] + "..."

    @staticmethod
    def _skills_from_resume(resume: Resume) -> list[str]:
        summary = resume.parsed_summary if isinstance(resume.parsed_summary, dict) else {}
        skills = summary.get("skills", [])
        return [str(skill).strip().lower() for skill in skills if str(skill).strip()]

    @staticmethod
    def _extract_resume_evidence_lines(resume_text: str, skills: list[str], limit: int = 5) -> list[str]:
        if not skills:
            return []

        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        highlights: list[str] = []
        for line in lines:
            line_l = line.lower()
            if any(skill in line_l for skill in skills):
                highlights.append(line)
            if len(highlights) >= limit:
                break
        return highlights

    def _retrieve_job_postings(
        self,
        db: Session,
        query_embedding: list[float],
        limit: int,
    ) -> list[RetrievedEvidence]:
        is_pg = db.bind is not None and db.bind.dialect.name == "postgresql"
        if settings.rag_enable_pgvector and is_pg:
            query = text(
                """
                SELECT id, title, company, description,
                       (1 - (embedding_vector <=> CAST(:query_vector AS vector))) AS similarity
                FROM job_postings
                WHERE embedding_vector IS NOT NULL
                ORDER BY embedding_vector <=> CAST(:query_vector AS vector)
                LIMIT :k
                """
            )
            rows = db.execute(
                query,
                {"query_vector": self._vector_literal(query_embedding), "k": limit},
            ).mappings()
            return [
                RetrievedEvidence(
                    source_table="job_postings",
                    source_id=int(row["id"]),
                    title=row["title"],
                    company=row["company"],
                    similarity=max(0.0, float(row["similarity"] or 0.0)),
                    snippet=self._snippet(row["description"]),
                )
                for row in rows
            ]

        rows = (
            db.query(JobPosting)
            .order_by(JobPosting.scraped_at.desc())
            .limit(max(limit * 20, 100))
            .all()
        )
        scored: list[RetrievedEvidence] = []
        for row in rows:
            candidate_embedding = row.embedding_vector or row.embedding
            if not candidate_embedding:
                continue
            if len(candidate_embedding) != len(query_embedding):
                continue
            similarity = self.matcher.cosine_similarity(query_embedding, candidate_embedding)
            normalized = max(0.0, min(1.0, (similarity + 1.0) / 2.0))
            scored.append(
                RetrievedEvidence(
                    source_table="job_postings",
                    source_id=row.id,
                    title=row.title,
                    company=row.company,
                    similarity=normalized,
                    snippet=self._snippet(row.description),
                )
            )

        return sorted(scored, key=lambda item: item.similarity, reverse=True)[:limit]

    def _retrieve_job_descriptions(
        self,
        db: Session,
        query_embedding: list[float],
        limit: int,
    ) -> list[RetrievedEvidence]:
        is_pg = db.bind is not None and db.bind.dialect.name == "postgresql"
        if settings.rag_enable_pgvector and is_pg:
            query = text(
                """
                SELECT id, title, company, jd_text,
                       (1 - (embedding_vector <=> CAST(:query_vector AS vector))) AS similarity
                FROM job_descriptions
                WHERE embedding_vector IS NOT NULL
                ORDER BY embedding_vector <=> CAST(:query_vector AS vector)
                LIMIT :k
                """
            )
            rows = db.execute(
                query,
                {"query_vector": self._vector_literal(query_embedding), "k": limit},
            ).mappings()
            return [
                RetrievedEvidence(
                    source_table="job_descriptions",
                    source_id=int(row["id"]),
                    title=row["title"],
                    company=row["company"],
                    similarity=max(0.0, float(row["similarity"] or 0.0)),
                    snippet=self._snippet(row["jd_text"]),
                )
                for row in rows
            ]

        rows = (
            db.query(JobDescription)
            .order_by(JobDescription.created_at.desc())
            .limit(max(limit * 20, 100))
            .all()
        )
        scored: list[RetrievedEvidence] = []
        for row in rows:
            candidate_embedding = row.embedding_vector
            if not candidate_embedding:
                continue
            if len(candidate_embedding) != len(query_embedding):
                continue
            similarity = self.matcher.cosine_similarity(query_embedding, candidate_embedding)
            normalized = max(0.0, min(1.0, (similarity + 1.0) / 2.0))
            scored.append(
                RetrievedEvidence(
                    source_table="job_descriptions",
                    source_id=row.id,
                    title=row.title,
                    company=row.company,
                    similarity=normalized,
                    snippet=self._snippet(row.jd_text),
                )
            )

        return sorted(scored, key=lambda item: item.similarity, reverse=True)[:limit]

    def _retrieve_past_matches(
        self,
        db: Session,
        resume_id: str,
        limit: int,
    ) -> list[RetrievedEvidence]:
        rows = (
            db.query(MatchResult)
            .filter(MatchResult.resume_id == resume_id)
            .order_by(MatchResult.total_score.desc())
            .limit(limit)
            .all()
        )

        evidence: list[RetrievedEvidence] = []
        for row in rows:
            snippet_payload = {
                "gaps": row.gaps,
                "explanation": row.explanation,
            }
            evidence.append(
                RetrievedEvidence(
                    source_table="match_results",
                    source_id=row.id,
                    title=row.job_description.title if row.job_description else None,
                    company=row.job_description.company if row.job_description else None,
                    similarity=max(0.0, min(1.0, row.total_score / 100.0)),
                    snippet=self._snippet(json.dumps(snippet_payload, default=str)),
                )
            )
        return evidence

    def retrieve(
        self,
        db: Session,
        resume_id: str,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievedEvidence]:
        candidates: list[RetrievedEvidence] = []
        candidates.extend(self._retrieve_job_postings(db, query_embedding, top_k))
        candidates.extend(self._retrieve_job_descriptions(db, query_embedding, top_k))
        candidates.extend(self._retrieve_past_matches(db, resume_id, top_k))

        ranked = sorted(candidates, key=lambda item: item.similarity, reverse=True)
        return ranked[:top_k]

    @staticmethod
    def _has_conflicting_top_evidence(
        evidence: list[RetrievedEvidence],
        requested_company: str | None,
        requested_title: str | None,
    ) -> bool:
        if len(evidence) < 2:
            return False

        top_two = evidence[:2]
        margin = abs(top_two[0].similarity - top_two[1].similarity)
        if margin > 0.03:
            return False

        if requested_company:
            requested_company_l = requested_company.strip().lower()
            top_companies = [
                item.company.strip().lower()
                for item in top_two
                if item.company and item.company.strip()
            ]
            if requested_company_l in top_companies:
                return False
            return len(set(top_companies)) > 1

        if requested_title:
            requested_title_l = requested_title.strip().lower()
            top_titles = [
                item.title.strip().lower()
                for item in top_two
                if item.title and item.title.strip()
            ]
            if any(requested_title_l in title for title in top_titles):
                return False
            return len(set(top_titles)) > 1

        return False

    def _reconcile(
        self,
        match_data: dict[str, Any],
        evidence: list[RetrievedEvidence],
        resume_skills: list[str],
        requested_title: str | None,
        requested_company: str | None,
    ) -> dict[str, Any]:
        if not evidence:
            return {
                "status": "no_match",
                "abstained": True,
                "abstain_reason": "No strong match found",
                "confidence": 0.0,
                "skill_overlap": [],
                "skill_overlap_ratio": 0.0,
            }

        top_similarity = evidence[0].similarity
        if top_similarity < settings.rag_similarity_threshold:
            return {
                "status": "no_match",
                "abstained": True,
                "abstain_reason": "No strong match found",
                "confidence": round(top_similarity, 4),
                "skill_overlap": [],
                "skill_overlap_ratio": 0.0,
            }

        if self._has_conflicting_top_evidence(
            evidence=evidence,
            requested_company=requested_company,
            requested_title=requested_title,
        ):
            return {
                "status": "ambiguous",
                "abstained": True,
                "abstain_reason": "Ambiguous match, needs review",
                "confidence": round(top_similarity, 4),
                "skill_overlap": [],
                "skill_overlap_ratio": 0.0,
            }

        evidence_text = " ".join(item.snippet.lower() for item in evidence)
        matched_skills = [skill for skill in resume_skills if skill in evidence_text]
        overlap_ratio = len(matched_skills) / max(1, len(resume_skills))

        title_bonus = 0.0
        if requested_title:
            title_l = requested_title.lower()
            if any((item.title or "").lower().find(title_l) >= 0 for item in evidence):
                title_bonus = 0.1

        company_penalty = 0.0
        if requested_company:
            company_l = requested_company.lower()
            if not any((item.company or "").lower() == company_l for item in evidence):
                company_penalty = 0.1

        confidence = (
            (0.55 * top_similarity)
            + (0.25 * (match_data["total_score"] / 100.0))
            + (0.20 * overlap_ratio)
            + title_bonus
            - company_penalty
        )
        confidence = max(0.0, min(1.0, confidence))

        if confidence < settings.rag_abstain_threshold:
            return {
                "status": "low_confidence",
                "abstained": True,
                "abstain_reason": "Low confidence, abstaining",
                "confidence": round(confidence, 4),
                "skill_overlap": matched_skills,
                "skill_overlap_ratio": round(overlap_ratio, 4),
            }

        return {
            "status": "valid",
            "abstained": False,
            "abstain_reason": None,
            "confidence": round(confidence, 4),
            "skill_overlap": matched_skills,
            "skill_overlap_ratio": round(overlap_ratio, 4),
        }

    def _generate_grounded_answer(
        self,
        jd_text: str,
        match_data: dict[str, Any],
        evidence: list[RetrievedEvidence],
        reconciliation: dict[str, Any],
    ) -> str | None:
        if reconciliation["abstained"]:
            return None

        evidence_lines = [
            f"- [{item.source_table}:{item.source_id}] {item.title or 'Untitled'} | {item.company or 'Unknown'} | sim={item.similarity:.3f}"
            for item in evidence
        ]

        if settings.llm_provider.lower() == "groq" and settings.groq_api_key:
            try:
                from groq import Groq

                client = Groq(api_key=settings.groq_api_key)
                completion = client.chat.completions.create(
                    model=settings.groq_model,
                    temperature=0.1,
                    max_tokens=400,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a strict retrieval-grounded assistant. "
                                "DO NOT hallucinate skills. ONLY use provided context. "
                                "If uncertain, say: Not enough info."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"JD:\n{jd_text}\n\n"
                                f"Match scores: keyword={match_data['keyword_score']}, "
                                f"embedding={match_data['embedding_score']}, total={match_data['total_score']}\n\n"
                                "Retrieved evidence:\n"
                                + "\n".join(evidence_lines)
                                + "\n\nProvide a concise matching rationale in 3 bullets."
                            ),
                        },
                    ],
                )
                content = completion.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as exc:
                logger.warning("groq_generation_failed error=%s", exc)

        top = evidence[0]
        return (
            "Grounded match summary:\n"
            f"1) Top evidence: {top.title or 'Untitled'} at {top.company or 'Unknown'} with similarity {top.similarity:.3f}.\n"
            f"2) Resume-to-JD total score is {match_data['total_score']:.2f}.\n"
            "3) Evidence is consistent enough for a tentative recommendation."
        )

    def run_reconciled_match(
        self,
        db: Session,
        resume: Resume,
        resume_version: ResumeVersion,
        jd_text: str,
        requested_title: str | None = None,
        requested_company: str | None = None,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        started = perf_counter()

        top_k_value = top_k or settings.rag_top_k
        top_k_value = max(1, min(20, top_k_value))

        match_data = self.matcher.match(resume_version.content_text, jd_text)
        query_embedding = self.matcher.embed_text(jd_text)
        evidence = self.retrieve(db=db, resume_id=resume.id, query_embedding=query_embedding, top_k=top_k_value)

        resume_skills = self._skills_from_resume(resume)
        reconciliation = self._reconcile(
            match_data=match_data,
            evidence=evidence,
            resume_skills=resume_skills,
            requested_title=requested_title,
            requested_company=requested_company,
        )

        answer = self._generate_grounded_answer(
            jd_text=jd_text,
            match_data=match_data,
            evidence=evidence,
            reconciliation=reconciliation,
        )

        latency_ms = int((perf_counter() - started) * 1000)
        retrieval_score = round(evidence[0].similarity, 4) if evidence else None
        evidence_payload = [item.to_dict() for item in evidence]

        result = {
            "status": reconciliation["status"],
            "abstained": reconciliation["abstained"],
            "abstain_reason": reconciliation["abstain_reason"],
            "confidence": reconciliation["confidence"],
            "retrieval_score": retrieval_score,
            "retrieval_top_k": top_k_value,
            "match": match_data,
            "answer": answer,
            "evidence": evidence_payload,
            "latency_ms": latency_ms,
            "skill_overlap": reconciliation["skill_overlap"],
            "skill_overlap_ratio": reconciliation["skill_overlap_ratio"],
            "resume_evidence_lines": self._extract_resume_evidence_lines(
                resume_version.content_text,
                reconciliation["skill_overlap"],
            ),
        }

        logger.info(
            "rag_reconciled_match status=%s retrieval_score=%s confidence=%s abstained=%s latency_ms=%d evidence_count=%d",
            result["status"],
            result["retrieval_score"],
            result["confidence"],
            result["abstained"],
            result["latency_ms"],
            len(evidence_payload),
        )
        return result
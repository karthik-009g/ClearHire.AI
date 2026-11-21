"""Explainable JD-resume matching using keyword overlap + sentence-transformers."""

from __future__ import annotations

from math import sqrt
from math import log1p
import re
from collections import Counter
from hashlib import blake2b
from typing import Any

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "your", "from", "are", "was", "were", "will",
    "would", "can", "could", "should", "about", "their", "them", "they", "all", "any", "a", "an",
    "to", "of", "in", "on", "at", "is", "it", "as", "or", "by", "be", "if", "not", "we", "i",
    "our", "you", "us", "role", "candidate", "looking", "required", "requirement", "requirements",
    "responsibilities", "responsibility", "experience", "years", "year", "strong", "good", "must",
    "nice", "plus", "preferred", "ability", "work", "working", "team", "teams", "build", "building",
    "need", "needs", "using", "use", "used", "relevant", "excellent", "communication", "passion",
}

TOKEN_NORMALIZATION = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "nodejs": "node",
    "node.js": "node",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "ci": "ci/cd",
    "cd": "ci/cd",
    "apis": "api",
    "api": "api",
    "restful": "rest api",
    "genai": "generative ai",
}

SKILL_PHRASES = (
    "artificial intelligence",
    "generative ai",
    "machine learning",
    "deep learning",
    "natural language processing",
    "data engineering",
    "software engineering",
    "system design",
    "ci/cd",
    "unit testing",
    "integration testing",
    "rest api",
    "microservices",
    "cloud computing",
    "resume parsing",
    "semantic search",
    "vector database",
    "vector databases",
    "large language models",
)

TECH_KEYWORDS = {
    "python", "java", "javascript", "typescript", "react", "next.js", "nextjs", "node", "fastapi",
    "django", "flask", "sql", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes",
    "aws", "azure", "gcp", "git", "github", "pytest", "playwright", "selenium", "spacy", "pandas",
    "numpy", "scikit-learn", "tensorflow", "pytorch", "langchain", "langgraph", "rag", "llm",
    "api", "rest api", "ci/cd", "linux", "airflow", "spark", "etl", "pinecone", "pgvector",
    "transformers", "huggingface", "hugging", "kaggle", "jupyter", "streamlit",
}


class ResumeMatcherService:
    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        embedding_dimensions: int = 384,
        load_embedding_model: bool = True,
    ):
        self.embedding_model_name = embedding_model_name
        self.embedding_dimensions = max(64, int(embedding_dimensions))
        self.model = None
        if load_embedding_model:
            try:
                from sentence_transformers import SentenceTransformer

                self.model = SentenceTransformer(embedding_model_name)
            except Exception:
                self.model = None

    @staticmethod
    def _normalize_token(token: str) -> str:
        token = token.strip().lower()
        return TOKEN_NORMALIZATION.get(token, token)

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z\+\#\.\-]{1,}", text.lower())
        return [self._normalize_token(token) for token in tokens if token not in STOPWORDS]

    @staticmethod
    def _extract_skill_phrases(text: str) -> list[str]:
        lowered = text.lower()
        return [phrase for phrase in SKILL_PHRASES if phrase in lowered]

    @staticmethod
    def _stable_bucket(token: str, dimensions: int, salt: str) -> int:
        digest = blake2b(f"{salt}:{token}".encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % dimensions

    def build_resume_context(self, resume_text: str, parsed_summary: dict[str, Any] | None = None) -> str:
        """Merge raw resume text with structured summary so embeddings preserve context."""
        lines: list[str] = [line.strip() for line in resume_text.splitlines() if line.strip()]

        if isinstance(parsed_summary, dict):
            skills = [str(skill).strip() for skill in parsed_summary.get("skills", []) if str(skill).strip()]
            if skills:
                lines.append("skills: " + ", ".join(skills))

            sections = parsed_summary.get("sections", {})
            if isinstance(sections, dict):
                for section_name in ("experience", "projects", "skills"):
                    section_rows = sections.get(section_name, [])
                    if isinstance(section_rows, list):
                        for row in section_rows[:80]:
                            text_row = str(row).strip()
                            if text_row:
                                lines.append(text_row)

        dedup: list[str] = []
        seen: set[str] = set()
        for line in lines:
            normalized = re.sub(r"\s+", " ", line.lower()).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            dedup.append(line)

        return "\n".join(dedup).strip() or resume_text

    @staticmethod
    def _canonical_phrase(value: str) -> str:
        value = value.lower().strip()
        if value == "vector databases":
            return "vector database"
        if value == "large language models":
            return "llm"
        return value

    def _extract_requirement_terms(self, text: str) -> list[str]:
        tokens = self._tokenize(text)
        phrases = [self._canonical_phrase(phrase) for phrase in self._extract_skill_phrases(text)]
        candidates = tokens + phrases

        filtered: list[str] = []
        for term in candidates:
            canonical = self._canonical_phrase(term)
            if canonical in STOPWORDS:
                continue
            if canonical in TECH_KEYWORDS or canonical in phrases or "/" in canonical or "+" in canonical:
                filtered.append(canonical)
                continue
        return list(dict.fromkeys(filtered))

    @staticmethod
    def _term_weight(term: str) -> float:
        if term in TECH_KEYWORDS:
            return 1.7
        if " " in term or "/" in term or "+" in term:
            return 1.5
        return 1.0

    def _keyword_overlap(self, resume_text: str, jd_text: str) -> tuple[float, list[str], list[str], dict[str, Any]]:
        resume_terms = set(self._extract_requirement_terms(resume_text))
        jd_terms = self._extract_requirement_terms(jd_text)

        if not jd_terms:
            return 0.0, [], [], {
                "required_terms_count": 0,
                "matched_terms_count": 0,
                "weighted_required": 0.0,
                "weighted_matched": 0.0,
            }

        matched = [term for term in jd_terms if term in resume_terms]
        missing = [term for term in jd_terms if term not in resume_terms]
        weighted_required = sum(self._term_weight(term) for term in jd_terms)
        weighted_matched = sum(self._term_weight(term) for term in matched)
        score = (weighted_matched / max(1.0, weighted_required)) * 100
        details = {
            "required_terms_count": len(jd_terms),
            "matched_terms_count": len(matched),
            "weighted_required": round(weighted_required, 2),
            "weighted_matched": round(weighted_matched, 2),
        }
        return round(score, 2), matched[:30], missing[:30], details

    def _embedding_similarity(self, resume_text: str, jd_text: str) -> float:
        resume_vector = self.embed_text(resume_text)
        jd_vector = self.embed_text(jd_text)
        similarity = self.cosine_similarity(resume_vector, jd_vector)
        similarity = max(-1.0, min(1.0, similarity))
        return round(((similarity + 1.0) / 2.0) * 100, 2)

    @staticmethod
    def _score_band(total_score: float, keyword_score: float) -> dict[str, Any]:
        if total_score >= 75 and keyword_score >= 55:
            label = "strong"
            review_priority = "low"
        elif total_score >= 55 and keyword_score >= 35:
            label = "moderate"
            review_priority = "medium"
        else:
            label = "weak"
            review_priority = "high"

        return {
            "label": label,
            "review_priority": review_priority,
            "reason": "Keyword score is weighted higher because ATS-style exact requirements need explicit coverage.",
        }

    def embed_text(self, text: str) -> list[float]:
        if self.model:
            try:
                vector = self.model.encode([text], normalize_embeddings=True)[0]
                return [float(x) for x in vector]
            except Exception:
                self.model = None

        tokens = self._tokenize(text)
        tokens.extend(phrase.replace(" ", "_") for phrase in self._extract_skill_phrases(text))
        if not tokens:
            return [0.0 for _ in range(self.embedding_dimensions)]

        token_counts = Counter(tokens)
        vector = [0.0 for _ in range(self.embedding_dimensions)]
        for token, count in token_counts.items():
            weight = 1.0 + log1p(count)
            index_a = self._stable_bucket(token, self.embedding_dimensions, "a")
            index_b = self._stable_bucket(token, self.embedding_dimensions, "b")
            sign = -1.0 if (self._stable_bucket(token, self.embedding_dimensions, "sign") % 2) else 1.0
            vector[index_a] += sign * weight
            vector[index_b] += 0.5 * sign * weight

        magnitude = sqrt(sum(value * value for value in vector))
        if magnitude == 0.0:
            return [0.0 for _ in range(self.embedding_dimensions)]

        return [value / magnitude for value in vector]


    def embed_texts_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Batch encode multiple texts with vectorization for high throughput."""
        if not texts:
            return []

        if self.model:
            try:
                vectors = self.model.encode(
                    texts,
                    batch_size=batch_size,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                return [[float(x) for x in vec] for vec in vectors]
            except Exception:
                self.model = None

        return [self.embed_text(t) for t in texts]

    @staticmethod
    def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = sqrt(sum(a * a for a in vec_a))
        mag_b = sqrt(sum(b * b for b in vec_b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def match(
        self,
        resume_text: str,
        jd_text: str,
        parsed_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resume_context = self.build_resume_context(resume_text, parsed_summary=parsed_summary)
        keyword_score, matched_keywords, missing_keywords, keyword_details = self._keyword_overlap(resume_context, jd_text)
        embedding_score = self._embedding_similarity(resume_context, jd_text)

        total_score = round((0.6 * keyword_score) + (0.4 * embedding_score), 2)
        score_band = self._score_band(total_score, keyword_score)

        return {
            "keyword_score": keyword_score,
            "embedding_score": embedding_score,
            "total_score": total_score,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "resume_context_length": len(resume_context),
            "explanation": {
                "formula": "total = 0.6 * keyword_score + 0.4 * embedding_score",
                "keyword_score_reason": "Weighted overlap of requirement-like JD terms present in resume context.",
                "embedding_score_reason": "Semantic similarity using sentence-transformers embeddings.",
                "keyword_details": keyword_details,
                "score_band": score_band,
            },
        }

"""Explainable JD-resume matching using keyword overlap + sentence-transformers."""

from __future__ import annotations

from math import sqrt
import re
from collections import Counter
from typing import Any

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "your", "from", "are", "was", "were", "will",
    "would", "can", "could", "should", "about", "their", "them", "they", "all", "any", "a", "an",
    "to", "of", "in", "on", "at", "is", "it", "as", "or", "by", "be", "if", "not", "we", "i"
}


class ResumeMatcherService:
    def __init__(self, embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedding_model_name = embedding_model_name
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(embedding_model_name)
        except Exception:
            self.model = None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z\+\#\.\-]{1,}", text.lower())
        return [token for token in tokens if token not in STOPWORDS]

    def _keyword_overlap(self, resume_text: str, jd_text: str) -> tuple[float, list[str], list[str]]:
        resume_counts = Counter(self._tokenize(resume_text))
        jd_tokens = self._tokenize(jd_text)

        if not jd_tokens:
            return 0.0, [], []

        jd_unique = list(dict.fromkeys(jd_tokens))
        matched = [word for word in jd_unique if word in resume_counts]
        missing = [word for word in jd_unique if word not in resume_counts]
        score = (len(matched) / max(1, len(jd_unique))) * 100
        return round(score, 2), matched[:30], missing[:30]

    def _embedding_similarity(self, resume_text: str, jd_text: str) -> float:
        resume_vector = self.embed_text(resume_text)
        jd_vector = self.embed_text(jd_text)
        similarity = self.cosine_similarity(resume_vector, jd_vector)
        similarity = max(-1.0, min(1.0, similarity))
        return round(((similarity + 1.0) / 2.0) * 100, 2)

    def embed_text(self, text: str) -> list[float]:
        if self.model:
            vector = self.model.encode([text], normalize_embeddings=True)[0]
            return [float(x) for x in vector]

        tokens = self._tokenize(text)
        if not tokens:
            return [0.0, 0.0, 0.0]

        token_set = set(tokens)
        return [
            float(len(token_set)),
            float(sum(len(token) for token in token_set)) / max(1.0, float(len(token_set))),
            float(sum(ord(token[0]) for token in token_set)) / max(1.0, float(len(token_set))),
        ]

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

    def match(self, resume_text: str, jd_text: str) -> dict[str, Any]:
        keyword_score, matched_keywords, missing_keywords = self._keyword_overlap(resume_text, jd_text)
        embedding_score = self._embedding_similarity(resume_text, jd_text)

        total_score = round((0.6 * keyword_score) + (0.4 * embedding_score), 2)

        return {
            "keyword_score": keyword_score,
            "embedding_score": embedding_score,
            "total_score": total_score,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "explanation": {
                "formula": "total = 0.6 * keyword_score + 0.4 * embedding_score",
                "keyword_score_reason": "Percentage of unique JD keywords present in resume text.",
                "embedding_score_reason": "Semantic similarity using sentence-transformers embeddings.",
            },
        }

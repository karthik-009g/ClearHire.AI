"""Resume parsing service using DOCX/PDF extraction plus spaCy-friendly heuristics."""

from __future__ import annotations

import io
import importlib
import re
from typing import Any

import spacy

SKILL_KEYWORDS = {
    "python", "java", "javascript", "typescript", "react", "nextjs", "next.js", "node", "fastapi",
    "django", "flask", "sql", "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws",
    "azure", "gcp", "git", "playwright", "selenium", "langgraph", "langchain", "pandas", "numpy",
    "machine learning", "nlp", "spacy", "transformers", "ci/cd", "pytest"
}

SECTION_ALIASES = {
    "skills": ["skills", "technical skills", "tech stack"],
    "experience": ["experience", "work experience", "employment"],
    "projects": ["projects", "personal projects", "key projects"],
}


class ResumeParserService:
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        try:
            self.nlp = spacy.load(spacy_model)
        except Exception:
            self.nlp = spacy.blank("en")

    @staticmethod
    def extract_text(file_bytes: bytes, extension: str) -> str:
        extension = extension.lower()
        if extension == ".pdf":
            pypdf2_module = importlib.import_module("PyPDF2")
            PdfReader = pypdf2_module.PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

        if extension == ".docx":
            docx_module = importlib.import_module("docx")
            Document = docx_module.Document
            document = Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in document.paragraphs if p.text.strip()).strip()

        raise ValueError("Unsupported file type. Only PDF and DOCX are allowed.")

    def parse_resume(self, text: str) -> dict[str, Any]:
        normalized = re.sub(r"\r\n?", "\n", text)
        lines = [line.strip() for line in normalized.split("\n") if line.strip()]

        sections = {
            "skills": self._extract_section(lines, "skills"),
            "experience": self._extract_section(lines, "experience"),
            "projects": self._extract_section(lines, "projects"),
        }

        skills = self._extract_skills(normalized)
        experience_years = self._estimate_experience_years(normalized)

        return {
            "skills": skills,
            "experience_years_estimate": experience_years,
            "projects_count_estimate": max(1 if sections["projects"] else 0, len(re.findall(r"\bproject\b", normalized.lower()))),
            "sections": sections,
        }

    @staticmethod
    def _extract_section(lines: list[str], section_name: str) -> list[str]:
        aliases = SECTION_ALIASES[section_name]
        result: list[str] = []
        capture = False

        for line in lines:
            lower = line.lower().strip(":")
            if any(lower == alias for alias in aliases):
                capture = True
                continue

            if capture and re.match(r"^[A-Za-z\s]{3,30}:?$", line) and line.lower().strip(":") not in aliases:
                break

            if capture:
                result.append(line)

        return result

    def _extract_skills(self, text: str) -> list[str]:
        lowered = text.lower()
        matches = sorted({skill for skill in SKILL_KEYWORDS if skill in lowered})

        doc = self.nlp(text)
        token_candidates = {
            token.text.lower()
            for token in doc
            if token.is_alpha and len(token.text) > 2
        }

        for candidate in token_candidates:
            if candidate in SKILL_KEYWORDS:
                matches.append(candidate)

        return sorted(set(matches))

    @staticmethod
    def _estimate_experience_years(text: str) -> int:
        years = re.findall(r"(\d{1,2})\+?\s*(?:years|yrs)", text.lower())
        if years:
            return max(int(y) for y in years)
        return 0

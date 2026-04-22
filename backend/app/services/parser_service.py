"""Resume parsing service using DOCX/PDF extraction plus spaCy-friendly heuristics."""

from __future__ import annotations

from datetime import datetime
import io
import importlib
import re
from typing import Any
import unicodedata

import spacy

SKILL_KEYWORDS = {
    "python", "java", "javascript", "typescript", "react", "nextjs", "next.js", "node", "fastapi",
    "django", "flask", "sql", "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws",
    "azure", "gcp", "git", "playwright", "selenium", "langgraph", "langchain", "pandas", "numpy",
    "machine learning", "deep learning", "nlp", "spacy", "transformers", "ci/cd", "pytest",
    "scikit-learn", "matplotlib", "seaborn", "power bi", "jupyter", "streamlit", "pinecone",
    "mysql", "hugging face", "rag", "prompt engineering", "data visualization", "eda", "cnn", "rnn"
}

SKILL_SECTION_PREFIXES = {
    "programming",
    "frameworks & libraries",
    "frameworks and libraries",
    "libraries",
    "ai/ml & deep learning",
    "ai/ml and deep learning",
    "ai ml & deep learning",
    "ai ml and deep learning",
    "data & analytics",
    "data and analytics",
    "databases",
    "tools",
    "skills",
    "technical skills",
}

SKILL_CANDIDATE_BLOCKLIST = {
    "programming",
    "frameworks",
    "libraries",
    "frameworks libraries",
    "data analytics",
    "databases",
    "tools",
    "skills",
    "technical skills",
    "summary",
    "education",
    "projects",
    "experience",
}

SECTION_ALIASES = {
    "skills": ["skills", "technical skills", "tech stack"],
    "experience": ["experience", "work experience", "employment"],
    "projects": ["projects", "personal projects", "key projects"],
}

GENERIC_SECTION_HEADERS = {
    "summary",
    "profile",
    "objective",
    "education",
    "certifications",
    "achievements",
    "awards",
    "publications",
    "internships",
    "internship",
    "activities",
    "leadership",
    "contact",
    "languages",
    "interests",
    "hobbies",
    "references",
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
            reader = PdfReader(io.BytesIO(file_bytes), strict=False)

            if getattr(reader, "is_encrypted", False):
                try:
                    reader.decrypt("")
                except Exception as exc:
                    raise ValueError("Encrypted PDF is not supported. Upload an unlocked PDF or DOCX.") from exc

            standard_chunks: list[str] = []
            layout_chunks: list[str] = []
            for page in reader.pages:
                standard_text = ""
                try:
                    standard_text = page.extract_text() or ""
                except Exception:
                    standard_text = ""

                layout_text = ""
                try:
                    layout_text = page.extract_text(extraction_mode="layout") or ""
                except TypeError:
                    # Older extractor signatures may not accept extraction_mode.
                    layout_text = ""
                except Exception:
                    layout_text = ""

                if standard_text.strip():
                    standard_chunks.append(standard_text)
                if layout_text.strip():
                    layout_chunks.append(layout_text)

            candidates: list[str] = []

            standard_text = "\n".join(standard_chunks).strip()
            if standard_text:
                candidates.append(ResumeParserService._normalize_extracted_text(standard_text))

            layout_text = "\n".join(layout_chunks).strip()
            if layout_text:
                candidates.append(ResumeParserService._normalize_extracted_text(layout_text))

            # Optional extractor: pdfminer often succeeds for font-encoded PDFs where PyPDF2 output is noisy.
            try:
                pdfminer_module = importlib.import_module("pdfminer.high_level")
                pdfminer_extract_text = pdfminer_module.extract_text
                pdfminer_text = (pdfminer_extract_text(io.BytesIO(file_bytes)) or "").strip()
                if pdfminer_text:
                    candidates.append(ResumeParserService._normalize_extracted_text(pdfminer_text))
            except Exception:
                pass

            if not candidates:
                raise ValueError(
                    "Extracted resume text is empty. This PDF likely contains scanned images only; "
                    "upload a text-based PDF or DOCX."
                )

            best_text = max(candidates, key=ResumeParserService._score_text_quality)
            return best_text

        if extension == ".docx":
            docx_module = importlib.import_module("docx")
            Document = docx_module.Document
            document = Document(io.BytesIO(file_bytes))

            parts: list[str] = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]

            # Some resumes keep key content inside tables.
            for table in document.tables:
                for row in table.rows:
                    for cell in row.cells:
                        cell_text = " ".join(
                            p.text.strip() for p in cell.paragraphs if p.text and p.text.strip()
                        ).strip()
                        if cell_text:
                            parts.append(cell_text)

            text = "\n".join(parts).strip()
            if not text:
                raise ValueError("Extracted resume text is empty. Upload a DOCX with selectable text.")

            return ResumeParserService._normalize_extracted_text(text)

        raise ValueError("Unsupported file type. Only PDF and DOCX are allowed.")

    @staticmethod
    def _normalize_extracted_text(text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text)
        normalized = normalized.replace("\ufb01", "fi").replace("\ufb02", "fl")
        normalized = re.sub(r"\r\n?", "\n", normalized)
        normalized = re.sub(r"([A-Za-z])\s*-\s*\n\s*([a-z])", r"\1\2", normalized)
        normalized = re.sub(r"[^\S\n]+", " ", normalized)
        normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", normalized)

        lines = [line.strip() for line in normalized.split("\n")]
        merged: list[str] = []
        for line in lines:
            if not line:
                continue
            if merged and ResumeParserService._should_merge_with_previous(merged[-1], line):
                merged[-1] = f"{merged[-1]} {line}".strip()
            else:
                merged.append(line)

        cleaned = "\n".join(merged)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def _should_merge_with_previous(previous: str, current: str) -> bool:
        prev = previous.strip()
        cur = current.strip()
        if not prev or not cur:
            return False

        if cur.startswith(("•", "-", "*")):
            return False
        if re.fullmatch(r"[A-Z][A-Z\s/&-]{2,40}:?", cur):
            return False
        if cur.lower() in GENERIC_SECTION_HEADERS:
            return False
        if any(cur.lower() == alias for aliases in SECTION_ALIASES.values() for alias in aliases):
            return False

        if cur[0].islower():
            return True
        if prev.endswith(":"):
            return False
        if prev.endswith((",", ";", "and", "&")):
            return True
        if len(cur.split()) <= 2 and cur.lower() not in GENERIC_SECTION_HEADERS:
            return True

        return False

    @staticmethod
    def _score_text_quality(text: str) -> float:
        if not text:
            return float("-inf")

        lowered = text.lower()
        alpha_chars = sum(1 for ch in text if ch.isalpha())
        total_chars = max(1, len(text))
        alpha_ratio = alpha_chars / total_chars

        weird_chars = len(re.findall(r"[^\w\s\.,:;()\[\]{}\-+/#&%|]", text, flags=re.UNICODE))
        weird_ratio = weird_chars / total_chars

        header_hits = 0
        for aliases in SECTION_ALIASES.values():
            for alias in aliases:
                if re.search(rf"(^|\n){re.escape(alias)}\s*$", lowered, flags=re.MULTILINE):
                    header_hits += 1
        for header in GENERIC_SECTION_HEADERS:
            if re.search(rf"(^|\n){re.escape(header)}\s*$", lowered, flags=re.MULTILINE):
                header_hits += 1

        bullet_hits = len(re.findall(r"(^|\n)\s*[•\-*]", text))
        long_lines_penalty = sum(1 for line in text.split("\n") if len(line) > 220)

        return (
            len(text) * 0.015
            + (alpha_ratio * 90)
            + (header_hits * 12)
            + (bullet_hits * 0.8)
            - (weird_ratio * 130)
            - (long_lines_penalty * 1.5)
        )

    def parse_resume(self, text: str) -> dict[str, Any]:
        normalized = re.sub(r"\r\n?", "\n", text)
        lines = [line.strip() for line in normalized.split("\n") if line.strip()]

        sections = {
            "skills": self._extract_section(lines, "skills"),
            "experience": self._extract_section(lines, "experience"),
            "projects": self._extract_section(lines, "projects"),
        }

        skills = self._extract_skills(normalized, sections["skills"])
        experience_years = self._estimate_experience_years(
            normalized,
            experience_lines=sections["experience"],
            project_lines=sections["projects"],
        )
        projects_count = self._estimate_projects_count(sections["projects"], normalized)

        return {
            "skills": skills,
            "experience_years_estimate": experience_years,
            "projects_count_estimate": projects_count,
            "sections": sections,
        }

    @staticmethod
    def _extract_section(lines: list[str], section_name: str) -> list[str]:
        aliases = SECTION_ALIASES[section_name]
        all_aliases = {alias for alias_list in SECTION_ALIASES.values() for alias in alias_list}
        result: list[str] = []
        capture = False

        for line in lines:
            normalized_line = re.sub(r"\s+", " ", line.lower().strip().strip(":"))

            if normalized_line in aliases:
                capture = True
                continue

            if capture:
                if normalized_line in all_aliases and normalized_line not in aliases:
                    break
                if normalized_line in GENERIC_SECTION_HEADERS and normalized_line not in aliases:
                    break
                # Uppercase headings like SUMMARY / EDUCATION are reliable section boundaries.
                if re.fullmatch(r"[A-Z][A-Z\s/&-]{2,40}:?", line.strip()) and normalized_line not in aliases:
                    break

            if capture:
                result.append(line)

        return result

    def _extract_skills(self, text: str, skill_lines: list[str]) -> list[str]:
        lowered = text.lower()
        matches = {skill for skill in SKILL_KEYWORDS if skill in lowered}

        matches.update(self._extract_skills_from_lines(skill_lines))

        for line in skill_lines:
            line_lower = line.lower()
            for skill in SKILL_KEYWORDS:
                if re.search(rf"\b{re.escape(skill)}\b", line_lower):
                    matches.add(skill)

        doc = self.nlp(text)
        token_candidates = {
            token.text.lower()
            for token in doc
            if token.is_alpha and len(token.text) > 2
        }

        for candidate in token_candidates:
            if candidate in SKILL_KEYWORDS:
                matches.add(candidate)

        return sorted(matches)

    @staticmethod
    def _extract_skills_from_lines(skill_lines: list[str]) -> set[str]:
        extracted: set[str] = set()

        for raw_line in skill_lines:
            line = raw_line.strip()
            if not line:
                continue

            lower_line = line.lower()
            prefix_match = next(
                (prefix for prefix in sorted(SKILL_SECTION_PREFIXES, key=len, reverse=True) if lower_line.startswith(prefix + " ")),
                None,
            )
            if prefix_match:
                line = line[len(prefix_match):].strip(" :-")

            parts = re.split(r"[,;•]", line)
            for part in parts:
                for fragment in re.split(r"\b(?:and|&)\b", part, flags=re.IGNORECASE):
                    candidate = fragment.strip(" .:-|/").lower()
                    candidate = re.sub(r"\s+", " ", candidate)
                    if not candidate:
                        continue
                    if candidate in SKILL_CANDIDATE_BLOCKLIST:
                        continue
                    if len(candidate) < 2 or len(candidate.split()) > 5:
                        continue
                    if not re.search(r"[a-z]", candidate):
                        continue

                    extracted.add(candidate)

        return extracted

    @staticmethod
    def _estimate_experience_years(text: str, experience_lines: list[str], project_lines: list[str]) -> int:
        # Business rule: if there is no explicit Experience section, treat experience as 0.
        if not experience_lines:
            return 0

        lowered = text.lower()
        prioritized_text = "\n".join(experience_lines + project_lines)

        explicit_year_matches = re.findall(
            r"(?:over\s+|about\s+|around\s+)?(\d{1,2})\+?\s*(?:years|year|yrs)",
            f"{prioritized_text}\n{lowered}",
        )
        if explicit_year_matches:
            return max(int(value) for value in explicit_year_matches)

        current_year = datetime.utcnow().year
        spans: list[int] = []
        for start, end in re.findall(
            r"((?:19|20)\d{2})\s*[-–—to]+\s*((?:19|20)\d{2}|present|current)",
            prioritized_text.lower(),
        ):
            start_year = int(start)
            end_year = current_year if end in {"present", "current"} else int(end)
            if end_year >= start_year:
                spans.append(max(1, min(40, end_year - start_year)))
        if spans:
            return max(spans)

        if "hands-on experience" in lowered or "hands on experience" in lowered:
            return 1

        return 0

    @staticmethod
    def _estimate_projects_count(project_lines: list[str], text: str) -> int:
        title_candidates: set[str] = set()
        github_titles: set[str] = set()

        for index, raw_line in enumerate(project_lines):
            line = re.sub(r"^[\-•*\s]+", "", raw_line).strip()
            if not line:
                continue
            lower = line.lower()
            if lower in {"github", "linkedin", "portfolio"}:
                continue
            if line.startswith("http://") or line.startswith("https://"):
                continue

            looks_like_bullet_body = raw_line.lstrip().startswith(("•", "-", "*"))
            if looks_like_bullet_body:
                continue

            prev_raw = project_lines[index - 1] if index > 0 else ""
            prev_is_bullet = prev_raw.lstrip().startswith(("•", "-", "*"))
            if prev_is_bullet and "github" not in lower:
                # Wrapped bullet continuation lines should not be counted as new project titles.
                continue

            if line and line[0].islower():
                continue

            cleaned = re.sub(r"\bgithub\b", "", line, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s+", " ", cleaned).strip(" -|,")
            if "github" in lower and len(cleaned.split()) >= 2:
                github_titles.add(cleaned.lower())

            if len(cleaned.split()) >= 2 and not cleaned.endswith("."):
                title_candidates.add(cleaned.lower())

        if github_titles:
            return len(github_titles)

        if title_candidates:
            return len(title_candidates)

        project_word_hits = len(re.findall(r"\bprojects?\b", text.lower()))
        return max(1 if project_lines else 0, project_word_hits)

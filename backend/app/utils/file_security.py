"""File upload security validation helpers."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path


class FileValidationError(ValueError):
    """Raised when an uploaded file fails security validation."""


def _looks_like_pdf(content: bytes) -> bool:
    return content.startswith(b"%PDF-")


def _looks_like_docx(content: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = set(zf.namelist())
            required = {"[Content_Types].xml", "word/document.xml"}
            if not required.issubset(names):
                return False

            # Reject macro-bearing Office payloads in uploaded resume docs.
            if "word/vbaProject.bin" in names:
                return False

            return True
    except zipfile.BadZipFile:
        return False


def validate_resume_upload(
    filename: str,
    content_type: str | None,
    content: bytes,
    allowed_extensions: tuple[str, ...],
    allowed_mime_types: tuple[str, ...],
    max_upload_mb: int,
) -> str:
    """Validate uploaded resume bytes using extension, MIME, and magic/structure checks.

    Returns the normalized extension if valid.
    """
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise FileValidationError(f"Unsupported file extension: {ext}")

    if not content:
        raise FileValidationError("Uploaded file is empty")

    if len(content) > max_upload_mb * 1024 * 1024:
        raise FileValidationError(f"File exceeds {max_upload_mb}MB limit")

    normalized_mime = (content_type or "application/octet-stream").split(";")[0].strip().lower()
    if normalized_mime not in allowed_mime_types:
        raise FileValidationError(f"Unsupported MIME type: {normalized_mime}")

    if ext == ".pdf" and not _looks_like_pdf(content):
        raise FileValidationError("File extension says PDF, but content signature is invalid")

    if ext == ".docx" and not _looks_like_docx(content):
        raise FileValidationError("File extension says DOCX, but document structure is invalid or unsafe")

    return ext

"""DOCX text extraction service."""

from docx import Document


def extract_text_from_docx(file_data) -> str:
    """Extract all paragraph text from a DOCX file-like object."""
    document = Document(file_data)
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    return "\n".join(paragraphs).strip()

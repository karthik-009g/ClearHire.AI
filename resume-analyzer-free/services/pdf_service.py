"""PDF text extraction service."""

from PyPDF2 import PdfReader


def extract_text_from_pdf(file_data) -> str:
    """Extract all readable text from a PDF file-like object."""
    reader = PdfReader(file_data)
    pages = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages).strip()

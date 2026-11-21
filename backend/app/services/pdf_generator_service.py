"""Simple single-column PDF exporter for candidate-controlled resume drafts.

Uses basic typography and adaptive text sizing intended to remain easy to parse.
Actual ATS parsing and final page count depend on the receiving system and content.
"""

from __future__ import annotations

import io
import re
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib import colors


class PdfGeneratorService:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Strip markdown markers and clean for ATS PDF typography."""
        # Escape user-provided text before adding the small amount of supported markup.
        clean = escape(text)
        clean = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", clean)
        clean = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", clean)
        return clean

    def generate_ats_pdf(
        self,
        resume_text: str,
        candidate_name: str = "",
        contact_line: str = "",
    ) -> bytes:
        """Compile resume text into an ATS-compliant 1-page PDF."""
        buffer = io.BytesIO()

        # Target 0.5 inch (36 pt) margins for standard ATS format
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Use smaller type for longer drafts; content may still span multiple pages.
        raw_lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
        line_count = len(raw_lines)

        base_font_size = 9.0 if line_count > 46 else 10.0
        base_leading = 11.5 if line_count > 46 else 13.0
        spacer_height = 4 if line_count > 46 else 6

        name_style = ParagraphStyle(
            "ATS_Name",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16.0,
            leading=18.0,
            alignment=1,  # Centered
            textColor=colors.HexColor("#082542"),
            spaceAfter=2,
        )

        contact_style = ParagraphStyle(
            "ATS_Contact",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.0,
            alignment=1,  # Centered
            textColor=colors.HexColor("#334155"),
            spaceAfter=8,
        )

        section_heading_style = ParagraphStyle(
            "ATS_SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.0,
            leading=14.0,
            textColor=colors.HexColor("#0f172a"),
            borderPadding=(0, 0, 2, 0),
            spaceBefore=4,
            spaceAfter=4,
        )

        body_style = ParagraphStyle(
            "ATS_Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=base_font_size,
            leading=base_leading,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=2,
        )

        bullet_style = ParagraphStyle(
            "ATS_Bullet",
            parent=body_style,
            leftIndent=12,
            bulletIndent=4,
            spaceAfter=2,
        )

        story = []

        # 1. Header Name and Contact
        story.append(Paragraph(f"<b>{escape(candidate_name)}</b>", name_style))
        story.append(Paragraph(escape(contact_line), contact_style))
        story.append(Spacer(1, spacer_height))

        # 2. Process resume text lines
        for line in raw_lines:
            # Check for section headers (e.g. ## Technical Skills or EXPERIENCE)
            is_header = False
            clean_line = line

            if line.startswith("#"):
                is_header = True
                clean_line = line.lstrip("#").strip()
            elif line.isupper() and len(line) < 35 and not line.startswith("-"):
                is_header = True

            if is_header:
                story.append(Spacer(1, spacer_height))
                story.append(Paragraph(f"<b>{escape(clean_line.upper())}</b>", section_heading_style))
                continue

            # Check for bullet points
            if line.startswith("- ") or line.startswith("* ") or line.startswith("• "):
                bullet_content = self._clean_markdown(line[2:].strip())
                story.append(Paragraph(f"&bull; {bullet_content}", bullet_style))
            else:
                body_content = self._clean_markdown(line)
                story.append(Paragraph(body_content, body_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

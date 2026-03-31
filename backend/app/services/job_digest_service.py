"""Service for ranking and formatting matched jobs for email digest."""

from __future__ import annotations

from html import escape

from app.models import JobPosting


class JobDigestService:
    @staticmethod
    def rank_jobs(jobs: list[JobPosting], keywords: list[str]) -> list[JobPosting]:
        ranked = []
        for job in jobs:
            title = (job.title or "").lower()
            desc = (job.description or "").lower()
            score = sum(1 for kw in keywords if kw.lower() in title or kw.lower() in desc)
            job.score = float(score)
            ranked.append(job)

        return sorted(ranked, key=lambda x: (x.score or 0.0), reverse=True)

    @staticmethod
    def to_html(jobs: list[JobPosting], top_n: int = 25) -> str:
        rows = []
        for job in jobs[:top_n]:
            rows.append(
                "<li>"
                f"<b>{escape(job.title)}</b> - {escape(job.company)} "
                f"({escape(job.source)}) "
                f"<a href=\"{escape(job.url)}\">Apply</a>"
                "</li>"
            )

        if not rows:
            rows.append("<li>No matching jobs found from current scrape run.</li>")

        return (
            "<html><body>"
            "<h3>Your matched jobs digest (India portals)</h3>"
            "<ul>"
            + "".join(rows)
            + "</ul>"
            "</body></html>"
        )

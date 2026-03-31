"""Best-effort scraping service for India-focused career portals.

This uses lightweight HTTP + HTML extraction and avoids browser automation in API path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.utils.config import settings


@dataclass
class ScrapedJob:
    source: str
    company: str
    title: str
    url: str
    location: str | None
    description: str | None
    scraped_at: datetime


SOURCES: dict[str, dict[str, str]] = {
    "naukri": {
        "company": "Naukri",
        "url": "https://www.naukri.com/software-developer-jobs-in-india",
    },
    "linkedin": {
        "company": "LinkedIn",
        "url": "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=India",
    },
    "accenture": {
        "company": "Accenture",
        "url": "https://www.accenture.com/in-en/careers/jobsearch",
    },
    "tcs": {
        "company": "TCS",
        "url": "https://www.tcs.com/careers/india",
    },
    "cognizant": {
        "company": "Cognizant",
        "url": "https://careers.cognizant.com/in/en",
    },
    "deloitte": {
        "company": "Deloitte",
        "url": "https://www2.deloitte.com/in/en/careers.html",
    },
    "swiggy": {
        "company": "Swiggy",
        "url": "https://careers.swiggy.com/#/jobs",
    },
    "microsoft": {
        "company": "Microsoft",
        "url": "https://jobs.careers.microsoft.com/global/en/search?lc=India",
    },
    "google": {
        "company": "Google",
        "url": "https://www.google.com/about/careers/applications/jobs/results/?location=India",
    },
    "ibm": {
        "company": "IBM",
        "url": "https://www.ibm.com/in-en/employment/",
    },
}


class JobScraperService:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                )
            }
        )

    def scrape_sources(self, source_keys: list[str], keywords: list[str] | None = None) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        for key in source_keys:
            if key not in SOURCES:
                continue
            jobs.extend(self._scrape_single_source(key, keywords or []))
        return jobs

    def _scrape_single_source(self, source_key: str, keywords: list[str]) -> list[ScrapedJob]:
        source_meta = SOURCES[source_key]
        url = source_meta["url"]
        company = source_meta["company"]

        try:
            response = self.session.get(url, timeout=settings.request_timeout)
            response.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(response.text, "lxml")

        jobs: list[ScrapedJob] = []
        for anchor in soup.select("a[href]"):
            title = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "").strip()

            if not title or len(title) < 4:
                continue

            title_lower = title.lower()
            if keywords and not any(kw.lower() in title_lower for kw in keywords):
                # keep broad job-like text if no direct keyword match
                if not any(x in title_lower for x in ["engineer", "developer", "analyst", "consultant", "architect"]):
                    continue
            elif not keywords and not any(x in title_lower for x in ["engineer", "developer", "analyst", "consultant", "architect"]):
                continue

            absolute_url = urljoin(url, href)
            jobs.append(
                ScrapedJob(
                    source=source_key,
                    company=company,
                    title=title[:255],
                    url=absolute_url[:1024],
                    location="India",
                    description=None,
                    scraped_at=datetime.utcnow(),
                )
            )

            if len(jobs) >= settings.scrape_max_jobs_per_source:
                break

        dedup: dict[str, ScrapedJob] = {job.url: job for job in jobs}
        return list(dedup.values())

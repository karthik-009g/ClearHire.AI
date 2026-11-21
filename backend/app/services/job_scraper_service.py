"""Best-effort scraping service for India-focused career portals.

This uses lightweight HTTP + HTML extraction and avoids browser automation in API path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, Tag

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
    posted_at: datetime | None = None
    posted_text: str | None = None


SOURCES: dict[str, dict[str, str]] = {
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

ROLE_HINTS: tuple[str, ...] = (
    "engineer",
    "developer",
    "fullstack",
    "full-stack",
    "sde",
    "analyst",
    "consultant",
    "architect",
    "scientist",
    "devops",
    "intern",
    "manager",
    "specialist",
    "sre",
    "qa",
    "test",
    "programmer",
)

URL_JOB_HINTS: tuple[str, ...] = (
    "/job",
    "/jobs",
    "jobsearch",
    "careers",
    "career",
    "opening",
    "vacanc",
    "position",
)

URL_EXCLUDE_HINTS: tuple[str, ...] = (
    "/about",
    "/services",
    "/insight",
    "/news",
    "/blog",
    "/privacy",
    "/policy",
    "/contact",
    "/investor",
    "/events",
    "/terms",
    "/sitemap",
    "/press",
)

TRACKING_QUERY_KEYS: tuple[str, ...] = (
    "refid",
    "trackingid",
    "trk",
    "position",
    "pagenum",
    "sessionid",
)


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

    def _fetch_html_rendered(self, url: str) -> str | None:
        """Headless browser rendering fallback for SPA job portals."""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_default_timeout(10000)
                page.goto(url, wait_until="domcontentloaded")
                content = page.content()
                browser.close()
                return content
        except Exception:
            return None

    def _get_with_retry(self, url: str):
        attempts = max(1, int(settings.max_retries))
        for _ in range(attempts):
            try:
                response = self.session.get(url, timeout=settings.request_timeout)
                response.raise_for_status()
                return response
            except Exception:
                continue

        rendered = self._fetch_html_rendered(url)
        if rendered:
            class _RenderedResponse:
                def __init__(self, text: str):
                    self.text = text
            return _RenderedResponse(rendered)
        return None

    def scrape_sources(
        self,
        source_keys: list[str],
        keywords: list[str] | None = None,
        max_post_age_hours: int | None = None,
    ) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        for key in source_keys:
            if key not in SOURCES:
                continue
            jobs.extend(self._scrape_single_source(key, keywords or [], max_post_age_hours=max_post_age_hours))
        return jobs

    def _scrape_single_source(
        self,
        source_key: str,
        keywords: list[str],
        max_post_age_hours: int | None,
    ) -> list[ScrapedJob]:
        if source_key == "linkedin":
            return self._scrape_linkedin_source(source_key, keywords, max_post_age_hours)
        return self._scrape_generic_source(source_key, keywords, max_post_age_hours=max_post_age_hours)

    def _linkedin_search_urls(self, keywords: list[str]) -> list[str]:
        keyword_query = " ".join(keyword.strip() for keyword in keywords if keyword.strip())
        if not keyword_query:
            keyword_query = "software engineer"

        pages = max(1, min(6, int(settings.scrape_max_pages_per_source)))
        urls = []
        for page_index in range(pages):
            query = urlencode({"keywords": keyword_query, "location": "India", "start": page_index * 25})
            urls.append(f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{query}")
        urls.append(SOURCES["linkedin"]["url"])
        return list(dict.fromkeys(urls))

    def _scrape_linkedin_source(
        self,
        source_key: str,
        keywords: list[str],
        max_post_age_hours: int | None,
    ) -> list[ScrapedJob]:
        source_meta = SOURCES[source_key]
        jobs: list[ScrapedJob] = []
        for search_url in self._linkedin_search_urls(keywords):
            response = self._get_with_retry(search_url)
            if response is None:
                continue

            soup = BeautifulSoup(response.text, "lxml")
            for anchor in soup.select("a[href*='/jobs/view/']"):
                href = (anchor.get("href") or "").strip()
                if not href:
                    continue

                job_url = self._canonicalize_url(source_key, urljoin(search_url, href))
                container = anchor.find_parent("li") or anchor.find_parent("div") or anchor.parent
                title = self._select_first_text(
                    container,
                    ("h3.base-search-card__title", "h3", "span.screen-reader-text"),
                ) or self._safe_text(anchor)
                if not self._looks_like_job_title(title):
                    continue

                context_snippet = self._context_snippet(container)
                if not self._passes_keyword_filter(title, keywords, context_snippet):
                    continue

                snippet_lower = (context_snippet or "").lower()
                if any(x in snippet_lower for x in ("no longer accepting applications", "job is closed", "expired", "closed")):
                    continue
                if "expired_jd_redirect" in job_url:
                    continue

                company = self._select_first_text(
                    container,
                    (
                        "h4.base-search-card__subtitle a",
                        "h4.base-search-card__subtitle",
                        "a.hidden-nested-link",
                    ),
                ) or self._extract_company_from_linkedin_url(job_url) or source_meta["company"]
                location = self._select_first_text(
                    container,
                    ("span.job-search-card__location", "span.base-search-card__metadata"),
                ) or "India"
                time_tag = self._select_first_tag(
                    container,
                    ("time", "span.job-search-card__listdate", "span.job-search-card__listdate--new"),
                )
                posted_at, posted_text = self._parse_posted_datetime(time_tag, container)
                if not self._is_recent(posted_at, max_post_age_hours):
                    continue

                jobs.append(
                    ScrapedJob(
                        source=source_key,
                        company=company[:255],
                        title=title[:255],
                        url=job_url[:1024],
                        location=location[:255],
                        description=context_snippet,
                        scraped_at=datetime.utcnow(),
                        posted_at=posted_at,
                        posted_text=posted_text,
                    )
                )
                if len(jobs) >= settings.scrape_max_jobs_per_source:
                    break
            if len(jobs) >= settings.scrape_max_jobs_per_source:
                break

        return self._dedupe_jobs(jobs)

    def _scrape_generic_source(
        self,
        source_key: str,
        keywords: list[str],
        max_post_age_hours: int | None,
    ) -> list[ScrapedJob]:
        source_meta = SOURCES[source_key]
        url = source_meta["url"]
        company = source_meta["company"]

        response = self._get_with_retry(url)
        if response is None:
            return []

        soup = BeautifulSoup(response.text, "lxml")

        jobs: list[ScrapedJob] = []
        for anchor in soup.select("a[href]"):
            title = self._safe_text(anchor)
            href = (anchor.get("href") or "").strip()

            if not title or len(title) < 4:
                continue

            absolute_url = self._canonicalize_url(source_key, urljoin(url, href))
            if not self._is_probable_job_url(source_key, absolute_url):
                continue

            if not self._looks_like_job_title(title):
                continue

            context_holder = anchor.find_parent("li") or anchor.find_parent("article") or anchor.find_parent("div") or anchor.parent
            context_snippet = self._context_snippet(context_holder)
            if not self._passes_keyword_filter(title, keywords, context_snippet):
                continue

            posted_at, posted_text = self._parse_posted_datetime(None, context_holder)
            if not self._is_recent(posted_at, max_post_age_hours):
                continue

            jobs.append(
                ScrapedJob(
                    source=source_key,
                    company=company[:255],
                    title=title[:255],
                    url=absolute_url[:1024],
                    location="India",
                    description=context_snippet,
                    scraped_at=datetime.utcnow(),
                    posted_at=posted_at,
                    posted_text=posted_text,
                )
            )

            if len(jobs) >= settings.scrape_max_jobs_per_source:
                break

        return self._dedupe_jobs(jobs)

    @staticmethod
    def _safe_text(node: Tag | None) -> str:
        if node is None:
            return ""
        return node.get_text(" ", strip=True)

    @staticmethod
    def _select_first_tag(container: Tag | None, selectors: tuple[str, ...]) -> Tag | None:
        if container is None:
            return None
        for selector in selectors:
            tag = container.select_one(selector)
            if tag is not None:
                return tag
        return None

    def _select_first_text(self, container: Tag | None, selectors: tuple[str, ...]) -> str:
        tag = self._select_first_tag(container, selectors)
        return self._safe_text(tag)

    @staticmethod
    def _dedupe_jobs(jobs: list[ScrapedJob]) -> list[ScrapedJob]:
        dedup: dict[str, ScrapedJob] = {}
        for job in jobs:
            key = job.url or f"{job.source}:{job.company.lower()}:{job.title.lower()}"
            existing = dedup.get(key)
            if existing is None:
                dedup[key] = job
                continue
            if job.posted_at and (existing.posted_at is None or job.posted_at > existing.posted_at):
                dedup[key] = job
        return list(dedup.values())

    @staticmethod
    def _context_snippet(node: Tag | None, max_len: int = 420) -> str | None:
        if node is None:
            return None
        text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()
        if not text:
            return None
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    @staticmethod
    def _looks_like_job_title(title: str) -> bool:
        cleaned = re.sub(r"\s+", " ", title).strip()
        if len(cleaned) < 4 or len(cleaned) > 180:
            return False
        lowered = cleaned.lower()
        if any(block in lowered for block in ("sign in", "privacy", "cookie", "terms", "contact us")):
            return False
        return any(hint in lowered for hint in ROLE_HINTS)

    def _passes_keyword_filter(self, title: str, keywords: list[str], context_text: str | None = None) -> bool:
        title_lower = title.lower()
        combined_lower = f"{title} {context_text or ''}".lower()
        if not keywords:
            return True
        if any(kw.lower() in combined_lower for kw in keywords):
            return True
        return any(hint in title_lower for hint in ROLE_HINTS)

    @staticmethod
    def _is_probable_job_url(source_key: str, absolute_url: str) -> bool:
        lowered = absolute_url.lower()

        if source_key == "linkedin":
            return "/jobs/view/" in lowered

        if any(hint in lowered for hint in URL_EXCLUDE_HINTS):
            return False

        return any(hint in lowered for hint in URL_JOB_HINTS)

    @staticmethod
    def _canonicalize_url(source_key: str, raw_url: str) -> str:
        parsed = urlparse(raw_url.strip())
        if not parsed.scheme or not parsed.netloc:
            return raw_url.strip()

        path = parsed.path.rstrip("/") or "/"
        netloc = parsed.netloc.lower()

        if source_key == "linkedin":
            return urlunparse((parsed.scheme, netloc, path, "", "", ""))

        query_items = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_query = [
            (key, value)
            for key, value in query_items
            if key.lower() not in TRACKING_QUERY_KEYS and not key.lower().startswith("utm_")
        ]
        query = urlencode(filtered_query, doseq=True)
        return urlunparse((parsed.scheme, netloc, path, "", query, ""))

    @staticmethod
    def _is_recent(posted_at: datetime | None, max_post_age_hours: int | None) -> bool:
        if max_post_age_hours is None:
            return True
        if posted_at is None:
            # Many company pages omit explicit post dates. Keep them eligible,
            # then let semantic and keyword ranking push weak matches down.
            return True
        cutoff = datetime.utcnow() - timedelta(hours=max_post_age_hours)
        return posted_at >= cutoff

    def _parse_posted_datetime(self, time_tag: Tag | None, container: Tag | None) -> tuple[datetime | None, str | None]:
        if time_tag is not None:
            datetime_attr = (time_tag.get("datetime") or "").strip()
            parsed_iso = self._parse_iso_datetime(datetime_attr)
            if parsed_iso is not None:
                text = self._safe_text(time_tag) or datetime_attr
                return parsed_iso, text

            text_value = self._safe_text(time_tag)
            parsed_relative = self._parse_relative_datetime(text_value)
            if parsed_relative is not None:
                return parsed_relative, text_value

        if container is None:
            return None, None

        context_text = " ".join(list(container.stripped_strings)[:60])
        relative = self._parse_relative_datetime(context_text)
        if relative is not None:
            return relative, context_text

        absolute = self._parse_datetime_from_text(context_text)
        if absolute is not None:
            return absolute, context_text

        return None, None

    @staticmethod
    def _parse_iso_datetime(value: str) -> datetime | None:
        if not value:
            return None

        candidate = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return None

        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed

    @staticmethod
    def _parse_relative_datetime(text: str) -> datetime | None:
        if not text:
            return None

        lowered = re.sub(r"\s+", " ", text.lower()).strip()
        lowered = lowered.replace("reposted", "").replace("+", "")

        now = datetime.utcnow()
        if "just now" in lowered or "today" in lowered:
            return now
        if "yesterday" in lowered:
            return now - timedelta(days=1)

        long_match = re.search(r"(\d+)\s*(hour|hours|hr|hrs|day|days|week|weeks|month|months)\s*ago", lowered)
        if long_match:
            amount = int(long_match.group(1))
            unit = long_match.group(2)
            if unit.startswith("hour") or unit.startswith("hr"):
                return now - timedelta(hours=amount)
            if unit.startswith("day"):
                return now - timedelta(days=amount)
            if unit.startswith("week"):
                return now - timedelta(days=amount * 7)
            if unit.startswith("month"):
                return now - timedelta(days=amount * 30)

        short_match = re.search(r"(\d+)\s*([hdw])\s*ago", lowered)
        if short_match:
            amount = int(short_match.group(1))
            unit = short_match.group(2)
            if unit == "h":
                return now - timedelta(hours=amount)
            if unit == "d":
                return now - timedelta(days=amount)
            if unit == "w":
                return now - timedelta(days=amount * 7)

        return None

    @staticmethod
    def _parse_datetime_from_text(text: str) -> datetime | None:
        if not text:
            return None

        candidates: list[tuple[str, str]] = [
            (r"\b\d{4}-\d{2}-\d{2}\b", "%Y-%m-%d"),
            (r"\b\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\b", "%d %b %Y"),
            (r"\b[A-Za-z]{3}\s+\d{1,2},\s+\d{4}\b", "%b %d, %Y"),
        ]

        for pattern, fmt in candidates:
            match = re.search(pattern, text)
            if not match:
                continue
            try:
                return datetime.strptime(match.group(0), fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def _title_case_company(raw: str) -> str:
        words = [word for word in raw.split() if word]
        if not words:
            return ""

        normalized: list[str] = []
        for word in words:
            if len(word) <= 3 and word.isupper():
                normalized.append(word)
                continue
            normalized.append(word.capitalize())
        return " ".join(normalized)

    def _extract_company_from_linkedin_url(self, absolute_url: str) -> str | None:
        path = urlparse(absolute_url).path
        match = re.search(r"/jobs/view/[^/]*?-at-([a-z0-9-]+)-\d+", path, flags=re.IGNORECASE)
        if not match:
            return None
        company_slug = match.group(1).strip("-")
        if not company_slug:
            return None
        return self._title_case_company(company_slug.replace("-", " "))

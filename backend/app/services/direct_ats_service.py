"""Fetch public postings from configured Greenhouse, Lever, and Ashby boards.

An ATS source helps identify where a listing came from; it does not prove availability,
employer identity, or predict whether a recruiter will respond.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import re
from typing import Any
import requests
from bs4 import BeautifulSoup

from app.services.cache_service import CacheService, get_cache_service
from app.services.job_scraper_service import ScrapedJob

logger = logging.getLogger(__name__)


def _serialize_scraped_job(job: ScrapedJob) -> dict[str, Any]:
    return {
        "source": job.source,
        "company": job.company,
        "title": job.title,
        "url": job.url,
        "location": job.location,
        "description": job.description,
        "scraped_at": job.scraped_at.isoformat() if isinstance(job.scraped_at, datetime) else str(job.scraped_at),
        "posted_at": job.posted_at.isoformat() if isinstance(job.posted_at, datetime) else (str(job.posted_at) if job.posted_at else None),
        "posted_text": job.posted_text,
        "ats_type": getattr(job, "ats_type", None),
    }


def _deserialize_scraped_job(data: dict[str, Any]) -> ScrapedJob:
    scraped_at_val = data.get("scraped_at")
    scraped_at = datetime.fromisoformat(scraped_at_val) if scraped_at_val else datetime.now(timezone.utc)
    posted_at_val = data.get("posted_at")
    posted_at = datetime.fromisoformat(posted_at_val) if posted_at_val else None
    job = ScrapedJob(
        source=data.get("source", ""),
        company=data.get("company", ""),
        title=data.get("title", ""),
        url=data.get("url", ""),
        location=data.get("location"),
        description=data.get("description"),
        scraped_at=scraped_at,
        posted_at=posted_at,
        posted_text=data.get("posted_text"),
    )
    if data.get("ats_type"):
        setattr(job, "ats_type", data["ats_type"])
    return job

# Curated registry of top tech companies & Indian tech leaders using modern ATS platforms
# Prioritizing verified boards with active public requisition APIs
CURATED_ATS_REGISTRY: list[dict[str, str]] = [
    # Greenhouse active verified boards (India & Global Remote)
    {"company": "Postman", "provider": "greenhouse", "token": "postman"},
    {"company": "InMobi", "provider": "greenhouse", "token": "inmobi"},
    {"company": "Groww", "provider": "greenhouse", "token": "groww"},
    {"company": "Stripe", "provider": "greenhouse", "token": "stripe"},
    {"company": "Rubrik", "provider": "greenhouse", "token": "rubrik"},
    {"company": "MongoDB", "provider": "greenhouse", "token": "mongodb"},
    {"company": "Cloudflare", "provider": "greenhouse", "token": "cloudflare"},
    {"company": "Elastic", "provider": "greenhouse", "token": "elastic"},
    {"company": "Datadog", "provider": "greenhouse", "token": "datadog"},
    {"company": "Coinbase", "provider": "greenhouse", "token": "coinbase"},
    {"company": "GitLab", "provider": "greenhouse", "token": "gitlab"},
    {"company": "Figma", "provider": "greenhouse", "token": "figma"},
    {"company": "Airtable", "provider": "greenhouse", "token": "airtable"},
    # Ashby active verified boards (AI & Modern Tech)
    {"company": "Perplexity AI", "provider": "ashby", "token": "perplexity"},
    {"company": "Replit", "provider": "ashby", "token": "replit"},
    {"company": "Ramp", "provider": "ashby", "token": "ramp"},
    {"company": "Vanta", "provider": "ashby", "token": "vanta"},
]

INDIA_LOCATION_KEYWORDS: tuple[str, ...] = (
    "india",
    "bengaluru",
    "bangalore",
    "hyderabad",
    "pune",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "mumbai",
    "chennai",
    "remote",
    "anywhere",
    "apac",
)


class DirectAtsService:
    def __init__(self, timeout: int = 6, cache: CacheService | None = None) -> None:
        self.timeout = timeout
        if cache is not None:
            self.cache = cache
        else:
            try:
                self.cache = get_cache_service()
            except Exception:
                self.cache = None
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ClearHire-DirectSourcing-Engine/1.0 (+https://clearhire.ai)",
            "Accept": "application/json, text/plain, */*",
        })

    def _strip_html(self, raw_html: str | None) -> str:
        if not raw_html:
            return ""
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            return " ".join(soup.stripped_strings)
        except Exception:
            return re.sub(r"<[^>]+>", " ", raw_html or "").strip()

    def fetch_greenhouse_jobs(self, token: str, company: str) -> list[ScrapedJob]:
        """Fetch jobs directly from Greenhouse public board API."""
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        jobs: list[ScrapedJob] = []
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                logger.debug(f"Greenhouse board {token} returned {resp.status_code}")
                return jobs

            payload = resp.json()
            items = payload.get("jobs", [])
            for item in items:
                title = item.get("title") or ""
                loc_dict = item.get("location") or {}
                loc_name = loc_dict.get("name") if isinstance(loc_dict, dict) else str(loc_dict)
                apply_url = item.get("absolute_url") or f"https://boards.greenhouse.io/{token}/jobs/{item.get('id')}"
                content = self._strip_html(item.get("content"))
                updated_at_str = item.get("updated_at")

                posted_at: datetime | None = None
                if updated_at_str:
                    try:
                        clean_dt = updated_at_str.replace("Z", "+00:00")
                        posted_at = datetime.fromisoformat(clean_dt)
                    except Exception:
                        posted_at = None

                jobs.append(
                    ScrapedJob(
                        source=f"greenhouse_{token}",
                        company=company,
                        title=title,
                        url=apply_url,
                        location=loc_name,
                        description=content[:2000] if content else f"{title} at {company}",
                        scraped_at=datetime.now(timezone.utc),
                        posted_at=posted_at,
                    )
                )
        except Exception as e:
            logger.debug(f"Error fetching Greenhouse board for {company}: {e}")
        return jobs

    def fetch_lever_jobs(self, token: str, company: str) -> list[ScrapedJob]:
        """Fetch jobs directly from Lever public postings API."""
        url = f"https://api.lever.co/v0/postings/{token}?mode=json"
        jobs: list[ScrapedJob] = []
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                logger.debug(f"Lever board {token} returned {resp.status_code}")
                return jobs

            items = resp.json()
            if not isinstance(items, list):
                return jobs

            for item in items:
                title = item.get("text") or ""
                categories = item.get("categories") or {}
                location = categories.get("location") or "Remote / Multiple"
                apply_url = item.get("hostedUrl") or f"https://jobs.lever.co/{token}/{item.get('id')}"
                description = self._strip_html(item.get("descriptionPlain") or item.get("description"))

                posted_at: datetime | None = None
                created_epoch = item.get("createdAt")
                if created_epoch:
                    try:
                        posted_at = datetime.fromtimestamp(created_epoch / 1000.0, tz=timezone.utc)
                    except Exception:
                        posted_at = None

                jobs.append(
                    ScrapedJob(
                        source=f"lever_{token}",
                        company=company,
                        title=title,
                        url=apply_url,
                        location=location,
                        description=description[:2000] if description else f"{title} at {company}",
                        scraped_at=datetime.now(timezone.utc),
                        posted_at=posted_at,
                    )
                )
        except Exception as e:
            logger.debug(f"Error fetching Lever board for {company}: {e}")
        return jobs

    def fetch_ashby_jobs(self, token: str, company: str) -> list[ScrapedJob]:
        """Fetch jobs directly from Ashby public board API."""
        url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
        jobs: list[ScrapedJob] = []
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                logger.debug(f"Ashby board {token} returned {resp.status_code}")
                return jobs

            data = resp.json()
            items = data.get("jobs", [])
            for item in items:
                title = item.get("title") or ""
                location = item.get("location") or "Remote"
                apply_url = item.get("jobUrl") or f"https://jobs.ashbyhq.com/{token}/{item.get('id')}"
                description = self._strip_html(item.get("descriptionHtml"))

                posted_at: datetime | None = None
                pub_str = item.get("publishedAt")
                if pub_str:
                    try:
                        posted_at = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                    except Exception:
                        posted_at = None

                jobs.append(
                    ScrapedJob(
                        source=f"ashby_{token}",
                        company=company,
                        title=title,
                        url=apply_url,
                        location=location,
                        description=description[:2000] if description else f"{title} at {company}",
                        scraped_at=datetime.now(timezone.utc),
                        posted_at=posted_at,
                    )
                )
        except Exception as e:
            logger.debug(f"Error fetching Ashby board for {company}: {e}")
        return jobs

    def fetch_company_jobs(self, entry: dict[str, str]) -> list[ScrapedJob]:
        provider = entry.get("provider", "").lower()
        token = entry.get("token", "")
        company = entry.get("company", token)

        if provider == "greenhouse":
            return self.fetch_greenhouse_jobs(token, company)
        elif provider == "lever":
            return self.fetch_lever_jobs(token, company)
        elif provider == "ashby":
            return self.fetch_ashby_jobs(token, company)
        return []

    def fetch_all_direct_jobs(
        self,
        target_companies: list[str] | None = None,
        keywords: list[str] | None = None,
        india_or_remote_only: bool = True,
        max_jobs: int = 50,
    ) -> list[ScrapedJob]:
        """Fetch and filter postings returned by supported public ATS endpoints (memoized with 15m TTL)."""
        cache_key = None
        if self.cache:
            try:
                cache_inputs = {
                    "companies": sorted([c.strip().lower() for c in (target_companies or []) if c.strip()]),
                    "keywords": sorted([k.strip().lower() for k in (keywords or []) if k.strip()]),
                    "india_or_remote_only": india_or_remote_only,
                    "max_jobs": max_jobs,
                }
                cache_key = self.cache.make_key("direct_ats_jobs", cache_inputs)
                cached = self.cache.get("direct_ats_jobs", cache_key)
                if cached is not None:
                    logger.debug(f"Direct ATS cache hit for {cache_key}")
                    return [_deserialize_scraped_job(j) if isinstance(j, dict) else j for j in cached]
            except Exception as exc:
                logger.warning(f"Error reading direct ATS cache: {exc}")

        results: list[ScrapedJob] = []

        registry = CURATED_ATS_REGISTRY
        if target_companies:
            lower_targets = {c.strip().lower() for c in target_companies if c.strip()}
            registry = [e for e in registry if e["company"].lower() in lower_targets or e["token"].lower() in lower_targets]
            if not registry:
                return []

        keywords_lower = [k.strip().lower() for k in (keywords or []) if k.strip()]

        for entry in registry:
            if len(results) >= max_jobs:
                break

            fetched = self.fetch_company_jobs(entry)
            for job in fetched:
                title_lower = (job.title or "").lower()
                loc_lower = (job.location or "").lower()

                # Location check (India / Remote preference)
                if india_or_remote_only:
                    if not any(loc_kw in loc_lower for loc_kw in INDIA_LOCATION_KEYWORDS):
                        continue

                # Keywords check
                if keywords_lower:
                    matches = any(k in title_lower or k in (job.description or "").lower() for k in keywords_lower)
                    if not matches:
                        continue

                results.append(job)
                if len(results) >= max_jobs:
                    break

        if self.cache and cache_key:
            try:
                serialized = [_serialize_scraped_job(j) for j in results]
                self.cache.set("direct_ats_jobs", cache_key, serialized, ttl=900)
            except Exception as exc:
                logger.warning(f"Error writing direct ATS cache: {exc}")

        return results

    def get_direct_jobs(
        self,
        target_companies: list[str] | None = None,
        keywords: list[str] | None = None,
        india_or_remote_only: bool = True,
        max_jobs: int = 50,
    ) -> list[ScrapedJob]:
        """Return only the real postings returned by the public ATS endpoints."""
        jobs = self.fetch_all_direct_jobs(
            target_companies=target_companies,
            keywords=keywords,
            india_or_remote_only=india_or_remote_only,
            max_jobs=max_jobs,
        )
        # Only return postings actually received from public ATS endpoints.
        for j in jobs:
            if not hasattr(j, "ats_type") or not getattr(j, "ats_type"):
                provider = "greenhouse" if "greenhouse" in j.source else ("lever" if "lever" in j.source else ("ashby" if "ashby" in j.source else "direct"))
                setattr(j, "ats_type", provider)
        return jobs[:max_jobs]


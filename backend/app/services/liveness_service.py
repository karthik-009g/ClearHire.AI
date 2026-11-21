"""Job link liveness and expiration verification service.

Detects expired job postings, closed requisitions, 404s, and expired redirects
before presenting them to candidates, and provides official fallback career portals.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse
import requests
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Known company official career portals (guaranteed active entry points)
COMPANY_CAREER_PORTALS: dict[str, str] = {
    "razorpay": "https://razorpay.com/jobs/",
    "cred": "https://careers.cred.club/",
    "postman": "https://www.postman.com/company/careers/open-positions/",
    "swiggy": "https://careers.swiggy.com/",
    "zepto": "https://www.zeptonow.com/careers",
    "browserstack": "https://www.browserstack.com/careers",
    "inmobi": "https://boards.greenhouse.io/inmobi",
    "groww": "https://boards.greenhouse.io/groww",
    "stripe": "https://stripe.com/jobs/search",
    "figma": "https://boards.greenhouse.io/figma",
    "coinbase": "https://boards.greenhouse.io/coinbase",
    "gitlab": "https://boards.greenhouse.io/gitlab",
    "datadog": "https://boards.greenhouse.io/datadog",
    "rubrik": "https://boards.greenhouse.io/rubrik",
    "mongodb": "https://boards.greenhouse.io/mongodb",
    "cloudflare": "https://boards.greenhouse.io/cloudflare",
    "elastic": "https://boards.greenhouse.io/elastic",
    "perplexity ai": "https://jobs.ashbyhq.com/perplexity",
    "perplexity": "https://jobs.ashbyhq.com/perplexity",
    "replit": "https://jobs.ashbyhq.com/replit",
    "ramp": "https://jobs.ashbyhq.com/ramp",
    "vanta": "https://jobs.ashbyhq.com/vanta",
    "airtable": "https://boards.greenhouse.io/airtable",
    "urban company": "https://careers.urbancompany.com/",
    "zomato": "https://www.zomato.com/careers",
    "paytm": "https://paytm.com/careers/",
    "phonepe": "https://www.phonepe.com/careers/",
    "meesho": "https://meesho.io/jobs",
    "microsoft": "https://jobs.careers.microsoft.com/global/en/search?lc=India",
    "google": "https://www.google.com/about/careers/applications/jobs/results/?location=India",
    "accenture": "https://www.accenture.com/in-en/careers/jobsearch",
    "tcs": "https://www.tcs.com/careers/india",
    "cognizant": "https://careers.cognizant.com/in/en",
    "deloitte": "https://www2.deloitte.com/in/en/careers.html",
}

EXPIRED_KEYWORDS: tuple[str, ...] = (
    "no longer accepting applications",
    "this job is closed",
    "job has expired",
    "position is no longer available",
    "this role has been filled",
    "opening has been closed",
    "sorry, this job is no longer available",
    "this position has been closed",
    "job posting has expired",
    "page not found",
    "404 not found",
    "the job you are looking for is no longer open",
)

_LIVENESS_CACHE: dict[str, dict[str, Any]] = {}


def get_company_fallback_career_url(company: str | None, current_url: str | None = None) -> str:
    """Return verified official career portal URL for a company."""
    if company:
        norm = company.strip().lower()
        if norm in COMPANY_CAREER_PORTALS:
            return COMPANY_CAREER_PORTALS[norm]
        for key, portal in COMPANY_CAREER_PORTALS.items():
            if key in norm or norm in key:
                return portal

    # Extract domain fallback from current URL if available
    if current_url:
        try:
            parsed = urlparse(current_url)
            if parsed.netloc:
                parts = parsed.netloc.split(".")
                if len(parts) >= 2:
                    domain = ".".join(parts[-2:])
                    return f"https://{domain}/careers"
        except Exception:
            pass

    return "https://clearhire.ai/job-hunter"


def verify_job_url(url: str, timeout: float = 3.5) -> dict[str, Any]:
    """Check whether a job application URL is live or expired/closed."""
    if not url or not url.startswith("http"):
        return {
            "url": url,
            "is_live": False,
            "is_expired": True,
            "status_code": 0,
            "reason": "invalid_url",
            "final_url": url,
        }

    # Check in-memory cache
    if url in _LIVENESS_CACHE:
        return _LIVENESS_CACHE[url]

    # ATS Direct Boards (Greenhouse, Lever, Ashby) URLs are well-formed
    # We test with a lightweight request
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        # Use GET with stream to avoid downloading large pages
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
        final_url = resp.url
        status_code = resp.status_code

        # Check HTTP error status codes
        if status_code in (404, 410):
            result = {
                "url": url,
                "is_live": False,
                "is_expired": True,
                "status_code": status_code,
                "reason": f"HTTP {status_code} Not Found",
                "final_url": final_url,
            }
            _LIVENESS_CACHE[url] = result
            return result

        # Check for expired redirects (e.g. LinkedIn trk=expired_jd_redirect)
        if "expired_jd_redirect" in final_url or "expired" in final_url.lower():
            result = {
                "url": url,
                "is_live": False,
                "is_expired": True,
                "status_code": status_code,
                "reason": "Redirected to expired job notice",
                "final_url": final_url,
            }
            _LIVENESS_CACHE[url] = result
            return result

        # Read first 8KB of body to check text indicators without downloading entire payload
        sample_bytes = resp.raw.read(8192)
        sample_text = sample_bytes.decode("utf-8", errors="ignore").lower()

        for kw in EXPIRED_KEYWORDS:
            if kw in sample_text:
                result = {
                    "url": url,
                    "is_live": False,
                    "is_expired": True,
                    "status_code": status_code,
                    "reason": f"Closure keyword detected: '{kw}'",
                    "final_url": final_url,
                }
                _LIVENESS_CACHE[url] = result
                return result

        # If 200/300 status code and no expired signals found, job is active
        is_live = status_code < 400
        result = {
            "url": url,
            "is_live": is_live,
            "is_expired": not is_live,
            "status_code": status_code,
            "reason": "Requisition verified active" if is_live else f"HTTP {status_code}",
            "final_url": final_url,
        }
        _LIVENESS_CACHE[url] = result
        return result

    except requests.Timeout:
        # On timeout, do not prematurely drop a potentially valid job; flag unverified
        return {
            "url": url,
            "is_live": True,
            "is_expired": False,
            "status_code": 408,
            "reason": "Connection timeout (assumed active)",
            "final_url": url,
        }
    except Exception as exc:
        logger.debug(f"Error checking url liveness {url}: {exc}")
        return {
            "url": url,
            "is_live": False,
            "is_expired": True,
            "status_code": 0,
            "reason": str(exc),
            "final_url": url,
        }


def filter_live_jobs_concurrently(jobs: list[Any], max_workers: int = 10) -> list[Any]:
    """Verify a batch of jobs in parallel, filtering out expired/dead links."""
    if not jobs:
        return []

    # Fast path: direct ATS and company career links fetched in the current scrape run are fresh from official APIs
    fresh_ats_sources = ("greenhouse_", "lever_", "ashby_", "direct_ats")
    
    verified_jobs = []
    candidates_to_check = []

    for job in jobs:
        source = getattr(job, "source", "") or ""
        source_type = getattr(job, "source_type", "") or ""
        # Direct ATS API calls return active postings directly from live company boards
        if any(source.startswith(prefix) for prefix in fresh_ats_sources) or source_type in ("direct_ats", "company_career_page"):
            verified_jobs.append(job)
        else:
            candidates_to_check.append(job)

    if not candidates_to_check:
        return verified_jobs

    def check_job(j: Any):
        res = verify_job_url(j.url)
        return j, res

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        checked = executor.map(check_job, candidates_to_check)
        for job, res in checked:
            if res.get("is_live", True):
                verified_jobs.append(job)
            else:
                logger.info(f"Filtering out expired/dead job: {job.title} at {job.company} ({res.get('reason')})")

    return verified_jobs

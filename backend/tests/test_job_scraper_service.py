from __future__ import annotations

from datetime import datetime, timedelta

from app.services.job_scraper_service import JobScraperService


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_linkedin_uses_actual_company_and_filters_old_posts(monkeypatch):
    recent_date = (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%d")
    old_date = (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d")

    html = f"""
    <html><body>
      <ul>
        <li class="jobs-search-results__list-item">
          <a class="base-card__full-link"
             href="https://www.linkedin.com/jobs/view/software-engineer-at-microsoft-1234567890?position=1&pageNum=0">
             View
          </a>
          <h3 class="base-search-card__title">Software Engineer</h3>
          <h4 class="base-search-card__subtitle"><a>Microsoft</a></h4>
          <span class="job-search-card__location">Bengaluru, India</span>
          <time datetime="{recent_date}">1 day ago</time>
        </li>
        <li class="jobs-search-results__list-item">
          <a class="base-card__full-link"
             href="https://www.linkedin.com/jobs/view/software-engineer-at-oldco-1234567891?position=2&pageNum=0">
             View
          </a>
          <h3 class="base-search-card__title">Software Engineer</h3>
          <h4 class="base-search-card__subtitle"><a>OldCo</a></h4>
          <time datetime="{old_date}">1 week ago</time>
        </li>
      </ul>
    </body></html>
    """

    service = JobScraperService()
    monkeypatch.setattr(service.session, "get", lambda *args, **kwargs: _FakeResponse(html))

    jobs = service.scrape_sources(["linkedin"], keywords=["software"], max_post_age_hours=48)

    assert len(jobs) == 1
    assert jobs[0].company == "Microsoft"
    assert jobs[0].url == "https://www.linkedin.com/jobs/view/software-engineer-at-microsoft-1234567890"


def test_linkedin_company_falls_back_to_url_slug(monkeypatch):
    html = """
    <html><body>
      <a href="https://in.linkedin.com/jobs/view/software-engineer-backend-at-doordash-4084261319?position=8&pageNum=0">
        Software Engineer, Backend
      </a>
    </body></html>
    """

    service = JobScraperService()
    monkeypatch.setattr(service.session, "get", lambda *args, **kwargs: _FakeResponse(html))

    jobs = service.scrape_sources(["linkedin"], keywords=["backend"], max_post_age_hours=None)

    assert len(jobs) == 1
    assert jobs[0].company.lower() == "doordash"


def test_generic_source_skips_non_job_links(monkeypatch):
    html = """
    <html><body>
      <a href="/in-en/about/company/industry-analyst">Industry Analyst Recognition</a>
      <div>
        <a href="/in-en/careers/jobdetails?id=ABC123">Software Engineer</a>
        <span>1 day ago</span>
      </div>
    </body></html>
    """

    service = JobScraperService()
    monkeypatch.setattr(service.session, "get", lambda *args, **kwargs: _FakeResponse(html))

    jobs = service.scrape_sources(["accenture"], keywords=["software"], max_post_age_hours=48)

    assert len(jobs) == 1
    assert jobs[0].title == "Software Engineer"
    assert "/careers/jobdetails" in jobs[0].url


def test_generic_source_keeps_job_when_posted_date_missing(monkeypatch):
    html = """
    <html><body>
      <div>
        <a href="/in-en/careers/jobdetails?id=XYZ999">Backend Engineer</a>
      </div>
    </body></html>
    """

    service = JobScraperService()
    monkeypatch.setattr(service.session, "get", lambda *args, **kwargs: _FakeResponse(html))

    jobs = service.scrape_sources(["accenture"], keywords=["backend"], max_post_age_hours=48)

    assert len(jobs) == 1
    assert jobs[0].title == "Backend Engineer"

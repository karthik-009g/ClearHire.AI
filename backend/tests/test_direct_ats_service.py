from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.direct_ats_service import DirectAtsService


def test_greenhouse_fetch_and_parse():
    service = DirectAtsService()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "id": 101,
                "title": "Staff Backend Engineer",
                "location": {"name": "Bengaluru, India"},
                "absolute_url": "https://boards.greenhouse.io/postman/jobs/101",
                "content": "<p>Build high scale API platform</p>",
                "updated_at": "2026-04-01T10:00:00Z",
            }
        ]
    }

    with patch.object(service.session, "get", return_value=mock_response):
        jobs = service.fetch_greenhouse_jobs("postman", "Postman")

    assert len(jobs) == 1
    assert jobs[0].company == "Postman"
    assert jobs[0].title == "Staff Backend Engineer"
    assert jobs[0].location == "Bengaluru, India"
    assert "Build high scale API platform" in (jobs[0].description or "")
    assert jobs[0].url == "https://boards.greenhouse.io/postman/jobs/101"


def test_lever_fetch_and_parse():
    service = DirectAtsService()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": "abc-202",
            "text": "Frontend Lead Engineer",
            "categories": {"location": "Bangalore / Remote"},
            "hostedUrl": "https://jobs.lever.co/urbancompany/abc-202",
            "description": "Architect modern frontend systems in Next.js and TypeScript",
            "createdAt": 1743500000000,
        }
    ]

    with patch.object(service.session, "get", return_value=mock_response):
        jobs = service.fetch_lever_jobs("urbancompany", "Urban Company")

    assert len(jobs) == 1
    assert jobs[0].company == "Urban Company"
    assert jobs[0].title == "Frontend Lead Engineer"
    assert jobs[0].location == "Bangalore / Remote"
    assert jobs[0].url == "https://jobs.lever.co/urbancompany/abc-202"


def test_direct_ats_filtering_by_keywords_and_india_location():
    service = DirectAtsService()

    def mock_fetch(entry):
        token = entry["token"]
        if token == "postman":
            from app.services.job_scraper_service import ScrapedJob
            from datetime import datetime, timezone
            return [
                ScrapedJob(
                    source="greenhouse_postman",
                    company="Postman",
                    title="Staff Backend Engineer",
                    url="https://boards.greenhouse.io/postman/jobs/101",
                    location="Bengaluru, India",
                    description="Python, Go, microservices",
                    scraped_at=datetime.now(timezone.utc),
                ),
                ScrapedJob(
                    source="greenhouse_postman",
                    company="Postman",
                    title="Account Executive",
                    url="https://boards.greenhouse.io/postman/jobs/102",
                    location="San Francisco, USA",
                    description="Enterprise sales",
                    scraped_at=datetime.now(timezone.utc),
                ),
            ]
        return []

    with patch.object(service, "fetch_company_jobs", side_effect=mock_fetch):
        results = service.fetch_all_direct_jobs(
            target_companies=["Postman"],
            keywords=["Backend"],
            india_or_remote_only=True,
            max_jobs=10,
        )

    assert len(results) == 1
    assert results[0].title == "Staff Backend Engineer"
    assert results[0].company == "Postman"


def test_direct_ats_caching_memoizes_subsequent_calls():
    from app.services.cache_service import CacheService, InMemoryCacheProvider
    from app.services.job_scraper_service import ScrapedJob
    from datetime import datetime, timezone

    cache = CacheService(provider=InMemoryCacheProvider())
    service = DirectAtsService(cache=cache)

    mock_job = ScrapedJob(
        source="greenhouse_postman",
        company="Postman",
        title="Senior Platform Engineer",
        url="https://boards.greenhouse.io/postman/jobs/201",
        location="Bengaluru, India",
        description="FastAPI, Redis, PostgreSQL",
        scraped_at=datetime.now(timezone.utc),
    )

    call_count = 0

    def mock_fetch(entry):
        nonlocal call_count
        call_count += 1
        if entry["token"] == "postman":
            return [mock_job]
        return []

    with patch.object(service, "fetch_company_jobs", side_effect=mock_fetch):
        first_call = service.fetch_all_direct_jobs(
            target_companies=["Postman"],
            keywords=["Platform"],
            india_or_remote_only=True,
            max_jobs=10,
        )
        assert len(first_call) == 1
        assert first_call[0].title == "Senior Platform Engineer"
        assert call_count == 1

        # Second identical call should hit the cache without calling fetch_company_jobs
        second_call = service.fetch_all_direct_jobs(
            target_companies=["Postman"],
            keywords=["Platform"],
            india_or_remote_only=True,
            max_jobs=10,
        )
        assert len(second_call) == 1
        assert second_call[0].title == "Senior Platform Engineer"
        assert call_count == 1  # Verify fetch_company_jobs was NOT called again

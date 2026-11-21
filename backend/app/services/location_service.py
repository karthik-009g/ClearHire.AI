"""Location normalization and preference matching for job discovery."""

from __future__ import annotations

import re


_LOCATION_ALIASES = {
    "bengaluru": ("bengaluru", "bangalore"),
    "bangalore": ("bengaluru", "bangalore"),
    "gurugram": ("gurugram", "gurgaon"),
    "gurgaon": ("gurugram", "gurgaon"),
    "mumbai": ("mumbai", "bombay"),
    "bombay": ("mumbai", "bombay"),
    "nyc": ("nyc", "new york", "new york city", "ny"),
    "new york": ("new york", "new york city", "nyc", "ny"),
    "new york city": ("new york", "new york city", "nyc", "ny"),
    "texas": ("texas", "tx"),
    "tx": ("texas", "tx"),
    "usa": ("usa", "us", "united states", "united states of america"),
    "us": ("usa", "us", "united states", "united states of america"),
    "united states": ("usa", "us", "united states", "united states of america"),
    "remote": ("remote", "work from home", "work from anywhere", "virtual"),
}
_INDIA_CITY_TERMS = {
    "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "bombay",
    "chennai", "delhi", "new delhi", "noida", "gurugram", "gurgaon",
    "kolkata", "ahmedabad", "kochi", "jaipur", "indore", "chandigarh",
}
_US_CITY_OR_STATE_TERMS = {
    "new york", "new york city", "nyc", "ny", "texas", "tx", "california",
    "ca", "washington", "wa", "florida", "fl", "illinois", "il",
    "massachusetts", "ma", "austin", "san francisco", "seattle", "boston",
}
_REMOTE_TERMS = ("remote", "work from home", "work from anywhere", "virtual")
_FOREIGN_MARKERS = (
    "usa", "united states", "america", "texas", "tx", "new york", "nyc",
    "california", "canada", "europe", "uk", "united kingdom", "australia",
    "singapore", "dubai",
)


def normalize_location(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_phrase = normalize_location(phrase)
    return bool(normalized_phrase and re.search(rf"(?<![a-z0-9]){re.escape(normalized_phrase)}(?![a-z0-9])", text))


def matches_locations(job_location: str | None, requested_locations: list[str]) -> bool:
    if not requested_locations:
        return True
    observed = normalize_location(job_location or "")
    if not observed:
        return False
    for requested in requested_locations:
        normalized = normalize_location(requested)
        if not normalized:
            continue
        aliases = _LOCATION_ALIASES.get(normalized, (normalized,))
        if any(_contains_phrase(observed, alias) for alias in aliases):
            return True
        if _contains_phrase(observed, "india") and normalized in _INDIA_CITY_TERMS:
            return True
        if normalized in {"usa", "us", "united states", "united states of america"} and any(_contains_phrase(observed, term) for term in _US_CITY_OR_STATE_TERMS):
            return True
        if any(_contains_phrase(observed, country) for country in ("united states", "united states of america", "usa")) and normalized in _US_CITY_OR_STATE_TERMS:
            return True
    return False


def india_or_remote_only(locations: list[str]) -> bool:
    """Keep India-only direct ATS filtering unless a non-India location is requested."""
    if not locations:
        return True
    for location in locations:
        normalized = normalize_location(location)
        if not normalized:
            continue
        if any(_contains_phrase(normalized, marker) for marker in _FOREIGN_MARKERS):
            return False
        if _contains_phrase(normalized, "india") or any(_contains_phrase(normalized, term) for term in _INDIA_CITY_TERMS):
            continue
        if any(_contains_phrase(normalized, term) for term in _REMOTE_TERMS):
            continue
        # An unfamiliar city is allowed to search broader public ATS boards.
        return False
    return True

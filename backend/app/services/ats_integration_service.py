"""ATS detection and integration capability metadata."""

from __future__ import annotations

from urllib.parse import urlparse


class ATSIntegrationService:
    KNOWN_ATS = {
        "greenhouse.io": {
            "name": "Greenhouse",
            "supports_browser_fill": True,
            "supports_api_submission": False,
        },
        "lever.co": {
            "name": "Lever",
            "supports_browser_fill": True,
            "supports_api_submission": False,
        },
        "myworkdayjobs.com": {
            "name": "Workday",
            "supports_browser_fill": False,
            "supports_api_submission": False,
        },
        "smartrecruiters.com": {
            "name": "SmartRecruiters",
            "supports_browser_fill": True,
            "supports_api_submission": False,
        },
        "ashbyhq.com": {
            "name": "Ashby",
            "supports_browser_fill": True,
            "supports_api_submission": False,
        },
    }

    def detect(self, application_url: str | None) -> dict:
        if not application_url:
            return self._unknown("missing_url")

        parsed = urlparse(application_url)
        host = parsed.netloc.lower()
        if not host:
            return self._unknown("invalid_url")

        for domain, metadata in self.KNOWN_ATS.items():
            if host == domain or host.endswith(f".{domain}"):
                return {
                    "ats": metadata["name"],
                    "detected": True,
                    "domain": domain,
                    "supports_browser_fill": metadata["supports_browser_fill"],
                    "supports_api_submission": metadata["supports_api_submission"],
                    "integration_status": "detected_fill_only",
                    "submission_policy": "user_submits_on_ats",
                }

        return self._unknown("unsupported_ats")

    @staticmethod
    def _unknown(reason: str) -> dict:
        return {
            "ats": "Unknown",
            "detected": False,
            "domain": None,
            "supports_browser_fill": False,
            "supports_api_submission": False,
            "integration_status": reason,
            "submission_policy": "user_submits_on_ats",
        }

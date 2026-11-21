"""n8n workflow event payloads and optional webhook dispatch."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from app.models import Application, JobDescription, ResumeVersion
from app.utils.config import settings


class N8NWorkflowService:
    ALLOWED_EVENTS = {
        "application_created",
        "application_reviewed",
        "application_marked_applied",
    }

    def build_application_event(
        self,
        event_type: str,
        application: Application,
        job: JobDescription | None,
        version: ResumeVersion | None,
    ) -> dict[str, Any]:
        if event_type not in self.ALLOWED_EVENTS:
            raise ValueError("unsupported n8n event type")

        return {
            "event_type": event_type,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "application": {
                "id": application.id,
                "status": application.status,
                "application_url": application.application_url,
                "notes": application.notes,
            },
            "job": {
                "id": job.id if job else None,
                "title": job.title if job else None,
                "company": job.company if job else None,
                "source": job.source if job else None,
            },
            "resume": {
                "version_id": version.id if version else None,
                "version_no": version.version_no if version else None,
            },
            "policy": {
                "notify_only": True,
                "never_submit_application": True,
                "user_review_required": True,
            },
        }

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not settings.n8n_enabled or not settings.n8n_webhook_url:
            return {
                "dispatched": False,
                "status": "disabled",
                "payload": payload,
            }

        response = requests.post(
            settings.n8n_webhook_url,
            json=payload,
            timeout=settings.rag_request_timeout_seconds,
        )
        response.raise_for_status()
        return {
            "dispatched": True,
            "status": "sent",
            "status_code": response.status_code,
        }

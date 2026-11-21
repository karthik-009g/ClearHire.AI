"""Browser autofill planning without autonomous submission."""

from __future__ import annotations

from typing import Any


class BrowserAutofillService:
    FIELD_ALIASES = {
        "full_name": ["name", "full name", "candidate name"],
        "email": ["email", "email address"],
        "phone": ["phone", "mobile", "telephone"],
        "target_role": ["role", "position", "job title"],
        "target_company": ["company", "employer"],
        "location_preference": ["location", "preferred location"],
        "skills": ["skills", "technical skills"],
        "experience_highlights": ["experience", "work experience", "summary"],
    }

    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return "\n".join(str(item).strip() for item in value if str(item).strip())
        return str(value).strip()

    def build_plan(self, autofill_payload: dict[str, Any] | None) -> dict[str, Any]:
        payload = autofill_payload if isinstance(autofill_payload, dict) else {}
        fields = []
        missing_required_fields = []

        for field_name, aliases in self.FIELD_ALIASES.items():
            value = self._stringify(payload.get(field_name))
            if field_name in {"full_name", "email", "phone"} and not value:
                missing_required_fields.append(field_name)

            fields.append(
                {
                    "field": field_name,
                    "value": value,
                    "aliases": aliases,
                    "fill_when_found": bool(value),
                }
            )

        review_required = bool(payload.get("review_required", True)) or bool(missing_required_fields)
        return {
            "mode": "browser_fill_plan",
            "policy": {
                "fill_only": True,
                "never_submit": True,
                "requires_user_review": True,
            },
            "fields": fields,
            "missing_required_fields": missing_required_fields,
            "ready_for_autofill": not missing_required_fields,
            "review_required": review_required,
            "instructions": (
                "Use this plan to prefill matching fields in a browser extension or manual helper. "
                "The user must review every field and submit on the employer portal themselves."
            ),
        }

"""Notification and morning digest engine with multi-channel delivery.

Digests include public ATS postings, candidate-tracked application follow-ups, and
pipeline summaries. A posting source does not predict whether an employer will respond.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import logging
from html import escape as escape_html
from typing import Any
from urllib.parse import urlsplit
import requests

from app.models.jobs import DigestLog, JobPosting, UserPreference
from app.models.resume import Application, JobDescription
from app.services.direct_ats_service import DirectAtsService
from app.utils.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DigestJobItem:
    title: str
    company: str
    location: str
    url: str
    ats_type: str
    ghosting_risk: str
    ghosting_score: int
    salary_range: str | None = None


@dataclass
class GhostingActionItem:
    application_id: int
    company: str
    role: str
    days_elapsed: int
    recommended_action: str


@dataclass
class FunnelMetrics:
    total_tracked: int = 0
    saved: int = 0
    applied: int = 0
    screening: int = 0
    interviewing: int = 0
    offer: int = 0
    ghosted: int = 0
    rejected: int = 0
    screen_conversion_rate: float = 0.0
    interview_conversion_rate: float = 0.0
    offer_rate: float = 0.0
    ghosting_rate: float = 0.0
    avg_days_to_response: float = 0.0


@dataclass
class DigestPayload:
    date_str: str
    candidate_name: str
    target_role: str
    top_jobs: list[DigestJobItem] = field(default_factory=list)
    ghosting_alerts: list[GhostingActionItem] = field(default_factory=list)
    funnel_metrics: FunnelMetrics = field(default_factory=FunnelMetrics)
    telegram_text: str = ""
    whatsapp_text: str = ""
    email_html: str = ""
    email_subject: str = ""


@dataclass
class DispatchResult:
    channel: str
    recipient: str
    status: str  # sent, simulated, failed, skipped
    detail: str


class NotificationDigestService:
    def __init__(self, direct_ats: DirectAtsService | None = None) -> None:
        self.direct_ats = direct_ats or DirectAtsService()

    @staticmethod
    def _safe_http_url(value: str) -> str | None:
        try:
            parsed = urlsplit((value or "").strip())
        except ValueError:
            return None
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None
        return value.strip()

    def compute_funnel_analytics(
        self, applications: list[Application], jobs_map: dict[int, JobDescription] | None = None
    ) -> FunnelMetrics:
        if not applications:
            return FunnelMetrics()

        now = datetime.utcnow()
        saved = 0
        applied = 0
        screening = 0
        interviewing = 0
        offer = 0
        ghosted = 0
        rejected = 0
        response_days_list = []

        for app in applications:
            st = (app.status or "").lower()
            up_time = app.updated_at or now
            days = (now - up_time).days

            if st in {"bookmarked", "draft"}:
                saved += 1
            elif st in {"pending", "review_required", "reviewed"}:
                saved += 1
            elif st == "applied":
                applied += 1
                if days >= 14:
                    ghosted += 1
            elif st == "screening":
                applied += 1
                screening += 1
                response_days_list.append(min(days, 14))
            elif st == "interviewing":
                applied += 1
                screening += 1
                interviewing += 1
                response_days_list.append(min(days, 21))
            elif st == "offer":
                applied += 1
                screening += 1
                interviewing += 1
                offer += 1
                response_days_list.append(min(days, 30))
            elif st == "ghosted":
                applied += 1
                ghosted += 1
            elif st == "rejected":
                applied += 1
                rejected += 1
                response_days_list.append(min(days, 20))

        screen_conv = round((screening / applied * 100), 1) if applied > 0 else 0.0
        interview_conv = round((interviewing / screening * 100), 1) if screening > 0 else 0.0
        offer_conv = round((offer / applied * 100), 1) if applied > 0 else 0.0
        ghost_rate = round((ghosted / applied * 100), 1) if applied > 0 else 0.0
        avg_days = round(sum(response_days_list) / len(response_days_list), 1) if response_days_list else 0.0

        return FunnelMetrics(
            total_tracked=len(applications),
            saved=saved,
            applied=applied,
            screening=screening,
            interviewing=interviewing,
            offer=offer,
            ghosted=ghosted,
            rejected=rejected,
            screen_conversion_rate=screen_conv,
            interview_conversion_rate=interview_conv,
            offer_rate=offer_conv,
            ghosting_rate=ghost_rate,
            avg_days_to_response=avg_days,
        )

    def build_morning_digest(
        self,
        candidate_name: str = "Candidate",
        preferences: UserPreference | None = None,
        applications: list[Application] | None = None,
        jobs_map: dict[int, JobDescription] | None = None,
        limit_jobs: int = 5,
    ) -> DigestPayload:
        now = datetime.utcnow()
        date_str = now.strftime("%A, %d %B %Y")
        target_role = getattr(preferences, "target_role", "Software Engineer") or "Software Engineer"
        target_companies_raw = getattr(preferences, "target_companies_csv", "") or ""
        target_companies = {c.strip().lower() for c in target_companies_raw.split(",") if c.strip()}

        # 1. Fetch live public ATS postings; the source does not predict employer response.
        top_jobs: list[DigestJobItem] = []
        try:
            candidates_jobs = self.direct_ats.get_direct_jobs()
            for dj in candidates_jobs:
                comp_name = (dj.company or "").lower()
                if target_companies and not any(tc in comp_name for tc in target_companies):
                    continue
                top_jobs.append(
                    DigestJobItem(
                        title=dj.title,
                        company=dj.company,
                        location=dj.location or "Unknown location",
                        url=dj.url,
                        ats_type=getattr(dj, "ats_type", dj.source),
                        ghosting_risk="unknown",
                        ghosting_score=0,
                        salary_range=getattr(dj, "salary_range", None),
                    )
                )
                if len(top_jobs) >= limit_jobs:
                    break
        except Exception as exc:
            logger.warning("Could not fetch direct jobs for digest: %s", exc)

        # 2. Identify 14-day Ghosting Action Items
        ghosting_alerts: list[GhostingActionItem] = []
        app_list = applications or []
        jmap = jobs_map or {}

        for app in app_list:
            up_time = app.updated_at or now
            days = (now - up_time).days
            if app.status == "ghosted" or (app.status in {"applied", "screening"} and days >= 14):
                job_desc = jmap.get(app.job_description_id)
                comp = job_desc.company if job_desc and job_desc.company else "Target Company"
                role = job_desc.title if job_desc and job_desc.title else "Role"
                rec_action = (
                    "Over 14 days without response. Send a 7-day follow-up InMail or pivot to active direct ATS opening."
                    if days < 21
                    else "21+ days stalled. Mark as Ghosted in Kanban to preserve pipeline focus."
                )
                ghosting_alerts.append(
                    GhostingActionItem(
                        application_id=app.id,
                        company=comp,
                        role=role,
                        days_elapsed=days,
                        recommended_action=rec_action,
                    )
                )

        # 3. Compute Funnel Analytics
        funnel = self.compute_funnel_analytics(app_list, jmap)

        # 4. Synthesize Multi-Channel Templates
        tg_text = self._format_telegram(candidate_name, date_str, target_role, top_jobs, ghosting_alerts, funnel)
        wa_text = self._format_whatsapp(candidate_name, date_str, target_role, top_jobs, ghosting_alerts, funnel)
        email_html = self._format_email(candidate_name, date_str, target_role, top_jobs, ghosting_alerts, funnel)
        email_subj = f"🌅 ClearHire Morning Briefing: {len(top_jobs)} public ATS postings for {candidate_name}"

        return DigestPayload(
            date_str=date_str,
            candidate_name=candidate_name,
            target_role=target_role,
            top_jobs=top_jobs,
            ghosting_alerts=ghosting_alerts,
            funnel_metrics=funnel,
            telegram_text=tg_text,
            whatsapp_text=wa_text,
            email_html=email_html,
            email_subject=email_subj,
        )

    def _format_telegram(
        self,
        name: str,
        date_str: str,
        role: str,
        jobs: list[DigestJobItem],
        alerts: list[GhostingActionItem],
        funnel: FunnelMetrics,
    ) -> str:
        lines = [
            f"⚡ *ClearHire.AI Morning Briefing* | {date_str}",
            f"Good morning *{name}*! Here is your recruitment intelligence update for *{role}*.\n",
            f"📊 *Pipeline Health & Funnel*",
            f"• Total Applied: *{funnel.applied}* | Interviews: *{funnel.interviewing}* | Offers: *{funnel.offer}*",
            f"• Screen-to-Interview Conversion: *{funnel.screen_conversion_rate}%*",
            f"• No-update / marked-ghosted rate: *{funnel.ghosting_rate}%* (Avg response: {funnel.avg_days_to_response}d)\n",
        ]

        if alerts:
            lines.append("⚠️ *Follow-up reminders (14+ days without an update)*")
            for a in alerts[:3]:
                lines.append(f"• *{a.company}* ({a.role}) - {a.days_elapsed}d waiting. {a.recommended_action}")
            lines.append("")

        lines.append(f"🎯 *Public ATS postings (confirm availability on the employer portal)*")
        for i, j in enumerate(jobs[:4], 1):
            salary = f" | {j.salary_range}" if j.salary_range else ""
            lines.append(f"{i}. *{j.title}* at *{j.company}*")
            lines.append(f"   📍 {j.location} • ATS: {j.ats_type.upper()}{salary}")
            lines.append(f"   🔗 [Direct Apply Portal]({j.url})")

        lines.append("\n_Empowered by ClearHire.AI • Public source links and candidate-controlled applications_")
        return "\n".join(lines)

    def _format_whatsapp(
        self,
        name: str,
        date_str: str,
        role: str,
        jobs: list[DigestJobItem],
        alerts: list[GhostingActionItem],
        funnel: FunnelMetrics,
    ) -> str:
        lines = [
            f"🌅 *ClearHire.AI Morning Digest* ({date_str})",
            f"Hi *{name}*, here are your fresh direct openings and pipeline status for *{role}*:\n",
            f"📈 *Pipeline Metrics*",
            f"• Applied: *{funnel.applied}* | Screenings: *{funnel.screening}* | Offers: *{funnel.offer}*",
            f"• Pipeline No-update / marked-ghosted rate: *{funnel.ghosting_rate}%*\n",
        ]

        if alerts:
            lines.append("⚠️ *Follow-up watch (>14d without an update)*")
            for a in alerts[:2]:
                lines.append(f"• *{a.company}* ({a.days_elapsed}d waiting): Recommend sending InMail follow-up")
            lines.append("")

        lines.append("🎯 *Public ATS postings (verify employer and role details)*")
        for i, j in enumerate(jobs[:3], 1):
            lines.append(f"{i}. *{j.title}* - {j.company} ({j.location})")
            lines.append(f"   Apply: {j.url}")

        lines.append("\n_ClearHire.AI: Track applications and review public job sources_")
        return "\n".join(lines)

    def _format_email(
        self,
        name: str,
        date_str: str,
        role: str,
        jobs: list[DigestJobItem],
        alerts: list[GhostingActionItem],
        funnel: FunnelMetrics,
    ) -> str:
        jobs_html = "".join([
            f"""
            <div style="background: #082542; border: 1px solid #1c4b78; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <h4 style="margin: 0; color: #51d2ff; font-size: 16px;">{escape_html(j.title)}</h4>
                <span style="font-size: 12px; color: #66e9ad; background: rgba(102, 233, 173, 0.15); padding: 2px 8px; border-radius: 4px;">Public ATS posting</span>
              </div>
              <p style="margin: 4px 0 8px; color: #b7d7f2; font-size: 13px;">{escape_html(j.company)} &bull; {escape_html(j.location)} &bull; Direct {escape_html(j.ats_type.upper())}</p>
              {self._email_job_link(j.url)}
            </div>
            """
            for j in jobs
        ])

        alerts_html = ""
        if alerts:
            alert_items = "".join([
                f"<li style='margin-bottom: 6px;'><strong>{escape_html(a.company)}</strong> ({escape_html(a.role)}): {a.days_elapsed} days waiting &mdash; <span style='color: #ff8484;'>{escape_html(a.recommended_action)}</span></li>"
                for a in alerts[:3]
            ])
            alerts_html = f"""
            <div style="background: rgba(70, 20, 30, 0.7); border: 1px solid rgba(255, 100, 100, 0.4); border-radius: 8px; padding: 14px; margin-bottom: 20px;">
              <h4 style="margin: 0 0 8px; color: #ff8484;">Application follow-up reminders</h4>
              <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #e9f5ff;">{alert_items}</ul>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="margin: 0; padding: 20px; background-color: #041327; color: #e9f5ff; font-family: 'Segoe UI', Tahoma, sans-serif;">
          <div style="max-width: 600px; margin: 0 auto; background: #081d33; border: 1px solid #153e66; border-radius: 12px; padding: 24px;">
            <div style="border-bottom: 1px solid #1c4b78; padding-bottom: 14px; margin-bottom: 18px;">
              <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #51d2ff; font-weight: bold;">ClearHire.AI Intelligence Briefing</span>
              <h2 style="margin: 6px 0 0; color: #ffffff;">Morning Recruitment Briefing</h2>
              <p style="margin: 2px 0 0; font-size: 13px; color: #b7d7f2;">{escape_html(date_str)} &bull; Curated for {escape_html(name)} ({escape_html(role)})</p>
            </div>

            <!-- Funnel Strip -->
            <div style="display: flex; gap: 8px; margin-bottom: 20px;">
              <div style="flex: 1; background: #0b2b4d; padding: 10px; border-radius: 8px; text-align: center;">
                <div style="font-size: 20px; font-weight: bold; color: #81c995;">{funnel.applied}</div>
                <div style="font-size: 11px; color: #b7d7f2;">Applied</div>
              </div>
              <div style="flex: 1; background: #0b2b4d; padding: 10px; border-radius: 8px; text-align: center;">
                <div style="font-size: 20px; font-weight: bold; color: #c58af9;">{funnel.screening}</div>
                <div style="font-size: 11px; color: #b7d7f2;">Screenings</div>
              </div>
              <div style="flex: 1; background: #0b2b4d; padding: 10px; border-radius: 8px; text-align: center;">
                <div style="font-size: 20px; font-weight: bold; color: #5bb974;">{funnel.offer}</div>
                <div style="font-size: 11px; color: #b7d7f2;">Offers</div>
              </div>
              <div style="flex: 1; background: #0b2b4d; padding: 10px; border-radius: 8px; text-align: center;">
                <div style="font-size: 20px; font-weight: bold; color: #ff8484;">{funnel.ghosting_rate}%</div>
                <div style="font-size: 11px; color: #b7d7f2;">No-update / marked-ghosted rate</div>
              </div>
            </div>

            {alerts_html}

            <h3 style="color: #66e9ad; margin: 0 0 12px;">🎯 Public ATS postings (verify availability)</h3>
            {jobs_html}

            <div style="text-align: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid #1c4b78; font-size: 12px; color: #7ba6cb;">
              Public ATS sources &bull; Candidate-controlled applications &bull; Verify current availability
            </div>
          </div>
        </body>
        </html>
        """

    def _email_job_link(self, value: str) -> str:
        safe_url = self._safe_http_url(value)
        if not safe_url:
            return '<span style="font-size: 12px; color: #b7d7f2;">No safe application URL available</span>'
        return (
            f'<a href="{escape_html(safe_url, quote=True)}" '
            'style="background: #2fb3ff; color: #041327; text-decoration: none; padding: 6px 14px; '
            'border-radius: 6px; font-weight: bold; font-size: 12px; display: inline-block;">Direct Apply &rarr;</a>'
        )

    def dispatch_digest(
        self,
        digest: DigestPayload,
        channels: list[str],
        recipient_info: dict[str, Any],
        user_id: str | None = None,
        db_session: Any | None = None,
    ) -> list[DispatchResult]:
        results: list[DispatchResult] = []

        for ch in channels:
            ch_lower = ch.strip().lower()
            if ch_lower == "telegram":
                chat_id = recipient_info.get("telegram_chat_id")
                bot_token = getattr(settings, "telegram_bot_token", None)
                if not chat_id:
                    res = DispatchResult(channel="telegram", recipient="", status="skipped", detail="No Telegram chat ID is configured")
                elif bot_token:
                    try:
                        resp = requests.post(
                            f"https://api.telegram.org/bot{bot_token}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": digest.telegram_text,
                                "parse_mode": "Markdown",
                                "disable_web_page_preview": True,
                            },
                            timeout=10,
                        )
                        if resp.ok:
                            res = DispatchResult(channel="telegram", recipient=chat_id, status="sent", detail="Delivered via Telegram Bot")
                        else:
                            res = DispatchResult(channel="telegram", recipient=chat_id, status="failed", detail=f"Telegram API {resp.status_code}: {resp.text}")
                    except Exception as err:
                        res = DispatchResult(channel="telegram", recipient=chat_id, status="failed", detail=str(err))
                else:
                    # Simulated dispatch mode
                    res = DispatchResult(
                        channel="telegram",
                        recipient=chat_id,
                        status="simulated",
                        detail="Simulated delivery (set TELEGRAM_BOT_TOKEN to send to live Telegram)",
                    )
                results.append(res)
                self._record_log(db_session, user_id, "telegram", res.recipient, digest.email_subject, digest.telegram_text, digest.funnel_metrics, res.status, res.detail)

            elif ch_lower == "whatsapp":
                phone = recipient_info.get("whatsapp_number")
                sid = getattr(settings, "twilio_account_sid", None)
                auth = getattr(settings, "twilio_auth_token", None)
                from_no = getattr(settings, "twilio_whatsapp_from", None)
                if not phone:
                    res = DispatchResult(channel="whatsapp", recipient="", status="skipped", detail="No WhatsApp number is configured")
                elif sid and auth and from_no:
                    try:
                        resp = requests.post(
                            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                            auth=(sid, auth),
                            data={
                                "From": f"whatsapp:{from_no}",
                                "To": f"whatsapp:{phone}",
                                "Body": digest.whatsapp_text,
                            },
                            timeout=10,
                        )
                        if resp.ok:
                            res = DispatchResult(channel="whatsapp", recipient=phone, status="sent", detail="Delivered via Twilio WhatsApp")
                        else:
                            res = DispatchResult(channel="whatsapp", recipient=phone, status="failed", detail=f"Twilio API {resp.status_code}")
                    except Exception as err:
                        res = DispatchResult(channel="whatsapp", recipient=phone, status="failed", detail=str(err))
                else:
                    res = DispatchResult(
                        channel="whatsapp",
                        recipient=phone,
                        status="simulated",
                        detail="Simulated delivery (configure TWILIO_ACCOUNT_SID to send live WhatsApp)",
                    )
                results.append(res)
                self._record_log(db_session, user_id, "whatsapp", res.recipient, digest.email_subject, digest.whatsapp_text, digest.funnel_metrics, res.status, res.detail)

            elif ch_lower == "email":
                email_addr = (recipient_info.get("email") or "").strip()
                sender_email = (settings.smtp_sender_email or "").strip()
                if not email_addr:
                    res = DispatchResult(channel="email", recipient="", status="skipped", detail="No email recipient is configured")
                elif settings.automation_email_enabled and settings.smtp_host and sender_email:
                    try:
                        import smtplib
                        from email.mime.multipart import MIMEMultipart
                        from email.mime.text import MIMEText

                        msg = MIMEMultipart("alternative")
                        msg["Subject"] = digest.email_subject
                        msg["From"] = sender_email
                        msg["To"] = email_addr
                        msg.attach(MIMEText(digest.email_html, "html"))

                        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                            if settings.smtp_use_tls:
                                server.starttls()
                            if settings.smtp_username and settings.smtp_password:
                                server.login(settings.smtp_username, settings.smtp_password)
                            server.send_message(msg)

                        res = DispatchResult(channel="email", recipient=email_addr, status="sent", detail=f"Delivered via SMTP to {email_addr}")
                    except Exception as err:
                        res = DispatchResult(channel="email", recipient=email_addr, status="failed", detail=str(err))
                else:
                    res = DispatchResult(
                        channel="email",
                        recipient=email_addr,
                        status="simulated",
                        detail="Simulated delivery (SMTP disabled or sender configuration incomplete; logged for in-app viewing)",
                    )
                results.append(res)
                self._record_log(db_session, user_id, "email", res.recipient, digest.email_subject, digest.email_html, digest.funnel_metrics, res.status, res.detail)

        return results

    def _record_log(
        self,
        db_session: Any | None,
        user_id: str | None,
        channel: str,
        recipient: str,
        subject: str,
        content: str,
        metrics: FunnelMetrics,
        status: str,
        detail: str,
    ) -> None:
        if not db_session:
            return
        try:
            log = DigestLog(
                user_id=user_id,
                channel=channel,
                recipient=recipient,
                subject=subject,
                content=content,
                metrics_snapshot=asdict(metrics),
                status=status,
                error_message=detail if status in {"failed", "skipped"} else None,
                created_at=datetime.utcnow(),
            )
            db_session.add(log)
            db_session.commit()
        except Exception as exc:
            logger.warning("Could not persist DigestLog: %s", exc)

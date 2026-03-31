"""User-configurable scheduler for automated scraping and matching."""

from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models import UserPreference
from app.services.automation_service import AutomationService
from app.utils.config import settings

scheduler = BackgroundScheduler(timezone=settings.default_schedule_timezone)
automation = AutomationService()


def _job_id(user_id: str) -> str:
    return f"user-automation-{user_id}"


def _run_user_job(user_id: str) -> None:
    db = SessionLocal()
    try:
        automation.run_user_automation(db=db, user_id=user_id, trigger="schedule")
    except Exception:
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        _load_scheduled_users()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def _load_scheduled_users() -> None:
    db = SessionLocal()
    try:
        prefs = db.query(UserPreference).filter(UserPreference.auto_schedule_enabled == True).all()  # noqa: E712
        for pref in prefs:
            if not pref.user_id:
                continue
            sync_user_schedule(
                user_id=pref.user_id,
                enabled=pref.auto_schedule_enabled,
                schedule_time=pref.schedule_time,
                timezone_name=pref.schedule_timezone,
            )
    finally:
        db.close()


def sync_user_schedule(
    user_id: str,
    enabled: bool,
    schedule_time: str,
    timezone_name: str,
) -> None:
    job_id = _job_id(user_id)

    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)

    if not enabled:
        return

    try:
        hour_str, minute_str = schedule_time.split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
    except Exception:
        hour = 9
        minute = 0

    trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone_name or settings.default_schedule_timezone)
    scheduler.add_job(
        _run_user_job,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        kwargs={"user_id": user_id},
        next_run_time=datetime.now(),
    )


def remove_user_schedule(user_id: str) -> None:
    job_id = _job_id(user_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def run_on_login(user_id: str) -> dict:
    db = SessionLocal()
    try:
        return automation.run_user_automation(db=db, user_id=user_id, trigger="login")
    finally:
        db.close()


def run_on_upload(user_id: str) -> dict:
    db = SessionLocal()
    try:
        return automation.run_user_automation(db=db, user_id=user_id, trigger="upload")
    finally:
        db.close()

"""Retention cleanup for resumes and files."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Resume
from app.services.storage import StorageProvider


def cleanup_expired_resumes(db: Session, storage: StorageProvider) -> tuple[int, int]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expired = db.query(Resume).filter(Resume.expires_at <= now).all()

    deleted_files = 0
    deleted_records = 0

    for item in expired:
        if storage.delete_file(item.stored_path):
            deleted_files += 1
        db.delete(item)
        deleted_records += 1

    db.commit()
    return deleted_records, deleted_files

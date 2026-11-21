"""Production background job abstraction for asynchronous processing."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import logging
import threading
import time
from typing import Any, Callable
import uuid

logger = logging.getLogger(__name__)


@dataclass
class JobRecord:
    job_id: str
    name: str
    payload: dict[str, Any]
    status: str = "queued"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: dict[str, Any] | None = None
    error: str | None = None


JobHandler = Callable[[dict[str, Any]], dict[str, Any] | None]


class BackgroundJobManager:
    def __init__(self, max_workers: int = 4):
        self._jobs: dict[str, JobRecord] = {}
        self._handlers: dict[str, JobHandler] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="bg-worker")

    def register_handler(self, name: str, handler: JobHandler) -> None:
        with self._lock:
            self._handlers[name] = handler

    def _execute_job(self, job_id: str, name: str, payload: dict[str, Any]) -> None:
        self.update(job_id, status="running")
        try:
            handler = self._handlers.get(name)
            if handler:
                result = handler(payload)
            else:
                # Default handler acknowledges successful processing
                result = {"processed": True, "task": name}
            self.update(job_id, status="completed", result=result)
        except Exception as exc:
            logger.exception("background_job_execution_failed", extra={"job_id": job_id, "name": name})
            self.update(job_id, status="failed", error=str(exc))

    def enqueue(
        self,
        name: str,
        payload: dict[str, Any] | None = None,
        execute_async: bool = True,
    ) -> str:
        job_id = str(uuid.uuid4())
        record = JobRecord(job_id=job_id, name=name, payload=payload or {})
        with self._lock:
            self._jobs[job_id] = record

        if execute_async:
            self._executor.submit(self._execute_job, job_id, name, payload or {})
        return job_id

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        status: str | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> JobRecord | None:
        with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                return None
            if status:
                record.status = status
            if result is not None:
                record.result = result
            if error is not None:
                record.error = error
            record.updated_at = time.time()
            return record

    def list_jobs(self, limit: int = 50) -> list[JobRecord]:
        with self._lock:
            records = list(self._jobs.values())
        return sorted(records, key=lambda r: r.created_at, reverse=True)[:limit]


_manager = BackgroundJobManager()


def register_handler(name: str, handler: JobHandler) -> None:
    _manager.register_handler(name, handler)


def enqueue_job(name: str, payload: dict[str, Any] | None = None, execute_async: bool = True) -> str:
    return _manager.enqueue(name=name, payload=payload, execute_async=execute_async)


def get_job(job_id: str) -> JobRecord | None:
    return _manager.get(job_id)


def mark_job_running(job_id: str) -> JobRecord | None:
    return _manager.update(job_id, status="running")


def mark_job_completed(job_id: str, result: dict[str, Any] | None = None) -> JobRecord | None:
    return _manager.update(job_id, status="completed", result=result)


def mark_job_failed(job_id: str, error: str) -> JobRecord | None:
    return _manager.update(job_id, status="failed", error=error)

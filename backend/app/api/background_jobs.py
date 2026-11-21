"""Background job enqueue and status endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.background_jobs import enqueue_job, get_job

router = APIRouter()


class EnqueueJobRequest(BaseModel):
    name: str
    payload: dict | None = None


class JobStatusResponse(BaseModel):
    job_id: str
    name: str
    status: str
    payload: dict
    result: dict | None = None
    error: str | None = None


@router.post("/enqueue")
def enqueue_background_job(request: EnqueueJobRequest):
    job_id = enqueue_job(request.name, request.payload)
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=500, detail="Background job not created")
    return {"job_id": job.job_id, "status": job.status}


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_background_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.job_id,
        name=job.name,
        status=job.status,
        payload=job.payload,
        result=job.result,
        error=job.error,
    )

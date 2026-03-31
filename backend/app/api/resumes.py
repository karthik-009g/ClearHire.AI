"""Resume upload, parse, and JD matching APIs."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timedelta
from hashlib import sha256

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.schemas.resume import CleanupResponse, MatchRequest, MatchResponse, ResumeDetailResponse, ResumeUploadResponse, TailorRequest, TailorResponse, ResumeVersionItem, ResumeVersionsResponse
from app.database import get_db
from app.models import JobDescription, MatchResult, Resume, ResumeVersion, User
from app.services.matcher_service import ResumeMatcherService
from app.services.parser_service import ResumeParserService
from app.services.retention_service import cleanup_expired_resumes
from app.services.storage import get_storage_provider
from app.services.tailor_service import ResumeTailorService
from app.services.workflow_service import run_resume_analysis_flow
from app.services.scheduler_service import run_on_upload
from app.utils.auth import get_current_user_optional
from app.utils.config import settings
from app.utils.file_security import FileValidationError, validate_resume_upload

router = APIRouter()

parser_service = ResumeParserService(spacy_model=settings.spacy_model)
matcher_service = ResumeMatcherService(embedding_model_name=settings.embedding_model_name)
storage = get_storage_provider(settings.storage_root)
tailor_service = ResumeTailorService()


def _create_tailored_version(
    request: TailorRequest,
    db: Session,
    current_user: User | None,
) -> tuple[Resume, ResumeVersion, dict, dict, JobDescription, MatchResult]:
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if settings.auth_enabled and current_user and resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this resume")

    source_version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .filter(ResumeVersion.version_no == request.source_version_no)
        .first()
    )
    if not source_version:
        raise HTTPException(status_code=404, detail="Requested source version not found")

    latest_version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_no.desc())
        .first()
    )
    if not latest_version:
        raise HTTPException(status_code=404, detail="No versions available")

    flow_output = run_resume_analysis_flow(
        resume_text=source_version.content_text,
        jd_text=request.jd_text,
        parser=parser_service,
        matcher=matcher_service,
    )
    match_data = flow_output["match"]

    job = JobDescription(
        title=request.role,
        company=request.company,
        source=request.source,
        jd_text=request.jd_text,
    )
    db.add(job)
    db.flush()

    match_result = MatchResult(
        resume_id=resume.id,
        job_description_id=job.id,
        keyword_score=match_data["keyword_score"],
        embedding_score=match_data["embedding_score"],
        total_score=match_data["total_score"],
        gaps={"missing_keywords": match_data["missing_keywords"]},
        explanation={**match_data["explanation"], "engine": flow_output.get("engine", "service-pipeline")},
    )
    db.add(match_result)

    tailored = tailor_service.tailor_resume(
        resume_text=source_version.content_text,
        jd_text=request.jd_text,
        missing_keywords=match_data["missing_keywords"],
        matched_keywords=match_data["matched_keywords"],
        candidate_name=request.candidate_name,
        role=request.role,
        company=request.company,
        include_cover_letter=request.include_cover_letter,
    )

    new_version = ResumeVersion(
        resume_id=resume.id,
        version_no=latest_version.version_no + 1,
        content_text=tailored["tailored_resume_text"],
        embedding=matcher_service.embed_text(tailored["tailored_resume_text"]),
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    db.refresh(match_result)
    db.refresh(job)

    return resume, source_version, match_data, tailored, job, match_result


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    filename = file.filename or "resume"
    content = await file.read()
    try:
        extension = validate_resume_upload(
            filename=filename,
            content_type=file.content_type,
            content=content,
            allowed_extensions=settings.allowed_upload_extensions,
            allowed_mime_types=settings.allowed_upload_mime_types,
            max_upload_mb=settings.max_upload_mb,
        )
    except FileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        resume_text = parser_service.extract_text(content, extension)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse resume: {exc}") from exc

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Extracted resume text is empty")

    parsed_summary = parser_service.parse_resume(resume_text)
    stored_path = storage.save_file(content, filename)
    expiry = datetime.utcnow() + timedelta(days=settings.resume_retention_days)

    resume = Resume(
        user_id=current_user.id if current_user else None,
        original_filename=filename,
        stored_path=stored_path,
        content_hash=sha256(content).hexdigest(),
        parsed_summary=parsed_summary,
        expires_at=expiry,
    )
    db.add(resume)
    db.flush()

    version = ResumeVersion(
        resume_id=resume.id,
        version_no=1,
        content_text=resume_text,
        embedding=matcher_service.embed_text(resume_text),
    )
    db.add(version)
    db.commit()
    db.refresh(resume)

    if current_user and background_tasks is not None:
        background_tasks.add_task(run_on_upload, current_user.id)

    return ResumeUploadResponse(
        resume_id=resume.id,
        original_filename=resume.original_filename,
        created_at=resume.created_at,
        expires_at=resume.expires_at,
        parsed_summary=resume.parsed_summary,
    )


@router.post("/match", response_model=MatchResponse)
def match_resume(
    request: MatchRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if settings.auth_enabled and current_user and resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this resume")

    version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_no.desc())
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Resume version not found")

    flow_output = run_resume_analysis_flow(
        resume_text=version.content_text,
        jd_text=request.jd_text,
        parser=parser_service,
        matcher=matcher_service,
    )
    match_data = flow_output["match"]

    job = JobDescription(
        title=request.title,
        company=request.company,
        source=request.source,
        jd_text=request.jd_text,
    )
    db.add(job)
    db.flush()

    match_result = MatchResult(
        resume_id=resume.id,
        job_description_id=job.id,
        keyword_score=match_data["keyword_score"],
        embedding_score=match_data["embedding_score"],
        total_score=match_data["total_score"],
        gaps={"missing_keywords": match_data["missing_keywords"]},
        explanation={**match_data["explanation"], "engine": flow_output.get("engine", "service-pipeline")},
    )
    db.add(match_result)
    db.commit()
    db.refresh(match_result)

    return MatchResponse(
        match_id=match_result.id,
        keyword_score=match_result.keyword_score,
        embedding_score=match_result.embedding_score,
        total_score=match_result.total_score,
        missing_keywords=match_data["missing_keywords"],
        explanation=match_result.explanation,
    )


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume_detail(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if settings.auth_enabled and current_user and resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this resume")

    latest_version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_no.desc())
        .first()
    )

    return ResumeDetailResponse(
        id=resume.id,
        original_filename=resume.original_filename,
        created_at=resume.created_at,
        expires_at=resume.expires_at,
        parsed_summary=resume.parsed_summary,
        latest_version=latest_version.version_no if latest_version else 0,
    )


@router.get("/{resume_id}/versions", response_model=ResumeVersionsResponse)
def list_resume_versions(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if settings.auth_enabled and current_user and resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this resume")

    versions = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_no.asc())
        .all()
    )

    return ResumeVersionsResponse(
        resume_id=resume.id,
        versions=[ResumeVersionItem(id=v.id, version_no=v.version_no, created_at=v.created_at) for v in versions],
    )


@router.post("/cleanup-expired", response_model=CleanupResponse)
def cleanup_expired(db: Session = Depends(get_db)):
    deleted_records, deleted_files = cleanup_expired_resumes(db, storage)
    return CleanupResponse(deleted_records=deleted_records, deleted_files=deleted_files)


@router.post("/tailor", response_model=TailorResponse)
def tailor_resume(
    request: TailorRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    resume, source_version, match_data, tailored, _, _ = _create_tailored_version(
        request=request,
        db=db,
        current_user=current_user,
    )

    latest_version_no = (
        db.query(ResumeVersion.version_no)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_no.desc())
        .first()[0]
    )

    return TailorResponse(
        resume_id=resume.id,
        based_on_version=source_version.version_no,
        version_no=latest_version_no,
        keyword_score=match_data["keyword_score"],
        embedding_score=match_data["embedding_score"],
        total_score=match_data["total_score"],
        tailored_resume_text=tailored["tailored_resume_text"],
        cover_letter_text=tailored.get("cover_letter_text"),
        change_summary=tailored["change_summary"],
        apply_ready_package=tailored["apply_ready_package"],
    )


@router.post("/package/tailor")
def tailor_resume_package(
    request: TailorRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    resume, source_version, match_data, tailored, job, _ = _create_tailored_version(
        request=request,
        db=db,
        current_user=current_user,
    )

    version_no = (
        db.query(ResumeVersion.version_no)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_no.desc())
        .first()[0]
    )

    package_filename = f"apply_ready_{resume.id}_v{version_no}.zip"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"tailored_resume_v{version_no}.txt", tailored["tailored_resume_text"])
        zf.writestr("match_scores.json", json.dumps({
            "keyword_score": match_data["keyword_score"],
            "embedding_score": match_data["embedding_score"],
            "total_score": match_data["total_score"],
            "missing_keywords": match_data.get("missing_keywords", []),
            "matched_keywords": match_data.get("matched_keywords", []),
        }, indent=2))
        zf.writestr("job_context.json", json.dumps({
            "title": job.title,
            "company": job.company,
            "source": job.source,
        }, indent=2))
        if tailored.get("cover_letter_text"):
            zf.writestr("cover_letter.txt", tailored["cover_letter_text"])

    buffer.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="{package_filename}"'}
    return StreamingResponse(buffer, media_type="application/zip", headers=headers)

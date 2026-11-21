"""
Job Automation Tool - FastAPI Main Application
"""
import logging
import re
import threading
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pythonjsonlogger import jsonlogger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, TimeoutError as SQLTimeoutError
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse, Response

from app.api import applications
from app.api import auth
from app.api import background_jobs
from app.api import digest
from app.api import jobs
from app.api import public_api
from app.api import resumes
from app.database import engine
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.utils.config import settings

logger = logging.getLogger("clearhire")
HTTP_REQUESTS = Counter(
    "clearhire_http_requests_total",
    "HTTP requests served by ClearHire",
    ("method", "route", "status_code"),
)
HTTP_REQUEST_DURATION = Histogram(
    "clearhire_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ("method", "route"),
)


def configure_logging() -> None:
    logger.setLevel(logging.INFO if settings.environment != "test" else logging.WARNING)
    handler = logging.StreamHandler()
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(method)s "
            "%(path)s %(status_code)s %(request_id)s %(duration_ms)s %(error_type)s"
        )
    )
    logger.addHandler(handler)
    logger.propagate = False


configure_logging()

tags_metadata = [
    {
        "name": "health",
        "description": "Health check endpoints",
    },
    {
        "name": "auth",
        "description": "Authentication endpoints",
    },
    {
        "name": "jobs",
        "description": "Job listing endpoints",
    },
    {
        "name": "applications",
        "description": "Application tracking endpoints",
    },
    {
        "name": "resumes",
        "description": "Resume management endpoints",
    },
    {
        "name": "scheduler",
        "description": "Automation scheduler endpoints",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("[startup] Starting Job Automation Tool...")
    start_scheduler()
    yield
    # Shutdown logic
    stop_scheduler()
    logger.info("[shutdown] Shutting down gracefully...")


# Initialize FastAPI app
app = FastAPI(
    title="Job Automation Tool API",
    description="API for automating job applications targeting Indian companies",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# CORS configuration
configured_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]
for dev_origin in ("http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"):
    if dev_origin not in configured_origins:
        configured_origins.append(dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    supplied_id = request.headers.get("x-request-id", "")
    request_id = supplied_id if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied_id) else str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.started_at = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - request.state.started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-MS"] = str(elapsed_ms)
    route = getattr(request.scope.get("route"), "path", "unmatched")
    HTTP_REQUESTS.labels(request.method, route, str(response.status_code)).inc()
    HTTP_REQUEST_DURATION.labels(request.method, route).observe(elapsed_ms / 1000)
    logger.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "request_id": request_id,
            "duration_ms": elapsed_ms,
        },
    )
    return response


@app.exception_handler(SQLTimeoutError)
async def sql_timeout_exception_handler(request: Request, exc: SQLTimeoutError):
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id", "") or str(uuid.uuid4())
    logger.error(
        "database_timeout_error",
        extra={"request_id": request_id, "error_type": type(exc).__name__, "detail": str(exc)},
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database connection or query timed out. Please retry shortly.",
            "error": "database_timeout",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(TimeoutError)
async def timeout_exception_handler(request: Request, exc: TimeoutError):
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id", "") or str(uuid.uuid4())
    logger.error(
        "request_timeout_error",
        extra={"request_id": request_id, "error_type": type(exc).__name__, "detail": str(exc)},
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Operation timed out. Please retry shortly.",
            "error": "operation_timeout",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id", "") or str(uuid.uuid4())
    logger.error(
        "database_error",
        extra={"request_id": request_id, "error_type": type(exc).__name__, "detail": str(exc)},
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database service is temporarily unavailable. Please retry shortly.",
            "error": "database_unavailable",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id", "") or str(uuid.uuid4())
    logger.error(
        "unhandled_server_exception",
        extra={"request_id": request_id, "error_type": type(exc).__name__, "detail": str(exc)},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please contact support or try again later.",
            "error": "internal_server_error",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


@app.get("/health", tags=["health"])
async def health_check(request: Request):
    """Health check endpoint for monitoring."""
    request_id = getattr(request.state, "request_id", None)
    return {
        "status": "healthy",
        "service": "job-automation-tool",
        "version": app.version,
        "environment": settings.environment,
        "request_id": request_id,
    }


@app.get("/ready", tags=["health"])
async def readiness_check(request: Request):
    """Readiness check for deployment orchestration."""
    request_id = getattr(request.state, "request_id", None)
    db_available = await run_in_threadpool(is_database_available)
    checks = {
        "database": "ok" if db_available else "unavailable",
        "storage": "ok" if settings.storage_provider else "missing",
        "config": "ok",
    }
    status = "ready" if all(check == "ok" for check in checks.values()) else "degraded"
    status_code = 200 if status == "ready" else 503
    return JSONResponse(
        content={
            "status": status,
            "checks": checks,
            "service": "job-automation-tool",
            "request_id": request_id,
        },
        status_code=status_code,
    )


_readiness_cache_lock = threading.Lock()
_readiness_cache_time = 0.0
_readiness_cache_result = False
_READINESS_CACHE_TTL = 5.0  # seconds


def is_database_available() -> bool:
    global _readiness_cache_time, _readiness_cache_result
    now = time.time()
    if now - _readiness_cache_time < _READINESS_CACHE_TTL:
        return _readiness_cache_result

    with _readiness_cache_lock:
        if now - _readiness_cache_time < _READINESS_CACHE_TTL:
            return _readiness_cache_result

        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            _readiness_cache_result = True
        except Exception as exc:
            logger.warning(
                "readiness_database_check_failed",
                extra={"error_type": type(exc).__name__},
            )
            _readiness_cache_result = False
        _readiness_cache_time = time.time()
        return _readiness_cache_result


@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics; values are process-local and should be scraped per pod."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(public_api.router, prefix="/api/public", tags=["public"])
app.include_router(background_jobs.router, prefix="/api/jobs", tags=["jobs-background"])
app.include_router(background_jobs.router, prefix="/api/background-jobs", tags=["background-jobs"])
app.include_router(digest.router, prefix="/api/digest", tags=["digest"])
app.include_router(digest.analytics_router, prefix="/api/analytics", tags=["analytics"])


@app.get("/", tags=["health"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Job Automation Tool API",
        "docs": "/docs",
        "graphql": "/graphql",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

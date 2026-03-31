"""
Job Automation Tool - FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.api import applications
from app.api import auth
from app.api import jobs
from app.api import resumes
from app.services.scheduler_service import start_scheduler, stop_scheduler

# Will be filled in with actual routers
# from app.api import jobs, applications, resumes, auth

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
    print("🚀 Starting Job Automation Tool...")
    start_scheduler()
    yield
    # Shutdown logic
    stop_scheduler()
    print("✓ Shutting down gracefully...")

# Initialize FastAPI app
app = FastAPI(
    title="Job Automation Tool API",
    description="API for automating job applications targeting Indian companies",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "service": "job-automation-tool",
        "version": app.version
    }

# Include routers (uncomment when implemented)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
# app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
# app.include_router(scheduler.router, prefix="/api/scheduler", tags=["scheduler"])

@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Job Automation Tool API",
        "docs": "/docs",
        "graphql": "/graphql"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

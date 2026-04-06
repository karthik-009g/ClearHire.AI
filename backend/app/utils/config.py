"""
Configuration management using Pydantic Settings
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://job_user:job_password_secure@localhost:5432/job_automation"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # API Keys
    claude_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    llm_provider: str = "groq"
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    auth_enabled: bool = True
    
    # Environment
    debug: bool = True
    environment: str = "development"

    # Resume storage and parsing
    storage_root: str = "storage/resumes"
    max_upload_mb: int = 10
    resume_retention_days: int = 15
    allowed_upload_extensions: tuple[str, ...] = (".pdf", ".docx")
    allowed_upload_mime_types: tuple[str, ...] = (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    )
    spacy_model: str = "en_core_web_sm"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # RAG and reconciliation
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.35
    rag_abstain_threshold: float = 0.55
    rag_reconcile_min_overlap: float = 0.5
    rag_enable_pgvector: bool = True
    rag_request_timeout_seconds: int = 20

    # Evaluation defaults
    evaluation_enabled: bool = True
    evaluation_default_k: int = 5
    evaluation_latency_target_ms_p95: int = 2500
    
    # Job Portal Credentials
    naukri_email: Optional[str] = None
    naukri_password: Optional[str] = None
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None
    
    # Scraping
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    scrape_max_jobs_per_source: int = 25
    default_schedule_timezone: str = "Asia/Kolkata"

    # Email delivery
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_sender_email: Optional[str] = None
    smtp_use_tls: bool = True
    
    # Rate limiting
    rate_limit_jobs_per_minute: int = 60
    rate_limit_applications_per_hour: int = 100
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        case_sensitive=False,
    )

# Create settings instance
settings = Settings()

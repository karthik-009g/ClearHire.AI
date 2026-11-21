"""
Configuration management using Pydantic Settings
"""
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # Azure OpenAI / Azure AI optional settings (kept empty by default)
    azure_api_base: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_deployment: Optional[str] = None

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    auth_enabled: bool = True
    auth_auto_provision_users: bool = False

    # Environment
    debug: bool = True
    environment: str = "development"
    cors_allowed_origins: str = "http://localhost:3000,http://localhost"

    # Resume storage and parsing
    storage_root: str = "storage/resumes"
    storage_provider: str = "local"
    storage_bucket: Optional[str] = None
    storage_region: Optional[str] = None
    storage_endpoint_url: Optional[str] = None
    storage_access_key: Optional[str] = None
    storage_secret_key: Optional[str] = None
    storage_use_ssl: bool = True
    storage_force_path_style: bool = True
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
    embedding_load_local_model: bool = False
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
    scrape_max_jobs_per_source: int = 50
    scrape_max_pages_per_source: int = 5
    default_scrape_posted_within_hours: int = 48
    default_schedule_timezone: str = "Asia/Kolkata"

    # Email delivery
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_sender_email: Optional[str] = None
    smtp_use_tls: bool = True
    automation_email_enabled: bool = False

    # Multi-channel notification delivery (Telegram, WhatsApp)
    telegram_bot_token: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None

    # Workflow automation
    n8n_enabled: bool = False
    n8n_webhook_url: Optional[str] = None

    # Rate limiting
    rate_limit_jobs_per_minute: int = 60
    rate_limit_applications_per_hour: int = 100

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_production_requirements(self):
        environment = (self.environment or "").lower()
        if environment != "production":
            return self

        missing = []
        if not self.secret_key or len(self.secret_key) < 32 or self.secret_key in {
            "your-secret-key-change-in-production",
            "change-me-in-production",
        } or "replace-with" in self.secret_key.lower():
            missing.append("SECRET_KEY")
        try:
            database_url = urlsplit(self.database_url or "")
            database_password = (database_url.password or "").lower()
            database_username = (database_url.username or "").lower()
        except ValueError:
            database_password = ""
            database_username = ""
        if not self.database_url or database_password in {
            "",
            "job_password_secure",
            "postgres",
            "password",
            "change-me",
            "changeme",
        } or "replace-with" in database_password or database_username in {"", "user", "username"}:
            missing.append("DATABASE_URL")
        if self.debug:
            missing.append("DEBUG=false")
        if not self.auth_enabled:
            missing.append("AUTH_ENABLED=true")
        origins = [origin.strip().lower() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
        if not origins or any(
            not origin.startswith("https://")
            or origin == "*"
            or "localhost" in origin
            or "127.0.0.1" in origin
            for origin in origins
        ):
            missing.append("CORS_ALLOWED_ORIGINS")
        if self.storage_provider == "s3" and not self.storage_bucket:
            missing.append("STORAGE_BUCKET")
        if self.n8n_enabled and not self.n8n_webhook_url:
            missing.append("N8N_WEBHOOK_URL")

        if missing:
            raise ValueError(f"Missing required production config: {', '.join(missing)}")
        return self


# Create settings instance
settings = Settings()

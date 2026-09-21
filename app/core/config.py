"""Global configuration and locked Vertex AI Agent Engine model definitions."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings enforcing SDD v1.3 guardrails and model tiers."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "hr-agentic-solution"
    GOOGLE_CLOUD_PROJECT: str = "hr-agentic-prod"
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    GOOGLE_CLOUD_FAILOVER_LOCATION: str = "us-east1"

    # Latest Gemini 3.6 / 3.8 Models on Vertex AI Agent Engine
    GEMINI_FLASH_MODEL: str = "gemini-3.6-flash"
    GEMINI_PRO_MODEL: str = "gemini-3.6-pro"

    # Maria Santos (DPO) Safeguard: Vertex AI Zero Data Retention (ZDR)
    VERTEX_AI_ZERO_DATA_RETENTION: bool = True

    # Alex Rivera (IT Director) Safeguard: PostgreSQL 16 Parity & Token-Bucket Rate Limits
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hr_agentic"
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 60  # Unified <= 60s Contractual & Technical Sync SLA

    WORKWEEK_RPS_LIMIT: int = 50
    WORKWEEK_BURST_CAPACITY: int = 100
    SERVICEIMMEDIATELY_RPS_LIMIT: int = 25
    SERVICEIMMEDIATELY_BURST_CAPACITY: int = 50
    CLOUD_TASKS_RETRY_QUEUE: str = "ww-it-mutation-retry-queue"


settings = Settings()

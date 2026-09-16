"""
core/config.py

Centralised configuration powered by pydantic-settings.

How it works
────────────
1. pydantic-settings reads every field from the environment (or .env file).
2. Type coercion and validation happen automatically at startup.
3. The singleton `settings` object is imported everywhere that needs config.
4. Nothing else in the codebase reads `os.environ` directly — ever.

Environment precedence (highest → lowest):
  real env vars  >  .env file  >  field defaults
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.constants import Environment


class Settings(BaseSettings):
    """
    Master settings class.

    All fields map 1-to-1 to environment variables (case-insensitive).
    Validation errors here abort startup — a deliberate fail-fast strategy
    so misconfigured deployments are caught immediately.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # silently discard unknown env vars
    )

    # ─────────────────────────────────────────────
    # Application identity
    # ─────────────────────────────────────────────
    app_name: str = Field(default="Mnemosyne")
    app_version: str = Field(default="0.1.0")
    app_description: str = Field(default="AI-powered knowledge management backend")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    # ─────────────────────────────────────────────
    # Server
    # ─────────────────────────────────────────────
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1)

    # ─────────────────────────────────────────────
    # Security
    # ─────────────────────────────────────────────
    secret_key: str = Field(default="CHANGE_ME_IN_PRODUCTION")
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:5173,chrome-extension://hhknhgcjdoefdpemmknckbbafoneaalp")
    allowed_hosts: str = Field(default="*")

    # ─────────────────────────────────────────────
    # Database (PostgreSQL)
    # ─────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/mnemosyne"
    )
    database_pool_size: int = Field(default=10, ge=1)
    database_max_overflow: int = Field(default=20, ge=0)

    # ─────────────────────────────────────────────
    # Redis
    # ─────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ─────────────────────────────────────────────
    # Vector Database (Qdrant)
    # ─────────────────────────────────────────────
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str = Field(default="")

    # ─────────────────────────────────────────────
    # AI Providers
    # ─────────────────────────────────────────────
    groq_api_key: str = Field(default="")
    hf_token: str = Field(default="", validation_alias="hf_token")

    # ─────────────────────────────────────────────
    # Logging
    # ─────────────────────────────────────────────
    log_level: str = Field(default="DEBUG")
    log_format: str = Field(default="text")  # "text" | "json"
    log_file_path: str = Field(default="logs/mnemosyne.log")

    # ─────────────────────────────────────────────
    # Computed properties
    # ─────────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def docs_url(self) -> str | None:
        """Swagger UI is hidden in production."""
        return None if self.is_production else "/docs"

    @property
    def redoc_url(self) -> str | None:
        return None if self.is_production else "/redoc"

    @property
    def openapi_url(self) -> str | None:
        return None if self.is_production else "/openapi.json"

    # ─────────────────────────────────────────────
    # Validators
    # ─────────────────────────────────────────────

    @property
    def allowed_origins_list(self) -> list[str]:
        """Split comma-separated origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Split comma-separated hosts into a list."""
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalise_log_level(cls, v: str) -> str:
        return v.upper()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached singleton Settings instance.

    @lru_cache ensures .env is parsed exactly once per process.
    Call `get_settings.cache_clear()` in tests to reset between cases.
    """
    return Settings()


# Module-level singleton — import this everywhere.
settings: Settings = get_settings()

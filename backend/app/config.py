"""Application settings, loaded from environment / .env (no secrets in code)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-only-insecure-secret-change-me-32chars-minimum"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_env: str = "local"
    app_name: str = "Solidita 4.0"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://solidita_app:solidita_app@localhost:5432/solidita"
    migration_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/solidita"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth / JWT
    jwt_secret_key: str = _DEV_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14

    # CORS (comma-separated string; parsed via cors_origins_list). Kept as a plain
    # string because pydantic-settings JSON-decodes list-typed env values.
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Public base URL (used in report QR verify links)
    public_base_url: str = "http://localhost:8000"

    # Object storage (used from Sprint 3+)
    s3_endpoint_url: str | None = None
    s3_bucket: str = "solidita-assets"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str = "eu-south-1"
    # Local filesystem object-storage dir (dev fallback when S3 is not configured)
    storage_local_dir: str = "storage"

    # Billing (Stripe). Optional — webhook is a no-op until the secret is set.
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def _require_strong_secret_outside_local(self) -> Settings:
        if self.app_env in ("staging", "production"):
            if self.jwt_secret_key == _DEV_SECRET or len(self.jwt_secret_key) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must be a strong (>=32 char) non-default secret "
                    f"when APP_ENV={self.app_env}."
                )
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

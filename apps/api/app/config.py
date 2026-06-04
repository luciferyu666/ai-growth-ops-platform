from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Growth Ops Platform API"
    app_env: str = "development"
    database_url: str = Field(
        default="postgresql+psycopg://growth_ops:growth_ops@db:5432/growth_ops"
    )
    redis_url: str = "redis://redis:6379/0"
    auth_provider: str = "demo-header"
    auth0_domain: str | None = None
    auth0_audience: str | None = None
    auth0_issuer_base_url: str | None = None
    auth0_scope: str = "openid profile email"
    notification_provider: str = "mock"
    notification_retry_base_seconds: int = 60
    notification_retry_max_seconds: int = 3600
    notification_alert_dead_letter_threshold: int = 1
    notification_alert_failed_job_threshold: int = 1
    notification_alert_stalled_minutes: int = 15
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

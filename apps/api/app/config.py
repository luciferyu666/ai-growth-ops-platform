from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Growth Ops Platform API"
    app_env: str = "development"
    database_url: str | None = None
    postgres_url: str | None = None
    postgres_url_non_pooling: str | None = None
    redis_url: str | None = None
    workflow_queue_mode: Literal["redis", "database"] = "redis"
    redis_required: bool = True
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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return value
            return [origin.strip() for origin in text.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def resolve_runtime_urls(self) -> "Settings":
        if not self.database_url:
            self.database_url = self.postgres_url or self.postgres_url_non_pooling

        if self.database_url:
            self.database_url = normalize_postgres_url(self.database_url)
        elif self.app_env == "development":
            self.database_url = (
                "postgresql+psycopg://growth_ops:growth_ops@db:5432/growth_ops"
            )

        if not self.redis_url and self.app_env == "development":
            self.redis_url = "redis://redis:6379/0"

        if self.workflow_queue_mode == "database":
            self.redis_required = False

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def normalize_postgres_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url

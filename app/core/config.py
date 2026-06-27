"""Application settings loaded from environment / `.env`.

Every external integration is optional. The `*_enabled` properties let services
decide at runtime whether to make real API calls or fall back to mock mode, so
the platform boots and works end-to-end with zero secrets.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # ---- App ----
    APP_NAME: str = "Murimi OS"
    ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    DEFAULT_LANGUAGE: str = "en"
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    # ---- Security / JWT ----
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    JWT_ALGORITHM: str = "HS256"
    FERNET_KEY: str = ""

    # ---- Database ----
    # Defaults to SQLite for zero-dependency local dev. Switch to Postgres for
    # production / pgvector RAG: postgresql+asyncpg://user:pass@host:5432/murimi
    DATABASE_URL: str = "sqlite+aiosqlite:///./murimi.db"
    TEST_DATABASE_URL: str = ""
    ENABLE_RLS: bool = False
    DB_ECHO: bool = False

    # ---- Redis / Celery ----
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ---- Rate limiting ----
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120

    # ---- OpenAI ----
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_VISION_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    EMBED_DIM: int = 1536

    # ---- WhatsApp Cloud API ----
    WHATSAPP_VERIFY_TOKEN: str = "murimi-verify-token"
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_API_VERSION: str = "v21.0"

    # ---- Weather ----
    WEATHER_PROVIDER: str = "openweather"
    WEATHER_API_KEY: str = ""

    # ---- AI training data / national AI sharing ----
    # Salt for pseudonymizing farmers in shared datasets (defaults from SECRET_KEY).
    ANON_SALT: str = ""
    NATIONAL_AI_ENDPOINT: str = ""   # blank => feed runs in mock/log mode
    NATIONAL_AI_API_KEY: str = ""

    # ---- Notifications ----
    SMS_PROVIDER: str = ""
    SMS_API_KEY: str = ""
    SMS_SENDER_ID: str = "Murimi"
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USER: str = ""
    EMAIL_SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "no-reply@murimi.os"

    # ------------------------------------------------------------------ #
    # Parsing helpers
    # ------------------------------------------------------------------ #
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()] or ["*"]
        return v

    # ------------------------------------------------------------------ #
    # Derived / capability flags
    # ------------------------------------------------------------------ #
    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def openai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def whatsapp_enabled(self) -> bool:
        return bool(self.WHATSAPP_ACCESS_TOKEN and self.WHATSAPP_PHONE_NUMBER_ID)

    @property
    def weather_enabled(self) -> bool:
        return bool(self.WEATHER_API_KEY)

    @property
    def sms_enabled(self) -> bool:
        return bool(self.SMS_API_KEY)

    @property
    def national_ai_enabled(self) -> bool:
        return bool(self.NATIONAL_AI_ENDPOINT)

    @property
    def email_enabled(self) -> bool:
        return bool(self.EMAIL_SMTP_HOST and self.EMAIL_SMTP_USER)

    @property
    def sync_database_url(self) -> str:
        """Synchronous URL (psycopg/-) — handy for tooling that needs sync drivers."""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def effective_test_database_url(self) -> str:
        if self.TEST_DATABASE_URL:
            return self.TEST_DATABASE_URL
        # Derive a *_test database from the main URL.
        base, _, tail = self.DATABASE_URL.rpartition("/")
        return f"{base}/{tail}_test"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

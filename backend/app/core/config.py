from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


FuelType = Literal["e5", "e10", "diesel"]
FuelTypeWithAll = Literal["e5", "e10", "diesel", "all"]
SortType = Literal["price", "distance"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FuelMind"
    app_version: str = "0.1.0"
    environment: str = "development"

    tankerkoenig_api_key: str | None = Field(default=None, alias="TANKERKOENIG_API_KEY")
    tankerkoenig_base_url: str = Field(
        default="https://creativecommons.tankerkoenig.de/json",
        alias="TANKERKOENIG_BASE_URL",
    )
    tankerkoenig_timeout_seconds: int = Field(default=12, alias="TANKERKOENIG_TIMEOUT_SECONDS")
    tankerkoenig_max_retries: int = Field(default=3, alias="TANKERKOENIG_MAX_RETRIES")
    geocoding_base_url: str = Field(
        default="https://nominatim.openstreetmap.org",
        alias="GEOCODING_BASE_URL",
    )
    geocoding_timeout_seconds: int = Field(default=10, alias="GEOCODING_TIMEOUT_SECONDS")
    geocoding_result_limit: int = Field(default=5, alias="GEOCODING_RESULT_LIMIT")
    geocoding_user_agent: str = Field(default="FuelMind/0.1", alias="GEOCODING_USER_AGENT")
    geocoding_country_codes: str | None = Field(default="de", alias="GEOCODING_COUNTRY_CODES")

    postgres_db: str = Field(default="fuelmind", alias="POSTGRES_DB")
    postgres_user: str = Field(default="fuelmind", alias="POSTGRES_USER")
    postgres_password: str = Field(default="fuelmind_password", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")

    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_port: int = Field(default=3000, alias="FRONTEND_PORT")
    frontend_api_base_url: str = Field(default="http://localhost:8000/api", alias="FRONTEND_API_BASE_URL")

    allow_public_api: bool = Field(default=False, alias="ALLOW_PUBLIC_API")
    enable_scheduler: bool = Field(default=True, alias="ENABLE_SCHEDULER")
    app_internal_token: str | None = Field(default=None, alias="APP_INTERNAL_TOKEN")

    default_lat: float | None = Field(default=None, alias="DEFAULT_LAT")
    default_lng: float | None = Field(default=None, alias="DEFAULT_LNG")
    default_radius_km: float = Field(default=10.0, alias="DEFAULT_RADIUS_KM")
    default_fuel_type: FuelType = Field(default="e10", alias="DEFAULT_FUEL_TYPE")

    cache_ttl_nearby_seconds: int = Field(default=60, alias="CACHE_TTL_NEARBY_SECONDS")
    cache_ttl_detail_seconds: int = Field(default=300, alias="CACHE_TTL_DETAIL_SECONDS")
    cache_ttl_prices_seconds: int = Field(default=60, alias="CACHE_TTL_PRICES_SECONDS")

    notification_mode: str = Field(default="none", alias="NOTIFICATION_MODE")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int | None = Field(default=None, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    ntfy_topic: str | None = Field(default=None, alias="NTFY_TOPIC")
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")

    cors_allow_origins_env: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ALLOW_ORIGINS",
    )
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    @field_validator(
        "tankerkoenig_api_key",
        "smtp_host",
        "smtp_port",
        "smtp_user",
        "smtp_password",
        "ntfy_topic",
        "telegram_bot_token",
        "telegram_chat_id",
        "app_internal_token",
        "database_url",
        "redis_url",
        "default_lat",
        "default_lng",
        "geocoding_country_codes",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value):
        if value == "":
            return None
        return value

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def resolved_redis_url(self) -> str:
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def external_api_configured(self) -> bool:
        return bool(self.tankerkoenig_api_key)

    @property
    def cors_allow_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_allow_origins_env.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

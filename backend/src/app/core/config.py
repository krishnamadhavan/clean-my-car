"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Clean My Car API"
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = "/api/v1"

    # Database — prefer DATABASE_URL; compose sets individual parts as fallback
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_user: str = Field(default="cleanmycar", alias="POSTGRES_USER")
    postgres_password: str = Field(default="cleanmycar", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="cleanmycar", alias="POSTGRES_DB")
    postgres_host: str = Field(default="db", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    # Auth / JWT
    jwt_secret_key: str = Field(
        default="change-me-in-production-use-long-random-string",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # OTP
    otp_length: int = Field(default=6, alias="OTP_LENGTH")
    otp_expire_minutes: int = Field(default=5, alias="OTP_EXPIRE_MINUTES")
    otp_max_attempts: int = Field(default=5, alias="OTP_MAX_ATTEMPTS")
    otp_resend_cooldown_seconds: int = Field(default=60, alias="OTP_RESEND_COOLDOWN_SECONDS")
    otp_max_requests_per_hour: int = Field(default=5, alias="OTP_MAX_REQUESTS_PER_HOUR")
    # Dev-only: include OTP in API response (never enable in production)
    otp_return_in_response: bool = Field(default=False, alias="OTP_RETURN_IN_RESPONSE")

    # After DELETE /me, same phone cannot complete OTP verify until this many days pass.
    # Set to 0 to allow immediate re-registration. Fractional days allowed (e.g. 0.5).
    account_deletion_cooloff_days: float = Field(
        default=1.0,
        ge=0,
        alias="ACCOUNT_DELETION_COOLOFF_DAYS",
    )

    # Ops Module 1 — optional bootstrap operator (created on API startup if email missing)
    ops_bootstrap_email: str | None = Field(default=None, alias="OPS_BOOTSTRAP_EMAIL")
    ops_bootstrap_password: str | None = Field(default=None, alias="OPS_BOOTSTRAP_PASSWORD")
    ops_bootstrap_name: str | None = Field(default=None, alias="OPS_BOOTSTRAP_NAME")

    # Browser origins allowed to call the API (ops-ui, etc.). Comma-separated.
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        if self.database_url:
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url

        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

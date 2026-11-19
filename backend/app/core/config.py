import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "SafeHer"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = Field(
        default="insecure-dev-secret-key-change-in-production-min-32-chars-long",
        min_length=32,
    )
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://safeher_user:safeher_password@localhost:5432/safeher_db"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Tokens
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Providers
    SMS_PROVIDER: str = "mock"
    PUSH_PROVIDER: str = "mock"
    EMAIL_PROVIDER: str = "mock"
    MAPS_PROVIDER: str = "mock"
    PAYMENTS_PROVIDER: str = "mock"
    LLM_PROVIDER: str = "mock"

    # SMS & DLT Credentials (India)
    SMS_DLT_SENDER_ID: str = "SAFEHR"
    FAST2SMS_API_KEY: str | None = None
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_FROM_PHONE: str | None = None

    # SMTP Email
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "emergency@safeher.internal"

    # Web Push (VAPID)
    VAPID_PUBLIC_KEY: str | None = None
    VAPID_PRIVATE_KEY: str | None = None

    # Webhook Security
    WEBHOOK_SECRET: str = "default-insecure-webhook-secret-change-in-prod"

    # Emergency Primary Contact
    EMERGENCY_NUMBER_PRIMARY: str = "112"


settings = Settings()

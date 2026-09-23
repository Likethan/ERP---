
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # General Project Info
    PROJECT_NAME: str = "CampusOS API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # CORS Settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database Settings
    DATABASE_URL: str = (
        "postgresql+asyncpg://campusos_user:campusos_password@localhost:5432/campusos_db"
    )

    # Security Settings
    SECRET_KEY: str = "campusos_insecure_development_secret_key_minimum_32_chars_long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage Settings
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: str = "campusos_admin"
    STORAGE_SECRET_KEY: str = "campusos_minio_secret"
    STORAGE_BUCKET_NAME: str = "campusos-documents"
    STORAGE_USE_SSL: bool = False


settings = Settings()

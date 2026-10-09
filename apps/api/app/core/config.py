
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
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # CORS Settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database Settings & Connection Pooling
    DATABASE_URL: str = (
        "postgresql+asyncpg://campusos_user:campusos_password@localhost:5432/campusos_db"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Security Settings
    SECRET_KEY: str = "campusos_insecure_development_secret_key_minimum_32_chars_long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_ENABLED: bool = False
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str | None = None
    DOCS_ENABLED: bool | None = None

    # Request Size Limits (Bytes)
    MAX_JSON_BODY_BYTES: int = 2 * 1024 * 1024  # 2 MB
    MAX_MULTIPART_BYTES: int = 25 * 1024 * 1024  # 25 MB

    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 120
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10
    RATE_LIMIT_BURST_MAX: int = 30

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage Settings
    STORAGE_PROVIDER: str = "minio"
    STORAGE_REGION: str = "us-east-1"
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: str = "campusos_admin"
    STORAGE_SECRET_KEY: str = "campusos_minio_secret"
    STORAGE_BUCKET_NAME: str = "campusos-documents"
    STORAGE_USE_SSL: bool = False

    # AI & Intelligence Settings
    AI_PROVIDER: str = "mock"
    AI_MODEL: str = "campusos-institutional-v1"
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_TOKENS: int = 2048
    AI_RATE_LIMIT_PER_MINUTE_USER: int = 60
    AI_RATE_LIMIT_PER_MINUTE_TENANT: int = 500
    AI_MAX_QUERY_LENGTH: int = 2000
    AI_MAX_TOOL_RESULTS: int = 50

    @property
    def is_docs_enabled(self) -> bool:
        if self.DOCS_ENABLED is not None:
            return self.DOCS_ENABLED
        return self.ENVIRONMENT.lower() != "production"

    def validate_production_configuration(self) -> None:
        """Validate critical security configurations for production environments."""
        if self.ENVIRONMENT.lower() == "production":
            insecure_keys = {
                "campusos_insecure_development_secret_key_minimum_32_chars_long",
                "change-me",
                "secret",
                "secret_key",
                "supersecret",
            }
            if self.SECRET_KEY in insecure_keys or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "Production startup rejected: SECRET_KEY must be a secure secret of at least 32 characters."
                )
            if self.DEBUG:
                raise ValueError("Production startup rejected: DEBUG cannot be enabled in production.")
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "Production startup rejected: Wildcard '*' CORS origin is not permitted in production."
                )


settings = Settings()


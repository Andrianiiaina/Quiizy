from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://lms:lms_dev_password@postgres:5432/lms"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    DEBUG: bool = False

    # CORS — séparé par virgule dans l'env, ex. : "http://localhost,http://localhost:80"
    CORS_ORIGINS: list[str] = ["http://localhost", "http://localhost:80"]

    # File storage
    MAX_UPLOAD_SIZE_MB: int = 50
    STORAGE_BACKEND: str = "LOCAL"
    STORAGE_LOCAL_PATH: str = "/app/storage"


settings = Settings()

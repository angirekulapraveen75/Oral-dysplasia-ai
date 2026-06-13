import os
from pydantic_settings import BaseSettings

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    """Application-wide configuration loaded from environment or defaults."""

    PROJECT_NAME: str = "OralDysplasia AI"
    API_V1_PREFIX: str = "/api/v1"

    # JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "oral-dysplasia-dev-secret-key-change-in-production-2026",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AES-256 Fernet key for encrypting patient PII at rest.
    # Generate a real one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    PATIENT_ENCRYPTION_KEY: str = os.getenv(
        "PATIENT_ENCRYPTION_KEY",
        "dGhpcy1pcy1hLTMyLWJ5dGUtZGV2LWtleS0xMjM0NQ==",
    )

    # Database — default is XAMPP MySQL, falls back to SQLite if offline
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+aiomysql://root:@127.0.0.1:3306/oraldysplasia",
    )

    # Where uploaded slide files are stored locally
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(_backend_dir, "uploads"))

    class Config:
        case_sensitive = True


settings = Settings()

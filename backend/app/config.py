"""Application configuration loaded from environment variables."""

import warnings

from pydantic_settings import BaseSettings

_DEFAULT_JWT_SECRET = "CHANGE-ME-in-production"


class Settings(BaseSettings):
    app_name: str = "Steps Challenge"
    debug: bool = False

    # Database
    database_url: str = "postgresql://localhost:5432/steps_challenge"

    # JWT auth
    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # CORS — comma-separated origins (e.g. "https://app.example.com,http://localhost:5173")
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Miles club thresholds (average steps per day)
    miles_club_high: int = 10_000
    miles_club_mid: int = 5_000

    # Steps-to-miles conversion (average stride)
    steps_per_mile: int = 2_000

    # Profile photo uploads
    upload_dir: str = "uploads"
    max_photo_size: int = 5 * 1024 * 1024  # 5 MB
    allowed_photo_types: str = "image/jpeg,image/png,image/webp,image/gif"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

if settings.jwt_secret == _DEFAULT_JWT_SECRET:
    warnings.warn(
        "JWT_SECRET is using the insecure default value. "
        "Set the JWT_SECRET environment variable to a strong random string (32+ chars).",
        stacklevel=1,
    )

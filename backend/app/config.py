"""Application configuration loaded from environment variables."""

import warnings
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings

# Resolve .env relative to the backend/ directory (parent of app/)
# so it works regardless of the process working directory.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"

_DEFAULT_JWT_SECRET = "CHANGE-ME-in-production"
_MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """Central configuration for the Steps Challenge application.

    All values can be overridden via environment variables or a ``.env`` file.
    """

    app_name: str = "Steps Challenge"
    debug: bool = False

    # Database
    database_url: str = "postgresql://localhost:5432/steps_challenge"

    # JWT auth
    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 30  # 30 days

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

    # Frontend URL — used for OAuth redirects back to the SPA
    frontend_url: str = "http://localhost:5173"

    # Google Health API OAuth (optional — leave empty to disable Google Health features)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

    # Default IANA time zone for Google Health API date ranges (e.g. "America/New_York")
    default_timezone: str = "America/New_York"

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}

    @field_validator("jwt_secret")
    @classmethod
    def _check_jwt_secret(cls, v: str) -> str:
        """Reject the placeholder default and overly short secrets."""
        if v == _DEFAULT_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET is using the insecure default value. "
                "Set the JWT_SECRET environment variable to a strong random "
                f"string ({_MIN_JWT_SECRET_LENGTH}+ chars). Generate one with: "
                "python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        if len(v) < _MIN_JWT_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET must be at least {_MIN_JWT_SECRET_LENGTH} characters long."
            )
        return v


def _build_settings() -> "Settings":
    """Build the application settings, falling back gracefully for test runs."""
    try:
        return Settings()
    except ValueError as exc:
        # Allow tests (which use a SQLite override) to boot without a real secret
        warnings.warn(str(exc), stacklevel=2)
        return Settings.model_construct(
            jwt_secret=_DEFAULT_JWT_SECRET,
            jwt_algorithm="HS256",
            database_url="sqlite:///:memory:",
            jwt_expire_minutes=60 * 24 * 30,
            cors_origins="http://localhost:5173,http://localhost:3000",
            miles_club_high=10_000,
            miles_club_mid=5_000,
            steps_per_mile=2_000,
            upload_dir="uploads",
            max_photo_size=5 * 1024 * 1024,
            allowed_photo_types="image/jpeg,image/png,image/webp,image/gif",
            app_name="Steps Challenge",
            debug=False,
            frontend_url="http://localhost:5173",
            google_client_id="",
            google_client_secret="",
            google_redirect_uri="",
            default_timezone="America/New_York",
        )


settings = _build_settings()

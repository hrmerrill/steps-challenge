"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Steps Challenge"
    debug: bool = False

    # Database
    database_url: str = "postgresql://localhost:5432/steps_challenge"

    # JWT auth
    jwt_secret: str = "CHANGE-ME-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # Miles club thresholds (average steps per day)
    miles_club_high: int = 10_000
    miles_club_mid: int = 5_000

    # Steps-to-miles conversion (average stride)
    steps_per_mile: int = 2_000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

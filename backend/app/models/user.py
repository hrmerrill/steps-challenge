"""User model — accounts, auth credentials, and fitness provider tokens."""

import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.steps import StepSource


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Profile photo (relative URL path, e.g. "/uploads/profile_photos/abc.jpg")
    profile_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Which step source to use for leaderboard/stats (avoids double-counting)
    preferred_step_source: Mapped[StepSource] = mapped_column(
        Enum(StepSource), default=StepSource.MANUAL, server_default="manual",
    )

    # Fitness provider OAuth tokens (null = not connected)
    garmin_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    strava_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_health_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Google Health API OAuth refresh token (stored separately for token refresh flow)
    google_health_refresh_token: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    daily_steps: Mapped[list["DailySteps"]] = relationship(back_populates="user")  # noqa: F821
    participations: Mapped[list["ChallengeParticipant"]] = relationship(  # noqa: F821
        back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"

"""User model — accounts, auth credentials, and fitness provider tokens."""

import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Fitness provider OAuth tokens (null = not connected)
    garmin_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    strava_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fitbit_token: Mapped[str | None] = mapped_column(String(500), nullable=True)

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

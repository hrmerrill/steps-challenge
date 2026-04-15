"""Challenge and ChallengeParticipant models."""

import datetime
import enum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MilesClubTier(str, enum.Enum):
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    NONE = "none"


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(5000), nullable=True, default=None)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    participants: Mapped[list["ChallengeParticipant"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Challenge id={self.id} name={self.name!r}>"


class ChallengeParticipant(Base):
    __tablename__ = "challenge_participants"
    __table_args__ = (
        UniqueConstraint("challenge_id", "user_id", name="uq_challenge_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    miles_club_tier: Mapped[MilesClubTier] = mapped_column(
        Enum(MilesClubTier), default=MilesClubTier.NONE
    )

    challenge: Mapped["Challenge"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="participations")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<ChallengeParticipant challenge={self.challenge_id} "
            f"user={self.user_id} tier={self.miles_club_tier}>"
        )

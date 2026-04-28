"""DailySteps model — one row per user per day."""

import datetime
import enum

from sqlalchemy import Date, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StepSource(str, enum.Enum):
    MANUAL = "manual"
    GARMIN = "garmin"
    STRAVA = "strava"
    GOOGLE_HEALTH = "google_health"


class DailySteps(Base):
    __tablename__ = "daily_steps"
    __table_args__ = (
        UniqueConstraint("user_id", "date", "source", name="uq_user_date_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    step_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[StepSource] = mapped_column(
        Enum(StepSource, values_callable=lambda e: [x.value for x in e]),
        default=StepSource.MANUAL,
    )

    user: Mapped["User"] = relationship(back_populates="daily_steps")  # noqa: F821

    def __repr__(self) -> str:
        return f"<DailySteps user_id={self.user_id} date={self.date} steps={self.step_count}>"

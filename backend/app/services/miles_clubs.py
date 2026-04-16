"""Miles club tier calculation service."""

import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.challenge import MilesClubTier
from app.models.steps import DailySteps


def calculate_tier(average_daily_steps: float) -> MilesClubTier:
    """Determine miles club tier from average daily steps in previous month."""
    if average_daily_steps >= settings.miles_club_high:
        return MilesClubTier.HIGH
    if average_daily_steps >= settings.miles_club_mid:
        return MilesClubTier.MID
    return MilesClubTier.LOW


def tier_label(tier: MilesClubTier) -> str:
    """Return display label for a miles club tier."""
    return {
        MilesClubTier.HIGH: ">10k steps/day",
        MilesClubTier.MID: "5k\u201310k steps/day",
        MilesClubTier.LOW: "0\u20135k steps/day",
        MilesClubTier.NONE: "",
    }[tier]


def get_prior_month_range(
    reference_date: datetime.date | None = None,
) -> tuple[datetime.date, datetime.date]:
    """Return (start, end) of the calendar month before *reference_date*."""
    if reference_date is None:
        reference_date = datetime.date.today()
    first_of_current = reference_date.replace(day=1)
    prior_month_end = first_of_current - datetime.timedelta(days=1)
    prior_month_start = prior_month_end.replace(day=1)
    return prior_month_start, prior_month_end


def _avg_daily_from_range(
    user_id: int,
    db: Session,
    start: datetime.date,
    end: datetime.date,
) -> float:
    """Average daily steps for a user in [start, end] (divides by calendar days)."""
    days = (end - start).days + 1
    total: int = (
        db.query(func.coalesce(func.sum(DailySteps.step_count), 0))
        .filter(
            DailySteps.user_id == user_id,
            DailySteps.date >= start,
            DailySteps.date <= end,
        )
        .scalar()
    )
    return total / days if days > 0 else 0


def get_user_tier(
    user_id: int,
    db: Session,
    reference_date: datetime.date | None = None,
) -> tuple[MilesClubTier, float]:
    """Return (tier, avg_daily) for *user_id* based on the prior calendar month."""
    start, end = get_prior_month_range(reference_date)
    avg = _avg_daily_from_range(user_id, db, start, end)
    return calculate_tier(avg), round(avg, 1)


def get_bulk_user_tiers(
    user_ids: list[int],
    db: Session,
    reference_date: datetime.date | None = None,
) -> dict[int, MilesClubTier]:
    """Return {user_id: tier} for many users based on the prior calendar month."""
    if not user_ids:
        return {}
    start, end = get_prior_month_range(reference_date)
    days = (end - start).days + 1

    rows = (
        db.query(
            DailySteps.user_id,
            func.coalesce(func.sum(DailySteps.step_count), 0).label("total"),
        )
        .filter(
            DailySteps.user_id.in_(user_ids),
            DailySteps.date >= start,
            DailySteps.date <= end,
        )
        .group_by(DailySteps.user_id)
        .all()
    )
    totals = {row[0]: row[1] for row in rows}

    return {
        uid: calculate_tier(totals.get(uid, 0) / days if days > 0 else 0)
        for uid in user_ids
    }

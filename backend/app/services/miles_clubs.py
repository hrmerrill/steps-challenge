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


def _current_month_range(
    reference_date: datetime.date | None = None,
) -> tuple[datetime.date, datetime.date]:
    """Return (start, end) of the calendar month containing *reference_date*."""
    if reference_date is None:
        reference_date = datetime.date.today()
    start = reference_date.replace(day=1)
    # Last day of the month: go to next month's first day, subtract 1
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1) - datetime.timedelta(days=1)
    else:
        end = start.replace(month=start.month + 1, day=1) - datetime.timedelta(days=1)
    return start, end


def _has_steps_in_range(user_id: int, db: Session, start: datetime.date, end: datetime.date) -> bool:
    """Return True if the user has any step records in [start, end]."""
    return (
        db.query(DailySteps.id)
        .filter(
            DailySteps.user_id == user_id,
            DailySteps.date >= start,
            DailySteps.date <= end,
        )
        .first()
    ) is not None


def get_user_tier(
    user_id: int,
    db: Session,
    reference_date: datetime.date | None = None,
) -> tuple[MilesClubTier, float]:
    """Return (tier, avg_daily) for *user_id*.

    Uses the prior calendar month's average daily steps.  If the user has
    no data in the prior month, falls back to the current month.
    """
    prior_start, prior_end = get_prior_month_range(reference_date)
    if _has_steps_in_range(user_id, db, prior_start, prior_end):
        avg = _avg_daily_from_range(user_id, db, prior_start, prior_end)
    else:
        cur_start, cur_end = _current_month_range(reference_date)
        avg = _avg_daily_from_range(user_id, db, cur_start, cur_end)
    return calculate_tier(avg), round(avg, 1)


def _bulk_steps_in_range(
    user_ids: list[int],
    db: Session,
    start: datetime.date,
    end: datetime.date,
) -> dict[int, int]:
    """Return {user_id: total_steps} for users with data in [start, end]."""
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
    return {row[0]: row[1] for row in rows}


def get_bulk_user_tiers(
    user_ids: list[int],
    db: Session,
    reference_date: datetime.date | None = None,
) -> dict[int, MilesClubTier]:
    """Return {user_id: tier} for many users.

    Uses prior month avg; falls back to current month for users with no
    prior-month data.
    """
    if not user_ids:
        return {}

    prior_start, prior_end = get_prior_month_range(reference_date)
    prior_days = (prior_end - prior_start).days + 1
    prior_totals = _bulk_steps_in_range(user_ids, db, prior_start, prior_end)

    # Users missing from prior_totals need current-month fallback
    missing = [uid for uid in user_ids if uid not in prior_totals]
    cur_totals: dict[int, int] = {}
    cur_days = 0
    if missing:
        cur_start, cur_end = _current_month_range(reference_date)
        cur_days = (cur_end - cur_start).days + 1
        cur_totals = _bulk_steps_in_range(missing, db, cur_start, cur_end)

    result: dict[int, MilesClubTier] = {}
    for uid in user_ids:
        if uid in prior_totals:
            avg = prior_totals[uid] / prior_days if prior_days > 0 else 0
        elif uid in cur_totals:
            avg = cur_totals[uid] / cur_days if cur_days > 0 else 0
        else:
            avg = 0
        result[uid] = calculate_tier(avg)
    return result

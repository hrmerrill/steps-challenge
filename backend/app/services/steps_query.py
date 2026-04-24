"""Deduplicated steps query helper — avoids double-counting when
a user has both manual and synced entries for the same date.

For each (user_id, date), picks the entry whose source matches the
user's preferred_step_source. Falls back to any available source if
the preferred source has no entry for that date.

Works with both PostgreSQL and SQLite (for tests).
"""

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.steps import DailySteps
from app.models.user import User


def _effective_ids_subquery():
    """Build a scalar subquery that returns deduplicated DailySteps IDs.

    For each (user_id, date), selects the single entry to count:
    - Prefers the entry matching the user's preferred_step_source
    - Falls back to any source if preferred has no data for that date
    """
    priority = case(
        (DailySteps.source == User.preferred_step_source, 0),
        else_=1,
    )

    # For each (user_id, date), pick the entry with the best priority
    # (0 = preferred source, 1 = fallback). Among ties, pick the lowest
    # DailySteps.id for determinism.
    best_priority = (
        select(
            DailySteps.user_id.label("user_id"),
            DailySteps.date.label("date"),
            func.min(priority).label("best_prio"),
        )
        .join(User, DailySteps.user_id == User.id)
        .group_by(DailySteps.user_id, DailySteps.date)
        .subquery("best_prio_sub")
    )

    effective_ids = (
        select(func.min(DailySteps.id).label("id"))
        .join(User, DailySteps.user_id == User.id)
        .join(
            best_priority,
            (DailySteps.user_id == best_priority.c.user_id)
            & (DailySteps.date == best_priority.c.date),
        )
        .where(
            case(
                (DailySteps.source == User.preferred_step_source, 0),
                else_=1,
            )
            == best_priority.c.best_prio
        )
        .group_by(DailySteps.user_id, DailySteps.date)
        .subquery("effective_ids")
    )

    return effective_ids


def effective_steps_filter():
    """Return a filter condition that limits DailySteps to deduplicated rows.

    Usage::

        effective = effective_steps_filter()
        db.query(DailySteps).filter(effective).all()

    Or in aggregate queries::

        db.query(func.sum(DailySteps.step_count)).filter(
            DailySteps.user_id == user_id,
            effective,
        ).scalar()
    """
    effective = _effective_ids_subquery()
    return DailySteps.id.in_(select(effective.c.id))

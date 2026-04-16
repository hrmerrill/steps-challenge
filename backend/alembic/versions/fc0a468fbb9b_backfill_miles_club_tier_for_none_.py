"""backfill miles_club_tier for none participants

Revision ID: fc0a468fbb9b
Revises: 227d93f0d934
Create Date: 2026-04-16 09:13:45.530297

Participants who joined before the miles-club feature was added have
miles_club_tier = 'none'. This migration retroactively calculates their
tier from their prior-month step data, matching the logic in the
join_challenge endpoint.
"""

from __future__ import annotations

import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "fc0a468fbb9b"
down_revision: Union[str, None] = "227d93f0d934"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Inline thresholds so migration is self-contained and reproducible
HIGH_THRESHOLD = 10_000
MID_THRESHOLD = 5_000


def _calculate_tier(avg_daily_steps: float) -> str:
    """Return tier as the enum name (uppercase) matching SQLAlchemy's storage."""
    if avg_daily_steps >= HIGH_THRESHOLD:
        return "HIGH"
    if avg_daily_steps >= MID_THRESHOLD:
        return "MID"
    return "LOW"


def upgrade() -> None:
    conn = op.get_bind()

    rows = conn.execute(
        sa.text(
            "SELECT cp.id, cp.user_id, c.start_date "
            "FROM challenge_participants cp "
            "JOIN challenges c ON c.id = cp.challenge_id "
            "WHERE LOWER(cp.miles_club_tier) = 'none'"
        )
    ).fetchall()

    for cp_id, user_id, start_date in rows:
        if isinstance(start_date, str):
            start_date = datetime.date.fromisoformat(start_date)

        prior_month_end = start_date.replace(day=1) - datetime.timedelta(days=1)
        prior_month_start = prior_month_end.replace(day=1)
        days_in_month = (prior_month_end - prior_month_start).days + 1

        total = conn.execute(
            sa.text(
                "SELECT COALESCE(SUM(step_count), 0) "
                "FROM daily_steps "
                "WHERE user_id = :uid AND date >= :start AND date <= :end"
            ),
            {"uid": user_id, "start": prior_month_start, "end": prior_month_end},
        ).scalar()

        avg_daily = total / days_in_month if days_in_month > 0 else 0
        tier = _calculate_tier(avg_daily)

        conn.execute(
            sa.text(
                "UPDATE challenge_participants SET miles_club_tier = :tier WHERE id = :id"
            ),
            {"tier": tier, "id": cp_id},
        )


def downgrade() -> None:
    # Not reversible — we don't know which participants originally had 'none'.
    pass

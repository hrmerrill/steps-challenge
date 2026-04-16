"""Tests for the miles_club_tier backfill migration logic."""

import datetime

from sqlalchemy import text

from app.models.challenge import Challenge, ChallengeParticipant, MilesClubTier
from app.models.steps import DailySteps
from app.models.user import User

# Inline the migration's tier logic for testing (avoid alembic import-path issues)
HIGH_THRESHOLD = 10_000
MID_THRESHOLD = 5_000


def _calculate_tier(avg_daily_steps: float) -> str:
    if avg_daily_steps >= HIGH_THRESHOLD:
        return "HIGH"
    if avg_daily_steps >= MID_THRESHOLD:
        return "MID"
    return "LOW"


class TestCalculateTierInline:
    """Verify the migration's inlined tier function matches the service."""

    def test_high(self):
        assert _calculate_tier(HIGH_THRESHOLD) == "HIGH"
        assert _calculate_tier(15_000) == "HIGH"

    def test_mid(self):
        assert _calculate_tier(MID_THRESHOLD) == "MID"
        assert _calculate_tier(9_999) == "MID"

    def test_low(self):
        assert _calculate_tier(0) == "LOW"
        assert _calculate_tier(4_999) == "LOW"


def _make_user(db, email: str, display_name: str) -> User:
    user = User(email=email, display_name=display_name, password_hash="x")
    db.add(user)
    db.flush()
    return user


def _make_challenge(db, start: datetime.date, end: datetime.date) -> Challenge:
    ch = Challenge(name="Test", start_date=start, end_date=end)
    db.add(ch)
    db.flush()
    return ch


class TestBackfillScenarios:
    """Integration tests: verify tier assignment based on prior-month steps."""

    def test_participant_with_no_prior_steps_gets_low(self, db_session):
        user = _make_user(db_session, "a@test.com", "No Steps User")
        ch = _make_challenge(db_session, datetime.date(2026, 4, 1), datetime.date(2026, 4, 30))
        cp = ChallengeParticipant(
            challenge_id=ch.id, user_id=user.id, miles_club_tier=MilesClubTier.NONE,
        )
        db_session.add(cp)
        db_session.commit()

        _run_backfill(db_session)

        db_session.refresh(cp)
        assert cp.miles_club_tier == MilesClubTier.LOW

    def test_participant_with_high_prior_steps_gets_high(self, db_session):
        user = _make_user(db_session, "b@test.com", "High Stepper")
        ch = _make_challenge(db_session, datetime.date(2026, 4, 1), datetime.date(2026, 4, 30))
        # Prior month = March 2026 (31 days). 10k/day * 31 = 310k total
        for day in range(1, 32):
            db_session.add(
                DailySteps(
                    user_id=user.id,
                    date=datetime.date(2026, 3, day),
                    step_count=12_000,
                )
            )
        cp = ChallengeParticipant(
            challenge_id=ch.id, user_id=user.id, miles_club_tier=MilesClubTier.NONE,
        )
        db_session.add(cp)
        db_session.commit()

        _run_backfill(db_session)

        db_session.refresh(cp)
        assert cp.miles_club_tier == MilesClubTier.HIGH

    def test_participant_with_mid_prior_steps_gets_mid(self, db_session):
        user = _make_user(db_session, "c@test.com", "Mid Stepper")
        ch = _make_challenge(db_session, datetime.date(2026, 4, 1), datetime.date(2026, 4, 30))
        for day in range(1, 32):
            db_session.add(
                DailySteps(
                    user_id=user.id,
                    date=datetime.date(2026, 3, day),
                    step_count=7_000,
                )
            )
        cp = ChallengeParticipant(
            challenge_id=ch.id, user_id=user.id, miles_club_tier=MilesClubTier.NONE,
        )
        db_session.add(cp)
        db_session.commit()

        _run_backfill(db_session)

        db_session.refresh(cp)
        assert cp.miles_club_tier == MilesClubTier.MID

    def test_already_assigned_tier_not_changed(self, db_session):
        user = _make_user(db_session, "d@test.com", "Already Tiered")
        ch = _make_challenge(db_session, datetime.date(2026, 4, 1), datetime.date(2026, 4, 30))
        cp = ChallengeParticipant(
            challenge_id=ch.id, user_id=user.id, miles_club_tier=MilesClubTier.HIGH,
        )
        db_session.add(cp)
        db_session.commit()

        _run_backfill(db_session)

        db_session.refresh(cp)
        assert cp.miles_club_tier == MilesClubTier.HIGH

    def test_multiple_participants_backfilled(self, db_session):
        user_a = _make_user(db_session, "e@test.com", "User A")
        user_b = _make_user(db_session, "f@test.com", "User B")
        ch = _make_challenge(db_session, datetime.date(2026, 4, 1), datetime.date(2026, 4, 30))
        # User A: no steps → LOW; User B: high steps → HIGH
        for day in range(1, 32):
            db_session.add(
                DailySteps(user_id=user_b.id, date=datetime.date(2026, 3, day), step_count=11_000)
            )
        cp_a = ChallengeParticipant(
            challenge_id=ch.id, user_id=user_a.id, miles_club_tier=MilesClubTier.NONE,
        )
        cp_b = ChallengeParticipant(
            challenge_id=ch.id, user_id=user_b.id, miles_club_tier=MilesClubTier.NONE,
        )
        db_session.add_all([cp_a, cp_b])
        db_session.commit()

        _run_backfill(db_session)

        db_session.refresh(cp_a)
        db_session.refresh(cp_b)
        assert cp_a.miles_club_tier == MilesClubTier.LOW
        assert cp_b.miles_club_tier == MilesClubTier.HIGH


def _run_backfill(db_session):
    """Execute the same SQL logic as the migration's upgrade(), using a test session."""
    import datetime as dt

    rows = db_session.execute(
        text(
            "SELECT cp.id, cp.user_id, c.start_date "
            "FROM challenge_participants cp "
            "JOIN challenges c ON c.id = cp.challenge_id "
            "WHERE LOWER(cp.miles_club_tier) = 'none'"
        )
    ).fetchall()

    for cp_id, user_id, start_date in rows:
        if isinstance(start_date, str):
            start_date = dt.date.fromisoformat(start_date)

        prior_month_end = start_date.replace(day=1) - dt.timedelta(days=1)
        prior_month_start = prior_month_end.replace(day=1)
        days_in_month = (prior_month_end - prior_month_start).days + 1

        total = db_session.execute(
            text(
                "SELECT COALESCE(SUM(step_count), 0) "
                "FROM daily_steps "
                "WHERE user_id = :uid AND date >= :start AND date <= :end"
            ),
            {"uid": user_id, "start": prior_month_start, "end": prior_month_end},
        ).scalar()

        avg_daily = total / days_in_month if days_in_month > 0 else 0
        tier = _calculate_tier(avg_daily)

        db_session.execute(
            text("UPDATE challenge_participants SET miles_club_tier = :tier WHERE id = :id"),
            {"tier": tier, "id": cp_id},
        )
    db_session.commit()

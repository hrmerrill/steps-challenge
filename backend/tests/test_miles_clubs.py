"""Tests for miles club tier calculation."""

import datetime

from app.models.challenge import MilesClubTier
from app.models.steps import DailySteps
from app.models.user import User
from app.services.miles_clubs import (
    calculate_tier,
    get_bulk_user_tiers,
    get_prior_month_range,
    get_user_tier,
    tier_label,
)


class TestCalculateTier:
    def test_high_tier(self):
        assert calculate_tier(10_000) == MilesClubTier.HIGH
        assert calculate_tier(15_000) == MilesClubTier.HIGH

    def test_mid_tier(self):
        assert calculate_tier(5_000) == MilesClubTier.MID
        assert calculate_tier(9_999) == MilesClubTier.MID

    def test_low_tier(self):
        assert calculate_tier(0) == MilesClubTier.LOW
        assert calculate_tier(4_999) == MilesClubTier.LOW


class TestTierLabel:
    def test_high_label(self):
        assert tier_label(MilesClubTier.HIGH) == ">10k steps/day"

    def test_mid_label(self):
        assert tier_label(MilesClubTier.MID) == "5k\u201310k steps/day"

    def test_low_label(self):
        assert tier_label(MilesClubTier.LOW) == "0\u20135k steps/day"

    def test_none_label(self):
        assert tier_label(MilesClubTier.NONE) == ""


class TestGetPriorMonthRange:
    def test_april_gives_march(self):
        start, end = get_prior_month_range(datetime.date(2026, 4, 15))
        assert start == datetime.date(2026, 3, 1)
        assert end == datetime.date(2026, 3, 31)

    def test_january_gives_december(self):
        start, end = get_prior_month_range(datetime.date(2026, 1, 1))
        assert start == datetime.date(2025, 12, 1)
        assert end == datetime.date(2025, 12, 31)

    def test_march_gives_february(self):
        start, end = get_prior_month_range(datetime.date(2026, 3, 10))
        assert start == datetime.date(2026, 2, 1)
        assert end == datetime.date(2026, 2, 28)


class TestGetUserTier:
    def _make_user(self, db, email: str) -> User:
        user = User(email=email, display_name=email.split("@")[0], password_hash="x")
        db.add(user)
        db.flush()
        return user

    def test_no_steps_gives_low(self, db_session):
        user = self._make_user(db_session, "none@test.com")
        tier, avg = get_user_tier(user.id, db_session, reference_date=datetime.date(2026, 4, 1))
        assert tier == MilesClubTier.LOW
        assert avg == 0.0

    def test_high_steps_prior_month(self, db_session):
        user = self._make_user(db_session, "high@test.com")
        for day in range(1, 32):
            db_session.add(DailySteps(user_id=user.id, date=datetime.date(2026, 3, day), step_count=12_000))
        db_session.commit()
        tier, avg = get_user_tier(user.id, db_session, reference_date=datetime.date(2026, 4, 1))
        assert tier == MilesClubTier.HIGH
        assert avg == 12_000.0

    def test_mid_steps_prior_month(self, db_session):
        user = self._make_user(db_session, "mid@test.com")
        for day in range(1, 32):
            db_session.add(DailySteps(user_id=user.id, date=datetime.date(2026, 3, day), step_count=7_000))
        db_session.commit()
        tier, avg = get_user_tier(user.id, db_session, reference_date=datetime.date(2026, 4, 1))
        assert tier == MilesClubTier.MID
        assert avg == 7_000.0

    def test_steps_outside_prior_month_ignored(self, db_session):
        """Steps in the current month or older months don't affect the tier."""
        user = self._make_user(db_session, "outside@test.com")
        # Steps in April (current) and February (two months ago) — should be ignored
        db_session.add(DailySteps(user_id=user.id, date=datetime.date(2026, 4, 5), step_count=15_000))
        db_session.add(DailySteps(user_id=user.id, date=datetime.date(2026, 2, 15), step_count=15_000))
        db_session.commit()
        tier, avg = get_user_tier(user.id, db_session, reference_date=datetime.date(2026, 4, 1))
        assert tier == MilesClubTier.LOW
        assert avg == 0.0


class TestGetBulkUserTiers:
    def _make_user(self, db, email: str) -> User:
        user = User(email=email, display_name=email.split("@")[0], password_hash="x")
        db.add(user)
        db.flush()
        return user

    def test_empty_list(self, db_session):
        assert get_bulk_user_tiers([], db_session) == {}

    def test_multiple_users(self, db_session):
        u1 = self._make_user(db_session, "bulk1@test.com")
        u2 = self._make_user(db_session, "bulk2@test.com")
        for day in range(1, 32):
            db_session.add(DailySteps(user_id=u1.id, date=datetime.date(2026, 3, day), step_count=12_000))
            db_session.add(DailySteps(user_id=u2.id, date=datetime.date(2026, 3, day), step_count=3_000))
        db_session.commit()
        tiers = get_bulk_user_tiers([u1.id, u2.id], db_session, reference_date=datetime.date(2026, 4, 1))
        assert tiers[u1.id] == MilesClubTier.HIGH
        assert tiers[u2.id] == MilesClubTier.LOW

"""Tests for database models — schema validation, constraints, relationships."""

import datetime

from app.models.user import User
from app.models.steps import DailySteps, StepSource
from app.models.challenge import Challenge, ChallengeParticipant, MilesClubTier


class TestUserModel:
    def test_create_user(self, db_session):
        user = User(email="test@example.com", password_hash="hashed", display_name="Test User")
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.garmin_token is None
        assert user.strava_token is None
        assert user.fitbit_token is None

    def test_user_email_unique(self, db_session):
        user1 = User(email="dup@example.com", password_hash="h1", display_name="User 1")
        user2 = User(email="dup@example.com", password_hash="h2", display_name="User 2")
        db_session.add(user1)
        db_session.commit()
        db_session.add(user2)
        try:
            db_session.commit()
            assert False, "Should have raised IntegrityError"
        except Exception:
            db_session.rollback()

    def test_user_repr(self, db_session):
        user = User(email="repr@test.com", password_hash="h", display_name="R")
        db_session.add(user)
        db_session.commit()
        assert "repr@test.com" in repr(user)


class TestDailyStepsModel:
    def _make_user(self, db_session):
        user = User(email="stepper@test.com", password_hash="h", display_name="Stepper")
        db_session.add(user)
        db_session.commit()
        return user

    def test_create_daily_steps(self, db_session):
        user = self._make_user(db_session)
        steps = DailySteps(
            user_id=user.id,
            date=datetime.date(2026, 4, 15),
            step_count=10_000,
            source=StepSource.MANUAL,
        )
        db_session.add(steps)
        db_session.commit()

        assert steps.id is not None
        assert steps.step_count == 10_000
        assert steps.source == StepSource.MANUAL

    def test_unique_user_date(self, db_session):
        user = self._make_user(db_session)
        day = datetime.date(2026, 4, 15)
        db_session.add(DailySteps(user_id=user.id, date=day, step_count=5000))
        db_session.commit()
        db_session.add(DailySteps(user_id=user.id, date=day, step_count=8000))
        try:
            db_session.commit()
            assert False, "Should have raised IntegrityError for duplicate user+date"
        except Exception:
            db_session.rollback()

    def test_step_source_enum(self):
        assert StepSource.GARMIN.value == "garmin"
        assert StepSource.STRAVA.value == "strava"
        assert StepSource.FITBIT.value == "fitbit"
        assert StepSource.MANUAL.value == "manual"

    def test_relationship_to_user(self, db_session):
        user = self._make_user(db_session)
        steps = DailySteps(user_id=user.id, date=datetime.date(2026, 4, 15), step_count=7500)
        db_session.add(steps)
        db_session.commit()
        db_session.refresh(user)
        assert len(user.daily_steps) == 1
        assert user.daily_steps[0].step_count == 7500


class TestChallengeModel:
    def test_create_challenge(self, db_session):
        ch = Challenge(
            name="April 2026",
            start_date=datetime.date(2026, 4, 1),
            end_date=datetime.date(2026, 4, 30),
        )
        db_session.add(ch)
        db_session.commit()

        assert ch.id is not None
        assert ch.is_active is True
        assert ch.name == "April 2026"

    def test_challenge_repr(self, db_session):
        ch = Challenge(
            name="Test",
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 31),
        )
        db_session.add(ch)
        db_session.commit()
        assert "Test" in repr(ch)


class TestChallengeParticipantModel:
    def _setup(self, db_session):
        user = User(email="p@test.com", password_hash="h", display_name="P")
        ch = Challenge(
            name="Test Challenge",
            start_date=datetime.date(2026, 4, 1),
            end_date=datetime.date(2026, 4, 30),
        )
        db_session.add_all([user, ch])
        db_session.commit()
        return user, ch

    def test_create_participant(self, db_session):
        user, ch = self._setup(db_session)
        cp = ChallengeParticipant(
            challenge_id=ch.id, user_id=user.id, miles_club_tier=MilesClubTier.GOLD
        )
        db_session.add(cp)
        db_session.commit()

        assert cp.id is not None
        assert cp.miles_club_tier == MilesClubTier.GOLD

    def test_default_tier_is_none(self, db_session):
        user, ch = self._setup(db_session)
        cp = ChallengeParticipant(challenge_id=ch.id, user_id=user.id)
        db_session.add(cp)
        db_session.commit()
        assert cp.miles_club_tier == MilesClubTier.NONE

    def test_unique_challenge_user(self, db_session):
        user, ch = self._setup(db_session)
        db_session.add(ChallengeParticipant(challenge_id=ch.id, user_id=user.id))
        db_session.commit()
        db_session.add(ChallengeParticipant(challenge_id=ch.id, user_id=user.id))
        try:
            db_session.commit()
            assert False, "Should have raised IntegrityError"
        except Exception:
            db_session.rollback()

    def test_miles_club_tier_values(self):
        assert MilesClubTier.GOLD.value == "gold"
        assert MilesClubTier.SILVER.value == "silver"
        assert MilesClubTier.BRONZE.value == "bronze"
        assert MilesClubTier.NONE.value == "none"

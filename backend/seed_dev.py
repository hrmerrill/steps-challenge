#!/usr/bin/env python3
"""
Seed the local dev database with sample data.

Usage:
    cd backend
    DATABASE_URL=sqlite:///./dev.db python seed_dev.py

Creates tables (via Alembic), sample users, an active challenge,
participants, and daily step history so the dashboard is functional
without any manual setup.
"""

import datetime
import os
import random
import sys

# Ensure DATABASE_URL and JWT_SECRET are set for dev mode
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///./dev.db"
if "JWT_SECRET" not in os.environ:
    os.environ["JWT_SECRET"] = "dev-only-secret-not-for-production-use!!"

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.challenge import (  # noqa: E402
    Challenge,
    ChallengeParticipant,
    MilesClubTier,
)
from app.models.steps import DailySteps, StepSource  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.auth import hash_password  # noqa: E402

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

TODAY = datetime.date.today()
CHALLENGE_START = TODAY.replace(day=1)
CHALLENGE_END = (CHALLENGE_START + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

USERS = [
    {"email": "alice@example.com", "display_name": "Alice", "password": "Test1234!"},
    {"email": "bob@example.com", "display_name": "Bob", "password": "Test1234!"},
    {"email": "carol@example.com", "display_name": "Carol", "password": "Test1234!"},
    {"email": "dave@example.com", "display_name": "Dave", "password": "Test1234!"},
    {"email": "eve@example.com", "display_name": "Eve", "password": "Test1234!"},
    {"email": "frank@example.com", "display_name": "Frank", "password": "Test1234!"},
]

# Average daily steps per user (creates variety for leaderboard & miles clubs)
USER_STEP_PROFILES = {
    "alice@example.com": (11000, 2500),   # high tier
    "bob@example.com": (9000, 2000),      # high tier (borderline)
    "carol@example.com": (7000, 1800),    # mid tier
    "dave@example.com": (6500, 2000),     # mid tier
    "eve@example.com": (4000, 1500),      # low tier
    "frank@example.com": (3000, 1200),    # low tier
}


def run_migrations() -> None:
    """Create tables from ORM models (avoids Alembic's PostgreSQL-specific defaults)."""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("  Tables ready.")


def seed() -> None:
    """Insert sample data if the database is empty."""
    db = SessionLocal()
    try:
        existing = db.query(User).first()
        if existing:
            print("Database already has data — skipping seed.")
            return

        print("Seeding users...")
        user_objs: dict[str, User] = {}
        for u in USERS:
            user = User(
                email=u["email"],
                display_name=u["display_name"],
                password_hash=hash_password(u["password"]),
            )
            db.add(user)
            db.flush()
            user_objs[u["email"]] = user
        print(f"  Created {len(user_objs)} users (password: Test1234!)")

        print("Seeding challenge...")
        challenge = Challenge(
            name=f"{CHALLENGE_START.strftime('%B %Y')} Steps Challenge",
            description="Walk, run, or hike — every step counts!",
            start_date=CHALLENGE_START,
            end_date=CHALLENGE_END,
            is_active=True,
        )
        db.add(challenge)
        db.flush()

        tier_map = {
            "alice@example.com": MilesClubTier.HIGH,
            "bob@example.com": MilesClubTier.HIGH,
            "carol@example.com": MilesClubTier.MID,
            "dave@example.com": MilesClubTier.MID,
            "eve@example.com": MilesClubTier.LOW,
            "frank@example.com": MilesClubTier.LOW,
        }
        for email, user in user_objs.items():
            db.add(
                ChallengeParticipant(
                    challenge_id=challenge.id,
                    user_id=user.id,
                    miles_club_tier=tier_map[email],
                )
            )
        print(f"  Created challenge: {challenge.name} ({CHALLENGE_START} → {CHALLENGE_END})")

        print("Seeding daily steps...")
        rng = random.Random(42)  # deterministic for reproducibility
        total_steps = 0
        day = CHALLENGE_START
        while day <= min(TODAY, CHALLENGE_END):
            for email, user in user_objs.items():
                mean, std = USER_STEP_PROFILES[email]
                steps = max(500, int(rng.gauss(mean, std)))
                db.add(
                    DailySteps(
                        user_id=user.id,
                        date=day,
                        step_count=steps,
                        source=StepSource.MANUAL,
                    )
                )
                total_steps += steps
            day += datetime.timedelta(days=1)

        days_seeded = (min(TODAY, CHALLENGE_END) - CHALLENGE_START).days + 1
        miles = total_steps / 2000
        print(f"  Generated {days_seeded} days × {len(user_objs)} users = {total_steps:,} steps ({miles:,.0f} mi)")

        db.commit()
        print("Seed complete!")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migrations()
    seed()

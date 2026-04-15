"""Leaderboard router — rankings, stats, and trail progress."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.challenge import Challenge, ChallengeParticipant
from app.models.steps import DailySteps
from app.models.user import User
from app.schemas.challenge import LeaderboardEntry, TrailProgress
from app.services.auth import get_current_user
from app.services.trail import calculate_trail_progress, steps_to_miles

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/{challenge_id}", response_model=list[LeaderboardEntry])
def get_leaderboard(challenge_id: int, db: Session = Depends(get_db)):
    """Get ranked leaderboard for a challenge."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Get all participants with their step totals for the challenge period
    results = (
        db.query(
            User.id,
            User.display_name,
            ChallengeParticipant.miles_club_tier,
            func.coalesce(func.sum(DailySteps.step_count), 0).label("total_steps"),
        )
        .join(ChallengeParticipant, ChallengeParticipant.user_id == User.id)
        .outerjoin(
            DailySteps,
            (DailySteps.user_id == User.id)
            & (DailySteps.date >= challenge.start_date)
            & (DailySteps.date <= challenge.end_date),
        )
        .filter(ChallengeParticipant.challenge_id == challenge_id)
        .group_by(User.id, User.display_name, ChallengeParticipant.miles_club_tier)
        .order_by(func.coalesce(func.sum(DailySteps.step_count), 0).desc())
        .all()
    )

    return [
        LeaderboardEntry(
            rank=i + 1,
            user_id=row[0],
            display_name=row[1],
            miles_club_tier=row[2],
            total_steps=row[3],
            total_miles=steps_to_miles(row[3]),
        )
        for i, row in enumerate(results)
    ]


@router.get("/{challenge_id}/trail", response_model=TrailProgress)
def get_trail_progress(
    challenge_id: int,
    trail: str = Query("appalachian", description="Trail key: appalachian, pacific_crest, continental_divide"),
    db: Session = Depends(get_db),
):
    """Get group trail progress for a challenge."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Sum all participant steps during the challenge period
    participants = (
        db.query(ChallengeParticipant.user_id)
        .filter(ChallengeParticipant.challenge_id == challenge_id)
        .subquery()
    )

    total_steps = (
        db.query(func.coalesce(func.sum(DailySteps.step_count), 0))
        .filter(
            DailySteps.user_id.in_(db.query(participants.c.user_id)),
            DailySteps.date >= challenge.start_date,
            DailySteps.date <= challenge.end_date,
        )
        .scalar()
    )

    return calculate_trail_progress(total_steps, trail)

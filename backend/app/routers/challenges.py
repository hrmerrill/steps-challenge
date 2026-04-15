"""Challenges router — CRUD and joining challenges."""

import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.challenge import Challenge, ChallengeParticipant
from app.models.steps import DailySteps
from app.models.user import User
from app.schemas.challenge import ChallengeCreate, ChallengeResponse
from app.services.auth import get_current_user
from app.services.miles_clubs import calculate_tier

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.post("/", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
def create_challenge(
    body: ChallengeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new monthly challenge."""
    if body.end_date <= body.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    challenge = Challenge(name=body.name, start_date=body.start_date, end_date=body.end_date)
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return ChallengeResponse(
        id=challenge.id,
        name=challenge.name,
        start_date=challenge.start_date,
        end_date=challenge.end_date,
        is_active=challenge.is_active,
        participant_count=0,
    )


@router.get("/", response_model=list[ChallengeResponse])
def list_challenges(db: Session = Depends(get_db)):
    """List all challenges with participant counts."""
    challenges = db.query(Challenge).order_by(Challenge.start_date.desc()).all()
    result = []
    for ch in challenges:
        count = db.query(ChallengeParticipant).filter(ChallengeParticipant.challenge_id == ch.id).count()
        result.append(ChallengeResponse(
            id=ch.id, name=ch.name, start_date=ch.start_date,
            end_date=ch.end_date, is_active=ch.is_active, participant_count=count,
        ))
    return result


@router.post("/{challenge_id}/join", status_code=status.HTTP_201_CREATED)
def join_challenge(
    challenge_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Join a challenge. Miles club tier is calculated from prior month steps."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    existing = (
        db.query(ChallengeParticipant)
        .filter(ChallengeParticipant.challenge_id == challenge_id, ChallengeParticipant.user_id == user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already joined this challenge")

    # Calculate miles club tier from previous month's steps
    prior_month_start = (challenge.start_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    prior_month_end = challenge.start_date.replace(day=1) - datetime.timedelta(days=1)
    prior_steps = (
        db.query(func.coalesce(func.sum(DailySteps.step_count), 0))
        .filter(
            DailySteps.user_id == user.id,
            DailySteps.date >= prior_month_start,
            DailySteps.date <= prior_month_end,
        )
        .scalar()
    )

    tier = calculate_tier(prior_steps)
    participant = ChallengeParticipant(
        challenge_id=challenge_id, user_id=user.id, miles_club_tier=tier
    )
    db.add(participant)
    db.commit()

    return {"joined": True, "miles_club_tier": tier.value, "prior_month_steps": prior_steps}

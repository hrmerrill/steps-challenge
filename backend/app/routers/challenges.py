"""Challenges router — CRUD and joining challenges."""

import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.challenge import Challenge, ChallengeParticipant
from app.models.steps import DailySteps
from app.models.user import User
from app.schemas.challenge import ChallengeCreate, ChallengeResponse, ChallengeMembership, UserChallengeStats
from app.services.auth import get_current_user
from app.services.miles_clubs import calculate_tier
from app.services.trail import steps_to_miles

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

    challenge = Challenge(
        name=body.name, description=body.description,
        start_date=body.start_date, end_date=body.end_date,
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return ChallengeResponse(
        id=challenge.id,
        name=challenge.name,
        description=challenge.description,
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
            id=ch.id, name=ch.name, description=ch.description, start_date=ch.start_date,
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


@router.get("/{challenge_id}/membership", response_model=ChallengeMembership)
def get_membership(
    challenge_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if the current user has joined a challenge."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    participant = (
        db.query(ChallengeParticipant)
        .filter(ChallengeParticipant.challenge_id == challenge_id, ChallengeParticipant.user_id == user.id)
        .first()
    )
    if participant:
        return ChallengeMembership(joined=True, miles_club_tier=participant.miles_club_tier)
    return ChallengeMembership(joined=False)


@router.get("/{challenge_id}/my-stats", response_model=UserChallengeStats)
def get_my_stats(
    challenge_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's stats for a challenge."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    participant = (
        db.query(ChallengeParticipant)
        .filter(ChallengeParticipant.challenge_id == challenge_id, ChallengeParticipant.user_id == user.id)
        .first()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Not a participant in this challenge")

    # User's total steps and days logged during the challenge period
    user_steps = (
        db.query(
            func.coalesce(func.sum(DailySteps.step_count), 0).label("total"),
            func.count(DailySteps.id).label("days"),
        )
        .filter(
            DailySteps.user_id == user.id,
            DailySteps.date >= challenge.start_date,
            DailySteps.date <= challenge.end_date,
        )
        .one()
    )
    total_steps = int(user_steps.total)
    days_logged = int(user_steps.days)

    # Calculate rank: count participants with more steps
    participants_above = (
        db.query(func.count())
        .select_from(ChallengeParticipant)
        .outerjoin(
            DailySteps,
            (DailySteps.user_id == ChallengeParticipant.user_id)
            & (DailySteps.date >= challenge.start_date)
            & (DailySteps.date <= challenge.end_date),
        )
        .filter(ChallengeParticipant.challenge_id == challenge_id)
        .group_by(ChallengeParticipant.user_id)
        .having(func.coalesce(func.sum(DailySteps.step_count), 0) > total_steps)
        .subquery()
    )
    rank = db.query(func.count()).select_from(participants_above).scalar() + 1

    total_participants = (
        db.query(ChallengeParticipant)
        .filter(ChallengeParticipant.challenge_id == challenge_id)
        .count()
    )

    avg_daily = round(total_steps / days_logged, 1) if days_logged > 0 else 0.0

    return UserChallengeStats(
        user_id=user.id,
        display_name=user.display_name,
        challenge_id=challenge_id,
        total_steps=total_steps,
        total_miles=steps_to_miles(total_steps),
        rank=rank,
        total_participants=total_participants,
        days_logged=days_logged,
        average_daily=avg_daily,
        miles_club_tier=participant.miles_club_tier,
    )

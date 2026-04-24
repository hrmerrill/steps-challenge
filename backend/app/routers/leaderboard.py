"""Leaderboard router — rankings, stats, and trail progress."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.challenge import Challenge, ChallengeParticipant, MilesClubTier
from app.models.steps import DailySteps
from app.models.user import User
from app.schemas.challenge import LeaderboardEntry, OverallTeamStats, OverallUserStats, TrailProgress
from app.services.auth import get_current_user
from app.services.miles_clubs import get_bulk_user_tiers, get_user_tier
from app.services.steps_query import effective_steps_filter
from app.services.trail import calculate_trail_progress, steps_to_miles

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


# ── Overall (all-time) endpoints — must be before /{challenge_id} routes ──


@router.get("/overall", response_model=list[LeaderboardEntry])
def get_overall_leaderboard(db: Session = Depends(get_db)):
    """Get all-time leaderboard ranked by total steps across all dates."""
    results = (
        db.query(
            User.id,
            User.display_name,
            User.profile_photo_url,
            func.coalesce(func.sum(DailySteps.step_count), 0).label("total_steps"),
        )
        .outerjoin(DailySteps, (DailySteps.user_id == User.id) & effective_steps_filter())
        .group_by(User.id, User.display_name, User.profile_photo_url)
        .having(func.coalesce(func.sum(DailySteps.step_count), 0) > 0)
        .order_by(func.coalesce(func.sum(DailySteps.step_count), 0).desc())
        .all()
    )

    user_ids = [row[0] for row in results]
    tiers = get_bulk_user_tiers(user_ids, db)

    return [
        LeaderboardEntry(
            rank=i + 1,
            user_id=row[0],
            display_name=row[1],
            profile_photo_url=row[2],
            miles_club_tier=tiers.get(row[0], MilesClubTier.NONE),
            total_steps=row[3],
            total_miles=steps_to_miles(row[3]),
        )
        for i, row in enumerate(results)
    ]


@router.get("/overall/trail", response_model=TrailProgress)
def get_overall_trail_progress(
    trail: str = Query("appalachian", description="Trail key"),
    db: Session = Depends(get_db),
):
    """Get trail progress using all-time steps from all users."""
    total_steps = (
        db.query(func.coalesce(func.sum(DailySteps.step_count), 0))
        .filter(effective_steps_filter())
        .scalar()
    )
    return calculate_trail_progress(total_steps, trail)


@router.get("/overall/team-stats", response_model=OverallTeamStats)
def get_overall_team_stats(db: Session = Depends(get_db)):
    """Get aggregate all-time stats across all users (no auth required)."""
    agg = (
        db.query(
            func.coalesce(func.sum(DailySteps.step_count), 0).label("total"),
            func.count(DailySteps.id).label("days"),
        )
        .filter(effective_steps_filter())
        .one()
    )
    total_steps = int(agg.total)
    total_days = int(agg.days)

    total_users = (
        db.query(func.count(func.distinct(DailySteps.user_id)))
        .filter(effective_steps_filter())
        .scalar() or 0
    )

    avg_daily = round(total_steps / total_days, 1) if total_days > 0 else 0.0

    return OverallTeamStats(
        total_steps=total_steps,
        total_miles=steps_to_miles(total_steps),
        total_users=total_users,
        total_days_logged=total_days,
        average_daily_per_user=avg_daily,
    )


@router.get("/overall/my-stats", response_model=OverallUserStats)
def get_overall_my_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's all-time stats with rank."""
    user_agg = (
        db.query(
            func.coalesce(func.sum(DailySteps.step_count), 0).label("total"),
            func.count(DailySteps.id).label("days"),
        )
        .filter(DailySteps.user_id == user.id, effective_steps_filter())
        .one()
    )
    total_steps = int(user_agg.total)
    days_logged = int(user_agg.days)

    # Rank: count users with more total steps
    users_above = (
        db.query(func.count())
        .select_from(User)
        .outerjoin(DailySteps, (DailySteps.user_id == User.id) & effective_steps_filter())
        .group_by(User.id)
        .having(func.coalesce(func.sum(DailySteps.step_count), 0) > total_steps)
        .subquery()
    )
    rank = db.query(func.count()).select_from(users_above).scalar() + 1

    # Total users who have logged at least one step
    total_users = (
        db.query(func.count(func.distinct(DailySteps.user_id)))
        .filter(effective_steps_filter())
        .scalar()
    )
    # Ensure current user is counted even with 0 steps
    if total_steps == 0 and total_users > 0:
        total_users += 1
    elif total_users == 0:
        total_users = 1

    avg_daily = round(total_steps / days_logged, 1) if days_logged > 0 else 0.0

    tier, tier_avg = get_user_tier(user.id, db)

    return OverallUserStats(
        user_id=user.id,
        display_name=user.display_name,
        total_steps=total_steps,
        total_miles=steps_to_miles(total_steps),
        rank=rank,
        total_users=total_users,
        days_logged=days_logged,
        average_daily=avg_daily,
        miles_club_tier=tier,
        miles_club_average_daily=tier_avg,
    )


# ── Per-challenge endpoints ──


@router.get("/{challenge_id}", response_model=list[LeaderboardEntry])
def get_leaderboard(challenge_id: int = Path(gt=0), db: Session = Depends(get_db)):
    """Get ranked leaderboard for a challenge."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Get all participants with their step totals for the challenge period
    results = (
        db.query(
            User.id,
            User.display_name,
            User.profile_photo_url,
            func.coalesce(func.sum(DailySteps.step_count), 0).label("total_steps"),
        )
        .join(ChallengeParticipant, ChallengeParticipant.user_id == User.id)
        .outerjoin(
            DailySteps,
            (DailySteps.user_id == User.id)
            & (DailySteps.date >= challenge.start_date)
            & (DailySteps.date <= challenge.end_date)
            & effective_steps_filter(),
        )
        .filter(ChallengeParticipant.challenge_id == challenge_id)
        .group_by(User.id, User.display_name, User.profile_photo_url)
        .order_by(func.coalesce(func.sum(DailySteps.step_count), 0).desc())
        .all()
    )

    # Compute tiers from the month before the challenge started
    user_ids = [row[0] for row in results]
    tiers = get_bulk_user_tiers(user_ids, db, reference_date=challenge.start_date)

    return [
        LeaderboardEntry(
            rank=i + 1,
            user_id=row[0],
            display_name=row[1],
            profile_photo_url=row[2],
            miles_club_tier=tiers.get(row[0], MilesClubTier.NONE),
            total_steps=row[3],
            total_miles=steps_to_miles(row[3]),
        )
        for i, row in enumerate(results)
    ]


@router.get("/{challenge_id}/trail", response_model=TrailProgress)
def get_trail_progress(
    challenge_id: int = Path(gt=0),
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
            effective_steps_filter(),
        )
        .scalar()
    )

    return calculate_trail_progress(total_steps, trail)

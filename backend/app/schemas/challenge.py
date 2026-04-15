"""Pydantic schemas for challenges and miles clubs."""

import datetime

from pydantic import BaseModel, Field

from app.models.challenge import MilesClubTier


class ChallengeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    start_date: datetime.date
    end_date: datetime.date


class ChallengeResponse(BaseModel):
    id: int
    name: str
    start_date: datetime.date
    end_date: datetime.date
    is_active: bool
    participant_count: int = 0

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    total_steps: int
    miles_club_tier: MilesClubTier
    total_miles: float


class TrailProgress(BaseModel):
    total_group_steps: int
    total_group_miles: float
    trail_name: str
    trail_length_miles: float
    progress_percent: float


class UserChallengeStats(BaseModel):
    """Per-challenge stats for the authenticated user."""

    user_id: int
    display_name: str
    challenge_id: int
    total_steps: int
    total_miles: float
    rank: int
    total_participants: int
    days_logged: int
    average_daily: float
    miles_club_tier: MilesClubTier


class ChallengeMembership(BaseModel):
    """Whether the current user has joined a challenge."""

    joined: bool
    miles_club_tier: MilesClubTier | None = None

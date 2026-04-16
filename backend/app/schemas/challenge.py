"""Pydantic schemas for challenges and miles clubs."""

import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.challenge import MilesClubTier


class ChallengeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    start_date: datetime.date
    end_date: datetime.date

    @model_validator(mode="after")
    def validate_dates(self) -> "ChallengeCreate":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        duration = (self.end_date - self.start_date).days
        if duration > 366:
            raise ValueError("Challenge duration cannot exceed 366 days")
        return self


class ChallengeResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    start_date: datetime.date
    end_date: datetime.date
    is_active: bool
    participant_count: int = 0

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    profile_photo_url: str | None = None
    total_steps: int
    miles_club_tier: MilesClubTier = MilesClubTier.NONE
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


class OverallUserStats(BaseModel):
    """All-time stats for the authenticated user across all challenges."""

    user_id: int
    display_name: str
    total_steps: int
    total_miles: float
    rank: int
    total_users: int
    days_logged: int
    average_daily: float
    miles_club_tier: MilesClubTier = MilesClubTier.NONE
    miles_club_average_daily: float = 0.0


class TeamChallengeStats(BaseModel):
    """Aggregate stats for all participants in a challenge."""

    challenge_id: int
    total_steps: int
    total_miles: float
    total_participants: int
    total_days_logged: int
    average_daily_per_participant: float


class OverallTeamStats(BaseModel):
    """Aggregate all-time stats across all users."""

    total_steps: int
    total_miles: float
    total_users: int
    total_days_logged: int
    average_daily_per_user: float

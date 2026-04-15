"""Pydantic schemas for step-related requests and responses."""

import datetime

from pydantic import BaseModel, Field

from app.models.steps import StepSource


class StepEntry(BaseModel):
    date: datetime.date
    step_count: int = Field(gt=0, le=500_000)
    source: StepSource = StepSource.MANUAL


class StepResponse(BaseModel):
    id: int
    user_id: int
    date: datetime.date
    step_count: int
    source: StepSource

    model_config = {"from_attributes": True}


class StepSummary(BaseModel):
    total_steps: int
    total_miles: float
    days_logged: int
    average_daily: float

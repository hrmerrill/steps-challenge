"""Pydantic schemas for step-related requests and responses."""

import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.steps import StepSource


class StepEntry(BaseModel):
    date: datetime.date
    step_count: int = Field(gt=0, le=100_000)
    source: StepSource = StepSource.MANUAL

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v: datetime.date) -> datetime.date:
        if v > datetime.date.today():
            raise ValueError("Date cannot be in the future")
        earliest = datetime.date.today() - datetime.timedelta(days=365 * 2)
        if v < earliest:
            raise ValueError("Date cannot be more than 2 years in the past")
        return v


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

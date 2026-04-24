"""Steps router — manual step entry CRUD and sync triggers."""

import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.steps import DailySteps, StepSource
from app.models.user import User
from app.schemas.steps import StepEntry, StepResponse, StepSummary
from app.services.auth import get_current_user
from app.services.steps_query import effective_steps_filter

router = APIRouter(prefix="/steps", tags=["steps"])


@router.post("/", response_model=StepResponse, status_code=status.HTTP_201_CREATED)
def log_steps(body: StepEntry, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Log steps for a specific date. Updates existing entry if one exists for that date and source."""
    existing = (
        db.query(DailySteps)
        .filter(
            DailySteps.user_id == user.id,
            DailySteps.date == body.date,
            DailySteps.source == body.source,
        )
        .first()
    )

    if existing:
        existing.step_count = body.step_count
        db.commit()
        db.refresh(existing)
        return existing

    entry = DailySteps(
        user_id=user.id,
        date=body.date,
        step_count=body.step_count,
        source=body.source,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[StepResponse])
def get_steps(
    start_date: datetime.date | None = Query(None),
    end_date: datetime.date | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get step entries for the current user, optionally filtered by date range."""
    query = db.query(DailySteps).filter(DailySteps.user_id == user.id)
    if start_date:
        query = query.filter(DailySteps.date >= start_date)
    if end_date:
        query = query.filter(DailySteps.date <= end_date)
    return query.order_by(DailySteps.date.desc()).all()


@router.get("/summary", response_model=StepSummary)
def get_summary(
    start_date: datetime.date | None = Query(None),
    end_date: datetime.date | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get summary statistics for the current user's steps."""
    query = db.query(DailySteps).filter(DailySteps.user_id == user.id)
    if start_date:
        query = query.filter(DailySteps.date >= start_date)
    if end_date:
        query = query.filter(DailySteps.date <= end_date)

    result = db.query(
        func.coalesce(func.sum(DailySteps.step_count), 0),
        func.count(DailySteps.id),
    ).filter(
        DailySteps.user_id == user.id,
        effective_steps_filter(),
        *([DailySteps.date >= start_date] if start_date else []),
        *([DailySteps.date <= end_date] if end_date else []),
    ).first()

    total_steps = result[0]
    days_logged = result[1]
    from app.services.trail import steps_to_miles

    return StepSummary(
        total_steps=total_steps,
        total_miles=steps_to_miles(total_steps),
        days_logged=days_logged,
        average_daily=round(total_steps / days_logged, 1) if days_logged > 0 else 0,
    )


@router.delete("/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_steps(step_id: int = Path(gt=0), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a step entry (only own manual entries)."""
    entry = db.query(DailySteps).filter(DailySteps.id == step_id, DailySteps.user_id == user.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Step entry not found")
    if entry.source != StepSource.MANUAL:
        raise HTTPException(status_code=403, detail="Cannot delete synced entries — disconnect the provider instead")
    db.delete(entry)
    db.commit()

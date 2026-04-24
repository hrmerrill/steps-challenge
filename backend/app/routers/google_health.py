"""Google Health API integration router — OAuth flow, step sync, and connection management."""

import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.steps import DailySteps, StepSource
from app.models.user import User
from app.services.auth import create_access_token, decode_token, get_current_user
from app.services.google_health import (
    exchange_code_for_tokens,
    fetch_daily_steps,
    get_authorization_url,
    is_google_health_configured,
    refresh_access_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/google-health", tags=["google-health"])


@router.get("/connect")
def connect_google_health(user: User = Depends(get_current_user)):
    """Return the Google OAuth authorization URL to redirect the user to."""
    if not is_google_health_configured():
        raise HTTPException(
            status_code=501,
            detail="Google Health integration is not configured on this server",
        )
    if user.google_health_token:
        raise HTTPException(status_code=409, detail="Google Health is already connected")

    # Embed a JWT in the OAuth state so the callback can identify the user
    # without needing an Authorization header on the browser redirect.
    state_token = create_access_token(user.id)
    return {"authorization_url": get_authorization_url(state=state_token)}


@router.get("/callback")
async def google_health_callback(
    code: str = Query(..., description="OAuth authorization code from Google"),
    state: str = Query(..., description="OAuth state containing the user JWT"),
    db: Session = Depends(get_db),
):
    """Handle the OAuth callback — exchange code for tokens and store them.

    The user is identified via the JWT embedded in the ``state`` parameter
    (set during ``/connect``), since the browser redirect from Google does
    not carry an ``Authorization`` header.
    """
    if not is_google_health_configured():
        raise HTTPException(status_code=501, detail="Google Health integration is not configured")

    user_id = decode_token(state)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    result = await exchange_code_for_tokens(code)
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)

    user.google_health_token = result.access_token
    user.google_health_refresh_token = result.refresh_token
    user.preferred_step_source = StepSource.GOOGLE_HEALTH
    db.commit()

    redirect_url = f"{settings.frontend_url.rstrip('/')}/#/profile?google_health=connected"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/sync")
async def sync_google_health_steps(
    days: int = Query(default=30, ge=1, le=30, description="Number of past days to sync"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pull daily step data from Google Health API for the specified number of past days."""
    if not user.google_health_token:
        raise HTTPException(status_code=400, detail="Google Health is not connected")

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days - 1)

    # Try fetching with current token
    result = await fetch_daily_steps(user.google_health_token, start_date, end_date)

    # If token expired, try refreshing
    if not result.success and "expired" in (result.error or "").lower() and user.google_health_refresh_token:
        refresh_result = await refresh_access_token(user.google_health_refresh_token)
        if refresh_result.success:
            user.google_health_token = refresh_result.access_token
            user.google_health_refresh_token = refresh_result.refresh_token
            db.commit()
            result = await fetch_daily_steps(user.google_health_token, start_date, end_date)
        else:
            raise HTTPException(
                status_code=502,
                detail=f"Token refresh failed: {refresh_result.error}",
            )

    if not result.success:
        raise HTTPException(
            status_code=result.status_code or 502,
            detail=result.error,
        )

    # Upsert each day's steps
    synced_count = 0
    for entry in result.steps:
        entry_date = datetime.date.fromisoformat(entry["date"])
        existing = (
            db.query(DailySteps)
            .filter(
                DailySteps.user_id == user.id,
                DailySteps.date == entry_date,
                DailySteps.source == StepSource.GOOGLE_HEALTH,
            )
            .first()
        )
        if existing:
            existing.step_count = entry["step_count"]
        else:
            db.add(DailySteps(
                user_id=user.id,
                date=entry_date,
                step_count=entry["step_count"],
                source=StepSource.GOOGLE_HEALTH,
            ))
        synced_count += 1

    db.commit()

    return {
        "synced": True,
        "days_synced": synced_count,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


@router.post("/disconnect")
def disconnect_google_health(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect Google Health — clears tokens, reverts preferred source to manual.

    Google Health step data is preserved in the database but will no longer be
    the preferred source for leaderboard/stats.
    """
    if not user.google_health_token:
        raise HTTPException(status_code=400, detail="Google Health is not connected")

    user.google_health_token = None
    user.google_health_refresh_token = None
    if user.preferred_step_source == StepSource.GOOGLE_HEALTH:
        user.preferred_step_source = StepSource.MANUAL
    db.commit()

    return {"disconnected": True, "preferred_step_source": "manual"}


@router.get("/status")
def google_health_status(user: User = Depends(get_current_user)):
    """Return Google Health connection status."""
    return {
        "configured": is_google_health_configured(),
        "connected": user.google_health_token is not None,
        "preferred_step_source": user.preferred_step_source.value,
    }

"""Google Health API integration service.

Handles OAuth 2.0 token exchange, token refresh, and daily step data
retrieval from the Google Health API (successor to the Fitbit Web API).

Credentials are managed in Google Cloud Console → APIs & Services → Credentials.
Enable the "Google Health API" under APIs & Services → Library.
"""

import datetime
import logging
from dataclasses import dataclass, field

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Google OAuth 2.0 / Health API endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_HEALTH_API_BASE = "https://www.googleapis.com/fitness/v1"

# Scopes needed: read activity data (includes steps)
GOOGLE_HEALTH_SCOPES = "https://www.googleapis.com/auth/fitness.activity.read"


def is_google_health_configured() -> bool:
    """Return True if Google Health API OAuth credentials are configured."""
    return bool(
        settings.google_client_id
        and settings.google_client_secret
        and settings.google_redirect_uri
    )


def get_authorization_url(state: str) -> str:
    """Build the Google OAuth 2.0 authorization URL for user consent.

    *state* is an opaque token (typically a JWT) passed through the OAuth flow
    so the callback can identify the user without requiring an ``Authorization``
    header on the redirect.
    """
    if not is_google_health_configured():
        raise ValueError("Google Health API OAuth is not configured")

    params = {
        "response_type": "code",
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "scope": GOOGLE_HEALTH_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    query = "&".join(f"{k}={httpx.URL('', params={k: v}).params[k]}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


@dataclass
class TokenResult:
    """Result of a Google OAuth token exchange or refresh."""
    access_token: str = ""
    refresh_token: str = ""
    error: str | None = None
    success: bool = True

    def __post_init__(self):
        self.success = self.error is None


@dataclass
class SyncResult:
    """Result of a Google Health step sync operation."""
    steps: list[dict] = field(default_factory=list)
    error: str | None = None
    success: bool = True

    def __post_init__(self):
        self.success = self.error is None


async def exchange_code_for_tokens(code: str) -> TokenResult:
    """Exchange an OAuth authorization code for access + refresh tokens."""
    if not is_google_health_configured():
        return TokenResult(error="Google Health API OAuth is not configured")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.google_redirect_uri,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()
            return TokenResult(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", ""),
            )
        except httpx.HTTPStatusError as e:
            logger.error("Google token exchange failed: %s %s", e.response.status_code, e.response.text)
            return TokenResult(error=f"Token exchange failed: {e.response.status_code}")
        except Exception as e:
            logger.error("Google token exchange error: %s", e)
            return TokenResult(error=f"Token exchange error: {e}")


async def refresh_access_token(refresh_token: str) -> TokenResult:
    """Refresh an expired Google access token."""
    if not is_google_health_configured():
        return TokenResult(error="Google Health API OAuth is not configured")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()
            return TokenResult(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", refresh_token),
            )
        except httpx.HTTPStatusError as e:
            logger.error("Google token refresh failed: %s", e.response.status_code)
            return TokenResult(error=f"Token refresh failed: {e.response.status_code}")
        except Exception as e:
            logger.error("Google token refresh error: %s", e)
            return TokenResult(error=f"Token refresh error: {e}")


async def fetch_daily_steps(
    access_token: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> SyncResult:
    """Fetch daily step totals from the Google Health API for a date range.

    Uses the dataset aggregate endpoint:
    POST /users/me/dataset:aggregate

    Returns a list of {date: str, step_count: int} dicts.
    Max range: 30 days per request.
    """
    if (end_date - start_date).days > 30:
        return SyncResult(error="Date range cannot exceed 30 days")

    # Convert dates to epoch milliseconds for the Google Fitness API
    start_ms = int(datetime.datetime.combine(start_date, datetime.time.min).timestamp() * 1000)
    end_ms = int(datetime.datetime.combine(end_date, datetime.time.max).timestamp() * 1000)

    url = f"{GOOGLE_HEALTH_API_BASE}/users/me/dataset:aggregate"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
                    "bucketByTime": {"durationMillis": 86400000},  # 1 day
                    "startTimeMillis": start_ms,
                    "endTimeMillis": end_ms,
                },
            )
            response.raise_for_status()
            data = response.json()

            steps = []
            for bucket in data.get("bucket", []):
                bucket_start = int(bucket["startTimeMillis"]) / 1000
                bucket_date = datetime.datetime.fromtimestamp(bucket_start).date().isoformat()
                for dataset in bucket.get("dataset", []):
                    for point in dataset.get("point", []):
                        for val in point.get("value", []):
                            step_count = val.get("intVal", 0)
                            if step_count > 0:
                                steps.append({
                                    "date": bucket_date,
                                    "step_count": step_count,
                                })

            return SyncResult(steps=steps)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return SyncResult(error="Token expired — needs refresh")
            logger.error("Google Health API error: %s %s", e.response.status_code, e.response.text)
            return SyncResult(error=f"Google Health API error: {e.response.status_code}")
        except Exception as e:
            logger.error("Google Health API fetch error: %s", e)
            return SyncResult(error=f"Google Health API fetch error: {e}")

"""Provider sync stubs — placeholder OAuth clients for Garmin, Strava, Google Health.

Real implementation requires developer API keys and OAuth flows.
These stubs define the interface for future implementation.
"""


class SyncResult:
    """Result of a provider sync operation."""

    def __init__(self, steps: list[dict] | None = None, error: str | None = None):
        self.steps = steps or []
        self.error = error
        self.success = error is None


def sync_garmin(token: str) -> SyncResult:
    """Sync steps from Garmin Connect. STUB — returns empty result."""
    # TODO: Implement Garmin Connect API integration
    # Requires: GARMIN_CLIENT_ID, GARMIN_CLIENT_SECRET env vars
    # Docs: https://developer.garmin.com/gc-developer-program/
    return SyncResult(error="Garmin sync not yet implemented — enter steps manually")


def sync_strava(token: str) -> SyncResult:
    """Sync steps from Strava. STUB — returns empty result."""
    # TODO: Implement Strava API v3 integration
    # Requires: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET env vars
    # Docs: https://developers.strava.com/
    return SyncResult(error="Strava sync not yet implemented — enter steps manually")


def sync_google_health(token: str) -> SyncResult:
    """Sync steps from Google Health API. STUB — returns empty result.

    For the full implementation, see app/services/google_health.py which
    handles the complete OAuth flow and step data retrieval.
    """
    # See app/services/google_health.py for the real implementation
    # Requires: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET env vars
    # Docs: https://developers.google.com/health/about
    return SyncResult(error="Google Health sync not yet implemented via this stub — use /google-health/sync endpoint")

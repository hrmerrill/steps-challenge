"""Provider sync stubs — placeholder OAuth clients for Garmin, Strava, Fitbit.

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


def sync_fitbit(token: str) -> SyncResult:
    """Sync steps from Fitbit. STUB — returns empty result."""
    # TODO: Implement Fitbit Web API integration
    # Requires: FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET env vars
    # Docs: https://dev.fitbit.com/build/reference/web-api/
    return SyncResult(error="Fitbit sync not yet implemented — enter steps manually")

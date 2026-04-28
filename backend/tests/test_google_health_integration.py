"""Integration test for Google Health API request format.

Validates that our dailyRollUp request body matches the Google Health API
schema by making a real HTTP request (with a dummy token).

The API will reject the token (401) but will return 400 if the request
body itself is malformed — letting us distinguish format errors from auth errors.

Run: pytest tests/test_google_health_integration.py -v -s
"""

import datetime
import json

import httpx
import pytest

from app.services.google_health import GOOGLE_HEALTH_API_BASE


def _build_daily_rollup_body(
    start: datetime.date, end: datetime.date
) -> dict:
    """Build the exact request body our sync code would send."""
    exclusive_end = end + datetime.timedelta(days=1)
    return {
        "range": {
            "start": {
                "date": {
                    "year": start.year,
                    "month": start.month,
                    "day": start.day,
                },
                "time": {
                    "hours": 0,
                    "minutes": 0,
                    "seconds": 0,
                    "nanos": 0,
                },
            },
            "end": {
                "date": {
                    "year": exclusive_end.year,
                    "month": exclusive_end.month,
                    "day": exclusive_end.day,
                },
                "time": {
                    "hours": 0,
                    "minutes": 0,
                    "seconds": 0,
                    "nanos": 0,
                },
            },
        },
        "windowSizeDays": 1,
    }


class TestGoogleHealthRequestFormat:
    """Validate request format by sending to the real API with a dummy token.

    A 401 response means the format is correct (auth rejected, not body).
    A 400 response means the request body is malformed.
    """

    @pytest.mark.integration
    def test_dailyrollup_request_format_is_accepted(self):
        """Send our request body to Google Health API — expect 401 (not 400).

        401 = request format OK, bad token
        400 = request body malformed
        """
        url = f"{GOOGLE_HEALTH_API_BASE}/users/me/dataTypes/steps/dataPoints:dailyRollUp"
        body = _build_daily_rollup_body(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 4, 7),
        )

        print(f"\n--- Request ---")
        print(f"POST {url}")
        print(f"Body: {json.dumps(body, indent=2)}")

        response = httpx.post(
            url,
            headers={
                "Authorization": "Bearer DUMMY_TOKEN_FOR_FORMAT_VALIDATION",
                "Content-Type": "application/json",
            },
            json=body,
        )

        print(f"\n--- Response ---")
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")

        # 401 means the request format was accepted but auth failed — that's good!
        # 400 means the request body itself was rejected — that's the bug.
        assert response.status_code == 401, (
            f"Expected 401 (bad token, valid format) but got {response.status_code}. "
            f"Response: {response.text}"
        )

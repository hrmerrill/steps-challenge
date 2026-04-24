"""Tests for Google Health API integration — OAuth flow, step sync, and dedup logic."""

import datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.models.steps import DailySteps, StepSource
from app.models.user import User
from app.services.auth import hash_password, create_access_token


# ── Helpers ──


def _create_user(db, email="googlehealth@test.com", display_name="Google Health Tester"):
    """Create a test user and return (user, token)."""
    user = User(email=email, password_hash=hash_password("Test1234!"), display_name=display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return user, token


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _add_steps(db, user_id, date_str, step_count, source=StepSource.MANUAL):
    """Insert a DailySteps row."""
    entry = DailySteps(
        user_id=user_id,
        date=datetime.date.fromisoformat(date_str),
        step_count=step_count,
        source=source,
    )
    db.add(entry)
    db.commit()
    return entry


# ── Google Health API response parsing tests ──


class TestFetchDailyStepsResponseParsing:
    """Test that fetch_daily_steps correctly calls the Google Health API
    dailyRollUp endpoint and parses its response format."""

    @pytest.mark.asyncio
    async def test_parses_daily_rollup_response(self):
        """Correctly parses the Google Health API dailyRollUp response."""
        from app.services.google_health import fetch_daily_steps

        mock_response = httpx.Response(
            200,
            json={
                "rollupDataPoints": [
                    {
                        "civilStartTime": {"year": 2026, "month": 4, "day": 10, "hours": 0, "minutes": 0, "seconds": 0},
                        "civilEndTime": {"year": 2026, "month": 4, "day": 11, "hours": 0, "minutes": 0, "seconds": 0},
                        "steps": {"countSum": "8500"},
                    },
                    {
                        "civilStartTime": {"year": 2026, "month": 4, "day": 11, "hours": 0, "minutes": 0, "seconds": 0},
                        "civilEndTime": {"year": 2026, "month": 4, "day": 12, "hours": 0, "minutes": 0, "seconds": 0},
                        "steps": {"countSum": "12000"},
                    },
                ]
            },
            request=httpx.Request("POST", "https://health.googleapis.com/v4/users/me/dataTypes/steps/dataPoints:dailyRollUp"),
        )

        with patch("app.services.google_health.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await fetch_daily_steps(
                "fake-token",
                datetime.date(2026, 4, 10),
                datetime.date(2026, 4, 12),
            )

        assert result.success
        assert len(result.steps) == 2
        assert result.steps[0] == {"date": "2026-04-10", "step_count": 8500}
        assert result.steps[1] == {"date": "2026-04-11", "step_count": 12000}

        # Verify the request was made to the correct URL
        call_args = mock_client.post.call_args
        assert "health.googleapis.com" in call_args.args[0]
        assert "dailyRollUp" in call_args.args[0]

        # Verify timeZone is included in CivilDateTime objects
        request_body = call_args.kwargs["json"]
        assert "timeZone" in request_body["range"]["start"]
        assert "timeZone" in request_body["range"]["end"]

        # Verify correct CivilDateTime field names (plural: hours, minutes, seconds)
        for endpoint in ("start", "end"):
            dt = request_body["range"][endpoint]
            assert "hours" in dt, f"Expected 'hours' (plural) in {endpoint}, got {list(dt.keys())}"
            assert "minutes" in dt
            assert "seconds" in dt
            assert "hour" not in dt, "Should use 'hours' (plural), not 'hour'"

    @pytest.mark.asyncio
    async def test_skips_zero_step_days(self):
        """Days with zero steps are excluded from results."""
        from app.services.google_health import fetch_daily_steps

        mock_response = httpx.Response(
            200,
            json={
                "rollupDataPoints": [
                    {
                        "civilStartTime": {"year": 2026, "month": 4, "day": 10},
                        "civilEndTime": {"year": 2026, "month": 4, "day": 11},
                        "steps": {"countSum": "0"},
                    },
                    {
                        "civilStartTime": {"year": 2026, "month": 4, "day": 11},
                        "civilEndTime": {"year": 2026, "month": 4, "day": 12},
                        "steps": {"countSum": "5000"},
                    },
                ]
            },
            request=httpx.Request("POST", "https://health.googleapis.com/v4/test"),
        )

        with patch("app.services.google_health.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await fetch_daily_steps("fake-token", datetime.date(2026, 4, 10), datetime.date(2026, 4, 12))

        assert result.success
        assert len(result.steps) == 1
        assert result.steps[0]["step_count"] == 5000

    @pytest.mark.asyncio
    async def test_rejects_range_over_90_days(self):
        """Ranges over 90 days are rejected."""
        from app.services.google_health import fetch_daily_steps

        result = await fetch_daily_steps(
            "fake-token",
            datetime.date(2026, 1, 1),
            datetime.date(2026, 5, 1),
        )
        assert not result.success
        assert "90 days" in result.error


# ── Data model tests ──


class TestMultiSourceConstraint:
    """Test that the new (user_id, date, source) constraint works."""

    def test_allows_same_date_different_sources(self, db_session):
        """A user can have both manual and Google Health entries for the same date."""
        user, _ = _create_user(db_session)
        _add_steps(db_session, user.id, "2026-04-10", 5000, StepSource.MANUAL)
        _add_steps(db_session, user.id, "2026-04-10", 8000, StepSource.GOOGLE_HEALTH)

        entries = db_session.query(DailySteps).filter(
            DailySteps.user_id == user.id,
            DailySteps.date == datetime.date(2026, 4, 10),
        ).all()
        assert len(entries) == 2
        sources = {e.source for e in entries}
        assert sources == {StepSource.MANUAL, StepSource.GOOGLE_HEALTH}

    def test_rejects_duplicate_source_same_date(self, db_session):
        """Two entries with the same (user, date, source) should conflict."""
        from sqlalchemy.exc import IntegrityError

        user, _ = _create_user(db_session)
        _add_steps(db_session, user.id, "2026-04-10", 5000, StepSource.MANUAL)

        with pytest.raises(IntegrityError):
            _add_steps(db_session, user.id, "2026-04-10", 6000, StepSource.MANUAL)


# ── Anti-double-counting (dedup) tests ──


class TestDedupLogic:
    """Test that leaderboard/stats don't double-count when both manual and
    Google Health entries exist for the same user/date."""

    def test_prefers_preferred_source(self, client, db_session):
        """When user has preferred_step_source=google_health, Google Health entry should
        be used for stats, not the manual one."""
        user, token = _create_user(db_session)
        user.preferred_step_source = StepSource.GOOGLE_HEALTH
        db_session.commit()

        _add_steps(db_session, user.id, "2026-04-10", 3000, StepSource.MANUAL)
        _add_steps(db_session, user.id, "2026-04-10", 9000, StepSource.GOOGLE_HEALTH)

        resp = client.get("/steps/summary", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_steps"] == 9000
        assert data["days_logged"] == 1

    def test_falls_back_to_other_source(self, client, db_session):
        """When preferred source has no data for a date, falls back to
        whatever source does have data."""
        user, token = _create_user(db_session)
        user.preferred_step_source = StepSource.GOOGLE_HEALTH
        db_session.commit()

        # Only manual entry for this date — no Google Health data
        _add_steps(db_session, user.id, "2026-04-10", 7000, StepSource.MANUAL)

        resp = client.get("/steps/summary", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["total_steps"] == 7000

    def test_no_double_counting_leaderboard(self, client, db_session):
        """Overall leaderboard should not double-count steps."""
        user, token = _create_user(db_session)
        user.preferred_step_source = StepSource.GOOGLE_HEALTH
        db_session.commit()

        _add_steps(db_session, user.id, "2026-04-10", 3000, StepSource.MANUAL)
        _add_steps(db_session, user.id, "2026-04-10", 9000, StepSource.GOOGLE_HEALTH)

        resp = client.get("/leaderboard/overall")
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) == 1
        assert entries[0]["total_steps"] == 9000

    def test_manual_user_unaffected(self, client, db_session):
        """A user with preferred_step_source=manual sees normal behavior."""
        user, token = _create_user(db_session)
        # preferred_step_source defaults to MANUAL

        _add_steps(db_session, user.id, "2026-04-10", 5000, StepSource.MANUAL)

        resp = client.get("/steps/summary", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["total_steps"] == 5000


# ── Source-aware upsert tests ──


class TestSourceAwareUpsert:
    """Test that step POST upserts by (user_id, date, source)."""

    def test_upsert_same_source(self, client, db_session):
        """Posting manual entry for same date updates the existing one."""
        user, token = _create_user(db_session)
        headers = _auth_header(token)

        resp1 = client.post("/steps/", json={"date": "2026-04-10", "step_count": 5000}, headers=headers)
        assert resp1.status_code == 201

        resp2 = client.post("/steps/", json={"date": "2026-04-10", "step_count": 8000}, headers=headers)
        assert resp2.status_code == 201

        entries = db_session.query(DailySteps).filter(DailySteps.user_id == user.id).all()
        assert len(entries) == 1
        assert entries[0].step_count == 8000

    def test_different_sources_coexist(self, client, db_session):
        """Manual and Google Health entries for the same date both exist."""
        user, token = _create_user(db_session)
        headers = _auth_header(token)

        client.post("/steps/", json={"date": "2026-04-10", "step_count": 5000, "source": "manual"}, headers=headers)
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 9000, "source": "google_health"}, headers=headers)

        entries = db_session.query(DailySteps).filter(DailySteps.user_id == user.id).all()
        assert len(entries) == 2

    def test_delete_rejects_non_manual(self, client, db_session):
        """Cannot delete synced (non-manual) entries."""
        user, token = _create_user(db_session)
        entry = _add_steps(db_session, user.id, "2026-04-10", 9000, StepSource.GOOGLE_HEALTH)

        resp = client.delete(f"/steps/{entry.id}", headers=_auth_header(token))
        assert resp.status_code == 403
        assert "synced" in resp.json()["detail"].lower()

    def test_delete_allows_manual(self, client, db_session):
        """Can delete manual entries."""
        user, token = _create_user(db_session)
        entry = _add_steps(db_session, user.id, "2026-04-10", 5000, StepSource.MANUAL)

        resp = client.delete(f"/steps/{entry.id}", headers=_auth_header(token))
        assert resp.status_code == 204


# ── Google Health router tests ──


class TestGoogleHealthRouter:
    """Test Google Health OAuth endpoints with mocked external calls."""

    def test_status_unconfigured(self, client, db_session):
        """When Google Health is not configured, status reports configured=false."""
        user, token = _create_user(db_session)
        resp = client.get("/google-health/status", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is False
        assert data["connected"] is False

    def test_connect_unconfigured_returns_501(self, client, db_session):
        """Connect fails gracefully when Google Health creds aren't set."""
        user, token = _create_user(db_session)
        resp = client.get("/google-health/connect", headers=_auth_header(token))
        assert resp.status_code == 501

    @patch("app.routers.google_health.is_google_health_configured", return_value=True)
    @patch("app.routers.google_health.get_authorization_url", return_value="https://accounts.google.com/o/oauth2/v2/auth?client_id=test&state=jwt123")
    def test_connect_returns_auth_url(self, mock_url, mock_configured, client, db_session):
        """When configured, returns the OAuth authorization URL with state."""
        user, token = _create_user(db_session)
        resp = client.get("/google-health/connect", headers=_auth_header(token))
        assert resp.status_code == 200
        assert "authorization_url" in resp.json()
        assert "accounts.google.com" in resp.json()["authorization_url"]
        # Verify get_authorization_url was called with a state token
        mock_url.assert_called_once()
        call_kwargs = mock_url.call_args
        assert call_kwargs.kwargs.get("state") or call_kwargs.args

    @patch("app.routers.google_health.is_google_health_configured", return_value=True)
    def test_connect_already_connected(self, mock_configured, client, db_session):
        """If already connected, returns 409."""
        user, token = _create_user(db_session)
        user.google_health_token = "existing-token"
        db_session.commit()

        resp = client.get("/google-health/connect", headers=_auth_header(token))
        assert resp.status_code == 409

    @patch("app.routers.google_health.is_google_health_configured", return_value=True)
    @patch("app.routers.google_health.exchange_code_for_tokens")
    def test_callback_stores_tokens(self, mock_exchange, mock_configured, client, db_session):
        """OAuth callback stores tokens, sets preferred source, and redirects to profile."""
        from app.services.google_health import TokenResult
        mock_exchange.return_value = TokenResult(access_token="access123", refresh_token="refresh456")

        user, token = _create_user(db_session)
        resp = client.get(
            f"/google-health/callback?code=authcode123&state={token}",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/#/profile" in resp.headers["location"]
        assert "google_health=connected" in resp.headers["location"]

        db_session.refresh(user)
        assert user.google_health_token == "access123"
        assert user.google_health_refresh_token == "refresh456"
        assert user.preferred_step_source == StepSource.GOOGLE_HEALTH

    @patch("app.routers.google_health.fetch_daily_steps")
    def test_sync_creates_steps(self, mock_fetch, client, db_session):
        """Sync pulls Google Health steps and creates DailySteps entries."""
        from app.services.google_health import SyncResult
        mock_fetch.return_value = SyncResult(steps=[
            {"date": "2026-04-10", "step_count": 8500},
            {"date": "2026-04-11", "step_count": 12000},
        ])

        user, token = _create_user(db_session)
        user.google_health_token = "access123"
        user.google_health_refresh_token = "refresh456"
        db_session.commit()

        resp = client.post("/google-health/sync?days=7", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["days_synced"] == 2

        entries = db_session.query(DailySteps).filter(
            DailySteps.user_id == user.id,
            DailySteps.source == StepSource.GOOGLE_HEALTH,
        ).all()
        assert len(entries) == 2
        assert {e.step_count for e in entries} == {8500, 12000}

    def test_sync_not_connected(self, client, db_session):
        """Sync fails if Google Health not connected."""
        user, token = _create_user(db_session)
        resp = client.post("/google-health/sync", headers=_auth_header(token))
        assert resp.status_code == 400

    def test_status_empty_token_shows_not_connected(self, client, db_session):
        """Status reports connected=false when token is an empty string."""
        user, token = _create_user(db_session)
        user.google_health_token = ""
        db_session.commit()

        resp = client.get("/google-health/status", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["connected"] is False

    def test_disconnect(self, client, db_session):
        """Disconnect clears tokens and reverts preferred source."""
        user, token = _create_user(db_session)
        user.google_health_token = "access123"
        user.google_health_refresh_token = "refresh456"
        user.preferred_step_source = StepSource.GOOGLE_HEALTH
        db_session.commit()

        resp = client.post("/google-health/disconnect", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["disconnected"] is True

        db_session.refresh(user)
        assert user.google_health_token is None
        assert user.google_health_refresh_token is None
        assert user.preferred_step_source == StepSource.MANUAL

    def test_disconnect_not_connected(self, client, db_session):
        """Disconnect fails if not connected."""
        user, token = _create_user(db_session)
        resp = client.post("/google-health/disconnect", headers=_auth_header(token))
        assert resp.status_code == 400

    @patch("app.routers.google_health.fetch_daily_steps")
    def test_sync_upserts_existing_google_health_entries(self, mock_fetch, client, db_session):
        """Syncing again updates existing Google Health entries, doesn't duplicate."""
        from app.services.google_health import SyncResult
        mock_fetch.return_value = SyncResult(steps=[
            {"date": "2026-04-10", "step_count": 9500},
        ])

        user, token = _create_user(db_session)
        user.google_health_token = "access123"
        db_session.commit()

        # Pre-existing Google Health entry
        _add_steps(db_session, user.id, "2026-04-10", 8000, StepSource.GOOGLE_HEALTH)

        resp = client.post("/google-health/sync?days=7", headers=_auth_header(token))
        assert resp.status_code == 200

        entries = db_session.query(DailySteps).filter(
            DailySteps.user_id == user.id,
            DailySteps.date == datetime.date(2026, 4, 10),
            DailySteps.source == StepSource.GOOGLE_HEALTH,
        ).all()
        assert len(entries) == 1
        assert entries[0].step_count == 9500

    @patch("app.routers.google_health.fetch_daily_steps")
    def test_sync_preserves_manual_entries(self, mock_fetch, client, db_session):
        """Syncing Google Health data doesn't overwrite existing manual entries."""
        from app.services.google_health import SyncResult
        mock_fetch.return_value = SyncResult(steps=[
            {"date": "2026-04-10", "step_count": 9500},
        ])

        user, token = _create_user(db_session)
        user.google_health_token = "access123"
        db_session.commit()

        # Pre-existing manual entry
        _add_steps(db_session, user.id, "2026-04-10", 5000, StepSource.MANUAL)

        resp = client.post("/google-health/sync?days=7", headers=_auth_header(token))
        assert resp.status_code == 200

        # Both entries should coexist
        entries = db_session.query(DailySteps).filter(
            DailySteps.user_id == user.id,
            DailySteps.date == datetime.date(2026, 4, 10),
        ).all()
        assert len(entries) == 2
        sources = {e.source: e.step_count for e in entries}
        assert sources[StepSource.MANUAL] == 5000
        assert sources[StepSource.GOOGLE_HEALTH] == 9500


    @patch("app.routers.google_health.fetch_daily_steps")
    def test_sync_propagates_403(self, mock_fetch, client, db_session):
        """When Google returns 403, the sync endpoint returns 403 (not 502)."""
        from app.services.google_health import SyncResult
        mock_fetch.return_value = SyncResult(
            error="Google Health API error: 403 Forbidden. "
                  "Ensure the Fitness API is enabled in your Google Cloud Console "
                  "and the required scopes were granted during authorization.",
            status_code=403,
        )

        user, token = _create_user(db_session, email="err403@test.com")
        user.google_health_token = "access123"
        db_session.commit()

        resp = client.post("/google-health/sync?days=7", headers=_auth_header(token))
        assert resp.status_code == 403
        assert "Fitness API" in resp.json()["detail"]

    @patch("app.routers.google_health.fetch_daily_steps")
    def test_sync_generic_upstream_error_preserves_status(self, mock_fetch, client, db_session):
        """Non-403/401 upstream errors propagate the original status code."""
        from app.services.google_health import SyncResult
        mock_fetch.return_value = SyncResult(
            error="Google Health API error: 429",
            status_code=429,
        )

        user, token = _create_user(db_session, email="err429@test.com")
        user.google_health_token = "access123"
        db_session.commit()

        resp = client.post("/google-health/sync?days=7", headers=_auth_header(token))
        assert resp.status_code == 429


# ── Preferred step source in user response tests ──


class TestPreferredStepSourceResponse:
    """Test that preferred_step_source is included in user profile responses."""

    def test_default_is_manual(self, client, db_session):
        """New users default to manual preferred source."""
        user, token = _create_user(db_session)
        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["preferred_step_source"] == "manual"

    def test_reflects_google_health_after_connect(self, client, db_session):
        """After connecting Google Health, preferred source is reflected in profile."""
        user, token = _create_user(db_session)
        user.preferred_step_source = StepSource.GOOGLE_HEALTH
        user.google_health_token = "tok"
        db_session.commit()

        resp = client.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["preferred_step_source"] == "google_health"
        assert data["google_health_connected"] is True

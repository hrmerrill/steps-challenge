"""Tests for auth endpoints — register, login, /me."""

import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "Secure@pass1",
            "display_name": "New User",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "Secure@pass1", "display_name": "D"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_register_short_password(self, client):
        resp = client.post("/auth/register", json={
            "email": "short@example.com",
            "password": "short",
            "display_name": "S",
        })
        assert resp.status_code == 422

    def test_register_password_missing_uppercase(self, client):
        resp = client.post("/auth/register", json={
            "email": "weak@example.com",
            "password": "nouppercase1!",
            "display_name": "W",
        })
        assert resp.status_code == 422

    def test_register_password_missing_digit(self, client):
        resp = client.post("/auth/register", json={
            "email": "weak@example.com",
            "password": "NoDigitHere!",
            "display_name": "W",
        })
        assert resp.status_code == 422

    def test_register_password_missing_special(self, client):
        resp = client.post("/auth/register", json={
            "email": "weak@example.com",
            "password": "NoSpecial123",
            "display_name": "W",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "Secure@pass1",
            "display_name": "Bad",
        })
        assert resp.status_code == 422


class TestLogin:
    def _register(self, client):
        client.post("/auth/register", json={
            "email": "login@example.com",
            "password": "Secure@pass1",
            "display_name": "Login User",
        })

    def test_login_success(self, client):
        self._register(client)
        resp = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "Secure@pass1",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        self._register(client)
        resp = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "whatever123",
        })
        assert resp.status_code == 401


class TestMe:
    def _get_token(self, client) -> str:
        resp = client.post("/auth/register", json={
            "email": "me@example.com",
            "password": "Secure@pass1",
            "display_name": "Me User",
        })
        return resp.json()["access_token"]

    def test_me_authenticated(self, client):
        token = self._get_token(client)
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "me@example.com"
        assert body["display_name"] == "Me User"
        assert body["garmin_connected"] is False

    def test_me_no_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code in (401, 403)

    def test_me_invalid_token(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert resp.status_code == 401


class TestTokenExpiry:
    def test_default_jwt_expiry_is_30_days(self):
        from app.config import settings
        assert settings.jwt_expire_minutes == 60 * 24 * 30

    def test_expired_token_returns_401(self, client):
        """A token issued with an already-past expiry must be rejected."""
        from datetime import datetime, timedelta, timezone
        from jose import jwt as jose_jwt
        from app.config import settings

        expired_payload = {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=10),
        }
        expired_token = jose_jwt.encode(
            expired_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm,
        )
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401

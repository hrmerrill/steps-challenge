"""Tests for auth endpoints — register, login, /me, password reset."""

import pytest
from datetime import datetime, timedelta, timezone


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


class TestForgotPassword:
    def _register(self, client):
        client.post("/auth/register", json={
            "email": "reset@example.com",
            "password": "Secure@pass1",
            "display_name": "Reset User",
        })

    def test_forgot_password_existing_email(self, client):
        self._register(client)
        resp = client.post("/auth/forgot-password", json={"email": "reset@example.com"})
        assert resp.status_code == 200
        assert "password reset link" in resp.json()["message"].lower()

    def test_forgot_password_nonexistent_email(self, client):
        """Should return 200 even for unknown emails (enumeration protection)."""
        resp = client.post("/auth/forgot-password", json={"email": "unknown@example.com"})
        assert resp.status_code == 200
        assert "password reset link" in resp.json()["message"].lower()

    def test_forgot_password_missing_email(self, client):
        resp = client.post("/auth/forgot-password", json={})
        assert resp.status_code == 422

    def test_forgot_password_invalid_email(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "not-an-email"})
        assert resp.status_code == 422


class TestResetPassword:
    def _register_and_get_token(self, client, db_session):
        """Register a user and create a reset token directly."""
        client.post("/auth/register", json={
            "email": "resetpw@example.com",
            "password": "Secure@pass1",
            "display_name": "Reset PW User",
        })
        from app.models.user import User
        from app.services.auth import create_password_reset_token

        user = db_session.query(User).filter(User.email == "resetpw@example.com").first()
        token = create_password_reset_token(db_session, user.id)
        return token

    def test_reset_password_success(self, client, db_session):
        token = self._register_and_get_token(client, db_session)
        resp = client.post("/auth/reset-password", json={
            "token": token,
            "new_password": "NewSecure@pass2",
        })
        assert resp.status_code == 200
        assert "successfully" in resp.json()["message"].lower()

        # Verify new password works
        resp = client.post("/auth/login", json={
            "email": "resetpw@example.com",
            "password": "NewSecure@pass2",
        })
        assert resp.status_code == 200

    def test_reset_password_old_password_no_longer_works(self, client, db_session):
        token = self._register_and_get_token(client, db_session)
        client.post("/auth/reset-password", json={
            "token": token,
            "new_password": "NewSecure@pass2",
        })
        resp = client.post("/auth/login", json={
            "email": "resetpw@example.com",
            "password": "Secure@pass1",
        })
        assert resp.status_code == 401

    def test_reset_password_invalid_token(self, client):
        resp = client.post("/auth/reset-password", json={
            "token": "invalid-token-value",
            "new_password": "NewSecure@pass2",
        })
        assert resp.status_code == 400
        assert "invalid" in resp.json()["detail"].lower()

    def test_reset_password_used_token(self, client, db_session):
        token = self._register_and_get_token(client, db_session)
        # Use it once
        resp = client.post("/auth/reset-password", json={
            "token": token,
            "new_password": "NewSecure@pass2",
        })
        assert resp.status_code == 200

        # Try to use it again
        resp = client.post("/auth/reset-password", json={
            "token": token,
            "new_password": "AnotherSecure@pass3",
        })
        assert resp.status_code == 400

    def test_reset_password_expired_token(self, client, db_session):
        """A token with an already-past expiry must be rejected."""
        client.post("/auth/register", json={
            "email": "expired@example.com",
            "password": "Secure@pass1",
            "display_name": "Expired User",
        })
        from app.models.user import User
        from app.models.password_reset_token import PasswordResetToken
        import secrets

        user = db_session.query(User).filter(User.email == "expired@example.com").first()
        expired_token = PasswordResetToken(
            user_id=user.id,
            token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(expired_token)
        db_session.commit()

        resp = client.post("/auth/reset-password", json={
            "token": expired_token.token,
            "new_password": "NewSecure@pass2",
        })
        assert resp.status_code == 400

    def test_reset_password_weak_password(self, client, db_session):
        token = self._register_and_get_token(client, db_session)
        resp = client.post("/auth/reset-password", json={
            "token": token,
            "new_password": "weak",
        })
        assert resp.status_code == 422

    def test_reset_password_missing_uppercase(self, client, db_session):
        token = self._register_and_get_token(client, db_session)
        resp = client.post("/auth/reset-password", json={
            "token": token,
            "new_password": "nouppercase1!",
        })
        assert resp.status_code == 422

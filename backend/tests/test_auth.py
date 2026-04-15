"""Tests for auth endpoints — register, login, /me."""

import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "securepass123",
            "display_name": "New User",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "securepass123", "display_name": "D"}
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

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "securepass123",
            "display_name": "Bad",
        })
        assert resp.status_code == 422


class TestLogin:
    def _register(self, client):
        client.post("/auth/register", json={
            "email": "login@example.com",
            "password": "securepass123",
            "display_name": "Login User",
        })

    def test_login_success(self, client):
        self._register(client)
        resp = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "securepass123",
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
            "password": "securepass123",
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

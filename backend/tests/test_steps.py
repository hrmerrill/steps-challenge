"""Tests for steps endpoints — CRUD, summary."""

import datetime


class TestLogSteps:
    def _auth_header(self, client) -> dict:
        resp = client.post("/auth/register", json={
            "email": "steps@test.com", "password": "Secure@pass1", "display_name": "Stepper",
        })
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def test_log_steps_success(self, client):
        h = self._auth_header(client)
        resp = client.post("/steps/", json={
            "date": "2026-04-15", "step_count": 10000,
        }, headers=h)
        assert resp.status_code == 201
        body = resp.json()
        assert body["step_count"] == 10000
        assert body["source"] == "manual"

    def test_log_steps_updates_existing(self, client):
        h = self._auth_header(client)
        client.post("/steps/", json={"date": "2026-04-15", "step_count": 5000}, headers=h)
        resp = client.post("/steps/", json={"date": "2026-04-15", "step_count": 8000}, headers=h)
        assert resp.status_code == 201
        assert resp.json()["step_count"] == 8000

    def test_log_steps_invalid_count(self, client):
        h = self._auth_header(client)
        resp = client.post("/steps/", json={"date": "2026-04-15", "step_count": 0}, headers=h)
        assert resp.status_code == 422

    def test_get_steps(self, client):
        h = self._auth_header(client)
        client.post("/steps/", json={"date": "2026-04-14", "step_count": 10000}, headers=h)
        client.post("/steps/", json={"date": "2026-04-15", "step_count": 12000}, headers=h)
        resp = client.get("/steps/", headers=h)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_steps_date_filter(self, client):
        h = self._auth_header(client)
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 5000}, headers=h)
        client.post("/steps/", json={"date": "2026-04-15", "step_count": 8000}, headers=h)
        resp = client.get("/steps/?start_date=2026-04-14", headers=h)
        assert len(resp.json()) == 1

    def test_delete_steps(self, client):
        h = self._auth_header(client)
        resp = client.post("/steps/", json={"date": "2026-04-15", "step_count": 5000}, headers=h)
        step_id = resp.json()["id"]
        del_resp = client.delete(f"/steps/{step_id}", headers=h)
        assert del_resp.status_code == 204

    def test_delete_nonexistent(self, client):
        h = self._auth_header(client)
        resp = client.delete("/steps/9999", headers=h)
        assert resp.status_code == 404

    def test_summary(self, client):
        h = self._auth_header(client)
        client.post("/steps/", json={"date": "2026-04-14", "step_count": 10000}, headers=h)
        client.post("/steps/", json={"date": "2026-04-15", "step_count": 12000}, headers=h)
        resp = client.get("/steps/summary", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 22000
        assert body["days_logged"] == 2
        assert body["average_daily"] == 11000.0
        assert body["total_miles"] > 0

    def test_log_future_date_rejected(self, client):
        h = self._auth_header(client)
        resp = client.post("/steps/", json={"date": "2099-01-01", "step_count": 5000}, headers=h)
        assert resp.status_code == 422

    def test_log_ancient_date_rejected(self, client):
        h = self._auth_header(client)
        resp = client.post("/steps/", json={"date": "2020-01-01", "step_count": 5000}, headers=h)
        assert resp.status_code == 422

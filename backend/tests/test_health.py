"""Smoke tests for the health endpoint."""


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "app" in body


def test_health_contains_app_name(client):
    resp = client.get("/health")
    assert resp.json()["app"] == "Steps Challenge"

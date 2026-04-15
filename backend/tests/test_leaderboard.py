"""Tests for leaderboard and challenge endpoints."""

import datetime


def _register_and_get_header(client, email: str, name: str) -> dict:
    resp = client.post("/auth/register", json={
        "email": email, "password": "securepass123", "display_name": name,
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_challenge(client, headers: dict) -> int:
    resp = client.post("/challenges/", json={
        "name": "April 2026", "start_date": "2026-04-01", "end_date": "2026-04-30",
    }, headers=headers)
    return resp.json()["id"]


class TestChallenges:
    def test_create_challenge(self, client):
        h = _register_and_get_header(client, "ch@test.com", "Creator")
        resp = client.post("/challenges/", json={
            "name": "April 2026", "start_date": "2026-04-01", "end_date": "2026-04-30",
        }, headers=h)
        assert resp.status_code == 201
        assert resp.json()["name"] == "April 2026"

    def test_create_invalid_dates(self, client):
        h = _register_and_get_header(client, "bad@test.com", "Bad")
        resp = client.post("/challenges/", json={
            "name": "Bad", "start_date": "2026-04-30", "end_date": "2026-04-01",
        }, headers=h)
        assert resp.status_code == 400

    def test_list_challenges(self, client):
        h = _register_and_get_header(client, "list@test.com", "Lister")
        _create_challenge(client, h)
        resp = client.get("/challenges/")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_join_challenge(self, client):
        h = _register_and_get_header(client, "join@test.com", "Joiner")
        ch_id = _create_challenge(client, h)
        resp = client.post(f"/challenges/{ch_id}/join", headers=h)
        assert resp.status_code == 201
        assert resp.json()["joined"] is True

    def test_join_duplicate(self, client):
        h = _register_and_get_header(client, "dup@test.com", "Dup")
        ch_id = _create_challenge(client, h)
        client.post(f"/challenges/{ch_id}/join", headers=h)
        resp = client.post(f"/challenges/{ch_id}/join", headers=h)
        assert resp.status_code == 400

    def test_join_nonexistent(self, client):
        h = _register_and_get_header(client, "ghost@test.com", "Ghost")
        resp = client.post("/challenges/9999/join", headers=h)
        assert resp.status_code == 404


class TestLeaderboard:
    def test_leaderboard_empty(self, client):
        h = _register_and_get_header(client, "lb@test.com", "LB")
        ch_id = _create_challenge(client, h)
        resp = client.get(f"/leaderboard/{ch_id}")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_leaderboard_with_participants(self, client):
        h1 = _register_and_get_header(client, "alice@test.com", "Alice")
        h2 = _register_and_get_header(client, "bob@test.com", "Bob")
        ch_id = _create_challenge(client, h1)

        client.post(f"/challenges/{ch_id}/join", headers=h1)
        client.post(f"/challenges/{ch_id}/join", headers=h2)

        # Log steps during challenge period
        client.post("/steps/", json={"date": "2026-04-15", "step_count": 15000}, headers=h1)
        client.post("/steps/", json={"date": "2026-04-15", "step_count": 20000}, headers=h2)

        resp = client.get(f"/leaderboard/{ch_id}")
        assert resp.status_code == 200
        board = resp.json()
        assert len(board) == 2
        assert board[0]["display_name"] == "Bob"  # Bob has more steps
        assert board[0]["rank"] == 1
        assert board[1]["rank"] == 2

    def test_leaderboard_nonexistent(self, client):
        resp = client.get("/leaderboard/9999")
        assert resp.status_code == 404


class TestTrailEndpoint:
    def test_trail_progress(self, client):
        h = _register_and_get_header(client, "trail@test.com", "Trail")
        ch_id = _create_challenge(client, h)
        client.post(f"/challenges/{ch_id}/join", headers=h)
        client.post("/steps/", json={"date": "2026-04-15", "step_count": 10000}, headers=h)

        resp = client.get(f"/leaderboard/{ch_id}/trail")
        assert resp.status_code == 200
        body = resp.json()
        assert body["trail_name"] == "Appalachian Trail"
        assert body["total_group_steps"] == 10000
        assert body["progress_percent"] > 0


class TestOverallLeaderboard:
    def test_overall_leaderboard_empty(self, client):
        resp = client.get("/leaderboard/overall")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_overall_leaderboard_ranked(self, client):
        h1 = _register_and_get_header(client, "oa@test.com", "Alice")
        h2 = _register_and_get_header(client, "ob@test.com", "Bob")
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 5000}, headers=h1)
        client.post("/steps/", json={"date": "2026-04-11", "step_count": 3000}, headers=h1)
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 20000}, headers=h2)

        resp = client.get("/leaderboard/overall")
        assert resp.status_code == 200
        board = resp.json()
        assert len(board) == 2
        assert board[0]["display_name"] == "Bob"
        assert board[0]["total_steps"] == 20000
        assert board[0]["rank"] == 1
        assert board[1]["display_name"] == "Alice"
        assert board[1]["total_steps"] == 8000
        assert board[1]["rank"] == 2


class TestOverallTrail:
    def test_overall_trail_progress(self, client):
        h = _register_and_get_header(client, "ot@test.com", "Trekker")
        client.post("/steps/", json={"date": "2026-01-15", "step_count": 10000}, headers=h)
        client.post("/steps/", json={"date": "2026-04-15", "step_count": 10000}, headers=h)

        resp = client.get("/leaderboard/overall/trail")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_group_steps"] == 20000
        assert body["total_group_miles"] == 10.0
        assert body["progress_percent"] > 0

    def test_overall_trail_empty(self, client):
        resp = client.get("/leaderboard/overall/trail")
        assert resp.status_code == 200
        assert resp.json()["total_group_steps"] == 0


class TestOverallMyStats:
    def test_overall_my_stats(self, client):
        h = _register_and_get_header(client, "oms@test.com", "MyStat")
        client.post("/steps/", json={"date": "2026-01-10", "step_count": 5000}, headers=h)
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 15000}, headers=h)

        resp = client.get("/leaderboard/overall/my-stats", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 20000
        assert body["total_miles"] == 10.0
        assert body["days_logged"] == 2
        assert body["average_daily"] == 10000.0
        assert body["rank"] == 1
        assert body["total_users"] >= 1

    def test_overall_my_stats_no_steps(self, client):
        h = _register_and_get_header(client, "omsn@test.com", "NoSteps")
        resp = client.get("/leaderboard/overall/my-stats", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 0
        assert body["days_logged"] == 0
        assert body["rank"] == 1

    def test_overall_my_stats_rank(self, client):
        h1 = _register_and_get_header(client, "omr1@test.com", "Leader")
        h2 = _register_and_get_header(client, "omr2@test.com", "Follower")
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 30000}, headers=h1)
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 5000}, headers=h2)

        resp = client.get("/leaderboard/overall/my-stats", headers=h2)
        assert resp.status_code == 200
        assert resp.json()["rank"] == 2
        assert resp.json()["total_users"] == 2


class TestMembership:
    def test_membership_not_joined(self, client):
        h = _register_and_get_header(client, "notin@test.com", "NotIn")
        ch_id = _create_challenge(client, h)
        resp = client.get(f"/challenges/{ch_id}/membership", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["joined"] is False
        assert body["miles_club_tier"] is None

    def test_membership_joined(self, client):
        h = _register_and_get_header(client, "joined@test.com", "Joined")
        ch_id = _create_challenge(client, h)
        client.post(f"/challenges/{ch_id}/join", headers=h)
        resp = client.get(f"/challenges/{ch_id}/membership", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["joined"] is True
        assert body["miles_club_tier"] is not None

    def test_membership_nonexistent_challenge(self, client):
        h = _register_and_get_header(client, "ghost2@test.com", "Ghost2")
        resp = client.get("/challenges/9999/membership", headers=h)
        assert resp.status_code == 404


class TestMyStats:
    def test_my_stats_with_steps(self, client):
        h = _register_and_get_header(client, "stats@test.com", "Stats")
        ch_id = _create_challenge(client, h)
        client.post(f"/challenges/{ch_id}/join", headers=h)
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 8000}, headers=h)
        client.post("/steps/", json={"date": "2026-04-11", "step_count": 12000}, headers=h)

        resp = client.get(f"/challenges/{ch_id}/my-stats", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 20000
        assert body["days_logged"] == 2
        assert body["average_daily"] == 10000.0
        assert body["rank"] == 1
        assert body["total_participants"] == 1
        assert body["total_miles"] == 10.0

    def test_my_stats_not_participant(self, client):
        h1 = _register_and_get_header(client, "creator2@test.com", "Creator2")
        h2 = _register_and_get_header(client, "outsider@test.com", "Outsider")
        ch_id = _create_challenge(client, h1)
        resp = client.get(f"/challenges/{ch_id}/my-stats", headers=h2)
        assert resp.status_code == 404

    def test_my_stats_no_steps(self, client):
        h = _register_and_get_header(client, "lazy@test.com", "Lazy")
        ch_id = _create_challenge(client, h)
        client.post(f"/challenges/{ch_id}/join", headers=h)
        resp = client.get(f"/challenges/{ch_id}/my-stats", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 0
        assert body["days_logged"] == 0
        assert body["average_daily"] == 0.0
        assert body["rank"] == 1

    def test_my_stats_rank_calculation(self, client):
        h1 = _register_and_get_header(client, "first@test.com", "First")
        h2 = _register_and_get_header(client, "second@test.com", "Second")
        ch_id = _create_challenge(client, h1)
        client.post(f"/challenges/{ch_id}/join", headers=h1)
        client.post(f"/challenges/{ch_id}/join", headers=h2)
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 20000}, headers=h1)
        client.post("/steps/", json={"date": "2026-04-10", "step_count": 5000}, headers=h2)

        resp = client.get(f"/challenges/{ch_id}/my-stats", headers=h2)
        assert resp.status_code == 200
        assert resp.json()["rank"] == 2
        assert resp.json()["total_participants"] == 2

    def test_my_stats_nonexistent_challenge(self, client):
        h = _register_and_get_header(client, "noexist@test.com", "NoExist")
        resp = client.get("/challenges/9999/my-stats", headers=h)
        assert resp.status_code == 404

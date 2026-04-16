"""Tests for leaderboard and challenge endpoints."""

import datetime


def _register_and_get_header(client, email: str, name: str) -> dict:
    resp = client.post("/auth/register", json={
        "email": email, "password": "Secure@pass1", "display_name": name,
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_challenge(client, headers: dict) -> int:
    resp = client.post("/challenges/", json={
        "name": "Carbon Miles Challenge - March", "start_date": "2026-03-01", "end_date": "2026-03-31",
    }, headers=headers)
    return resp.json()["id"]


class TestChallenges:
    def test_create_challenge(self, client):
        h = _register_and_get_header(client, "ch@test.com", "Creator")
        resp = client.post("/challenges/", json={
            "name": "Carbon Miles Challenge - March", "start_date": "2026-03-01", "end_date": "2026-03-31",
        }, headers=h)
        assert resp.status_code == 201
        assert resp.json()["name"] == "Carbon Miles Challenge - March"

    def test_create_challenge_with_description(self, client):
        h = _register_and_get_header(client, "desc@test.com", "DescCreator")
        resp = client.post("/challenges/", json={
            "name": "February Challenge", "start_date": "2026-02-01", "end_date": "2026-02-28",
            "description": "A test challenge with a description.",
        }, headers=h)
        assert resp.status_code == 201
        body = resp.json()
        assert body["description"] == "A test challenge with a description."

    def test_create_invalid_dates(self, client):
        h = _register_and_get_header(client, "bad@test.com", "Bad")
        resp = client.post("/challenges/", json={
            "name": "Bad", "start_date": "2026-03-31", "end_date": "2026-03-01",
        }, headers=h)
        assert resp.status_code == 422

    def test_create_too_long_challenge(self, client):
        h = _register_and_get_header(client, "long@test.com", "Long")
        resp = client.post("/challenges/", json={
            "name": "Too Long", "start_date": "2024-01-01", "end_date": "2026-01-01",
        }, headers=h)
        assert resp.status_code == 422

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
        assert resp.status_code == 409

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
        client.post("/steps/", json={"date": "2026-03-15", "step_count": 15000}, headers=h1)
        client.post("/steps/", json={"date": "2026-03-15", "step_count": 20000}, headers=h2)

        resp = client.get(f"/leaderboard/{ch_id}")
        assert resp.status_code == 200
        board = resp.json()
        assert len(board) == 2
        assert board[0]["display_name"] == "Bob"  # Bob has more steps
        assert board[0]["rank"] == 1
        assert board[1]["rank"] == 2

    def test_leaderboard_tiers_from_prior_month(self, client):
        """Miles club tier on leaderboard is computed from the prior month, not stored at join."""
        h = _register_and_get_header(client, "tiertest@test.com", "TierUser")

        # Log steps in February (prior month for March challenge)
        for day in range(1, 29):
            client.post(
                "/steps/",
                json={"date": f"2026-02-{day:02d}", "step_count": 8_000},
                headers=h,
            )

        ch_id = _create_challenge(client, h)  # March challenge
        client.post(f"/challenges/{ch_id}/join", headers=h)

        resp = client.get(f"/leaderboard/{ch_id}")
        assert resp.status_code == 200
        board = resp.json()
        assert len(board) == 1
        assert board[0]["miles_club_tier"] == "mid"

    def test_leaderboard_nonexistent(self, client):
        resp = client.get("/leaderboard/9999")
        assert resp.status_code == 404


class TestTrailEndpoint:
    def test_trail_progress(self, client):
        h = _register_and_get_header(client, "trail@test.com", "Trail")
        ch_id = _create_challenge(client, h)
        client.post(f"/challenges/{ch_id}/join", headers=h)
        client.post("/steps/", json={"date": "2026-03-15", "step_count": 10000}, headers=h)

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
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 5000}, headers=h1)
        client.post("/steps/", json={"date": "2026-03-11", "step_count": 3000}, headers=h1)
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 20000}, headers=h2)

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
        client.post("/steps/", json={"date": "2026-03-15", "step_count": 10000}, headers=h)

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
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 15000}, headers=h)

        resp = client.get("/leaderboard/overall/my-stats", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 20000
        assert body["total_miles"] == 10.0
        assert body["days_logged"] == 2
        assert body["average_daily"] == 10000.0
        assert body["rank"] == 1
        assert body["total_users"] >= 1
        # miles_club_tier should be present
        assert "miles_club_tier" in body
        assert "miles_club_average_daily" in body

    def test_overall_my_stats_no_steps(self, client):
        h = _register_and_get_header(client, "omsn@test.com", "NoSteps")
        resp = client.get("/leaderboard/overall/my-stats", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 0
        assert body["days_logged"] == 0
        assert body["rank"] == 1
        assert body["miles_club_tier"] == "low"

    def test_overall_my_stats_tier_from_prior_month(self, client):
        """Miles club tier in overall/my-stats reflects prior month avg."""
        h = _register_and_get_header(client, "omst@test.com", "TierStat")
        today = datetime.date.today()
        prior_start = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        # Log 7k steps/day for each day of last month
        day = prior_start
        end = today.replace(day=1) - datetime.timedelta(days=1)
        while day <= end:
            client.post("/steps/", json={"date": day.isoformat(), "step_count": 7_000}, headers=h)
            day += datetime.timedelta(days=1)

        resp = client.get("/leaderboard/overall/my-stats", headers=h)
        assert resp.status_code == 200
        body = resp.json()
        assert body["miles_club_tier"] == "mid"
        assert body["miles_club_average_daily"] == 7_000.0

    def test_overall_my_stats_rank(self, client):
        h1 = _register_and_get_header(client, "omr1@test.com", "Leader")
        h2 = _register_and_get_header(client, "omr2@test.com", "Follower")
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 30000}, headers=h1)
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 5000}, headers=h2)

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

    def test_membership_tier_reflects_prior_month(self, client):
        """Membership tier is dynamically computed from the prior month."""
        h = _register_and_get_header(client, "memtier@test.com", "MemTier")
        # Log 8k/day in February (prior month for March challenge)
        for day in range(1, 29):
            client.post("/steps/", json={"date": f"2026-02-{day:02d}", "step_count": 8_000}, headers=h)

        ch_id = _create_challenge(client, h)
        client.post(f"/challenges/{ch_id}/join", headers=h)
        resp = client.get(f"/challenges/{ch_id}/membership", headers=h)
        assert resp.status_code == 200
        assert resp.json()["miles_club_tier"] == "mid"

    def test_membership_nonexistent_challenge(self, client):
        h = _register_and_get_header(client, "ghost2@test.com", "Ghost2")
        resp = client.get("/challenges/9999/membership", headers=h)
        assert resp.status_code == 404


class TestMyStats:
    def test_my_stats_with_steps(self, client):
        h = _register_and_get_header(client, "stats@test.com", "Stats")
        ch_id = _create_challenge(client, h)
        client.post(f"/challenges/{ch_id}/join", headers=h)
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 8000}, headers=h)
        client.post("/steps/", json={"date": "2026-03-11", "step_count": 12000}, headers=h)

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
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 20000}, headers=h1)
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 5000}, headers=h2)

        resp = client.get(f"/challenges/{ch_id}/my-stats", headers=h2)
        assert resp.status_code == 200
        assert resp.json()["rank"] == 2
        assert resp.json()["total_participants"] == 2

    def test_my_stats_nonexistent_challenge(self, client):
        h = _register_and_get_header(client, "noexist@test.com", "NoExist")
        resp = client.get("/challenges/9999/my-stats", headers=h)
        assert resp.status_code == 404


class TestTeamChallengeStats:
    def test_team_stats_no_auth_required(self, client):
        h = _register_and_get_header(client, "team1@test.com", "Creator")
        ch_id = _create_challenge(client, h)
        resp = client.get(f"/challenges/{ch_id}/team-stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 0
        assert body["total_participants"] == 0
        assert body["total_miles"] == 0.0

    def test_team_stats_with_participants(self, client):
        h1 = _register_and_get_header(client, "team2@test.com", "Alice")
        h2 = _register_and_get_header(client, "team3@test.com", "Bob")
        ch_id = _create_challenge(client, h1)
        client.post(f"/challenges/{ch_id}/join", headers=h1)
        client.post(f"/challenges/{ch_id}/join", headers=h2)
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 8000}, headers=h1)
        client.post("/steps/", json={"date": "2026-03-11", "step_count": 12000}, headers=h1)
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 5000}, headers=h2)

        resp = client.get(f"/challenges/{ch_id}/team-stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 25000
        assert body["total_participants"] == 2
        assert body["total_miles"] == 12.5
        assert body["total_days_logged"] == 3
        assert body["average_daily_per_participant"] > 0

    def test_team_stats_nonexistent(self, client):
        resp = client.get("/challenges/9999/team-stats")
        assert resp.status_code == 404


class TestOverallTeamStats:
    def test_overall_team_stats_empty(self, client):
        resp = client.get("/leaderboard/overall/team-stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 0
        assert body["total_users"] == 0

    def test_overall_team_stats_with_data(self, client):
        h1 = _register_and_get_header(client, "oteam1@test.com", "Alice")
        h2 = _register_and_get_header(client, "oteam2@test.com", "Bob")
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 10000}, headers=h1)
        client.post("/steps/", json={"date": "2026-03-11", "step_count": 5000}, headers=h1)
        client.post("/steps/", json={"date": "2026-03-10", "step_count": 20000}, headers=h2)

        resp = client.get("/leaderboard/overall/team-stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_steps"] == 35000
        assert body["total_miles"] == 17.5
        assert body["total_users"] == 2
        assert body["total_days_logged"] == 3
        assert body["average_daily_per_user"] > 0

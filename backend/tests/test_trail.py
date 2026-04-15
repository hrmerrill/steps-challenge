"""Tests for trail progress calculation."""

from app.services.trail import steps_to_miles, calculate_trail_progress


class TestStepsToMiles:
    def test_basic_conversion(self):
        assert steps_to_miles(2000) == 1.0

    def test_zero_steps(self):
        assert steps_to_miles(0) == 0.0

    def test_large_number(self):
        assert steps_to_miles(1_000_000) == 500.0


class TestTrailProgress:
    def test_default_trail(self):
        result = calculate_trail_progress(4_380_000)  # 2190 miles worth
        assert result["trail_name"] == "Appalachian Trail"
        assert result["total_group_miles"] == 2190.0
        assert result["progress_percent"] == 100.0

    def test_partial_progress(self):
        result = calculate_trail_progress(2_190_000)  # ~1095 miles
        assert result["progress_percent"] == 50.0

    def test_zero_steps(self):
        result = calculate_trail_progress(0)
        assert result["progress_percent"] == 0.0
        assert result["total_group_miles"] == 0.0

    def test_over_100_percent_capped(self):
        result = calculate_trail_progress(10_000_000)
        assert result["progress_percent"] == 100.0

    def test_pacific_crest_trail(self):
        result = calculate_trail_progress(100_000, "pacific_crest")
        assert result["trail_name"] == "Pacific Crest Trail"
        assert result["trail_length_miles"] == 2650.0

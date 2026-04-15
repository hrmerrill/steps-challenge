"""Tests for miles club tier calculation."""

from app.services.miles_clubs import calculate_tier, tier_label
from app.models.challenge import MilesClubTier


class TestCalculateTier:
    def test_high_tier(self):
        assert calculate_tier(10_000) == MilesClubTier.HIGH
        assert calculate_tier(15_000) == MilesClubTier.HIGH

    def test_mid_tier(self):
        assert calculate_tier(5_000) == MilesClubTier.MID
        assert calculate_tier(9_999) == MilesClubTier.MID

    def test_low_tier(self):
        assert calculate_tier(0) == MilesClubTier.LOW
        assert calculate_tier(4_999) == MilesClubTier.LOW


class TestTierLabel:
    def test_high_label(self):
        assert tier_label(MilesClubTier.HIGH) == ">10k steps/day"

    def test_mid_label(self):
        assert tier_label(MilesClubTier.MID) == "5k\u201310k steps/day"

    def test_low_label(self):
        assert tier_label(MilesClubTier.LOW) == "0\u20135k steps/day"

    def test_none_label(self):
        assert tier_label(MilesClubTier.NONE) == ""

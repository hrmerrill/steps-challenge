"""Tests for miles club tier calculation."""

from app.services.miles_clubs import calculate_tier, tier_emoji
from app.models.challenge import MilesClubTier


class TestCalculateTier:
    def test_gold_tier(self):
        assert calculate_tier(300_000) == MilesClubTier.GOLD
        assert calculate_tier(400_000) == MilesClubTier.GOLD

    def test_silver_tier(self):
        assert calculate_tier(200_000) == MilesClubTier.SILVER
        assert calculate_tier(299_999) == MilesClubTier.SILVER

    def test_bronze_tier(self):
        assert calculate_tier(100_000) == MilesClubTier.BRONZE
        assert calculate_tier(199_999) == MilesClubTier.BRONZE

    def test_no_tier(self):
        assert calculate_tier(0) == MilesClubTier.NONE
        assert calculate_tier(99_999) == MilesClubTier.NONE


class TestTierEmoji:
    def test_gold_emoji(self):
        assert tier_emoji(MilesClubTier.GOLD) == "🥇"

    def test_silver_emoji(self):
        assert tier_emoji(MilesClubTier.SILVER) == "🥈"

    def test_bronze_emoji(self):
        assert tier_emoji(MilesClubTier.BRONZE) == "🥉"

    def test_none_emoji(self):
        assert tier_emoji(MilesClubTier.NONE) == ""

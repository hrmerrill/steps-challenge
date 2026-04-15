"""Miles club tier calculation service."""

from app.config import settings
from app.models.challenge import MilesClubTier


def calculate_tier(average_daily_steps: float) -> MilesClubTier:
    """Determine miles club tier from average daily steps in previous month."""
    if average_daily_steps >= settings.miles_club_high:
        return MilesClubTier.HIGH
    if average_daily_steps >= settings.miles_club_mid:
        return MilesClubTier.MID
    return MilesClubTier.LOW


def tier_label(tier: MilesClubTier) -> str:
    """Return display label for a miles club tier."""
    return {
        MilesClubTier.HIGH: ">10k steps/day",
        MilesClubTier.MID: "5k\u201310k steps/day",
        MilesClubTier.LOW: "0\u20135k steps/day",
        MilesClubTier.NONE: "",
    }[tier]

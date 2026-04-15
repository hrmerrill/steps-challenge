"""Miles club tier calculation service."""

from app.config import settings
from app.models.challenge import MilesClubTier


def calculate_tier(total_steps: int) -> MilesClubTier:
    """Determine miles club tier from total steps in previous month."""
    if total_steps >= settings.miles_club_gold:
        return MilesClubTier.GOLD
    if total_steps >= settings.miles_club_silver:
        return MilesClubTier.SILVER
    if total_steps >= settings.miles_club_bronze:
        return MilesClubTier.BRONZE
    return MilesClubTier.NONE


def tier_emoji(tier: MilesClubTier) -> str:
    """Return emoji for a miles club tier."""
    return {
        MilesClubTier.GOLD: "🥇",
        MilesClubTier.SILVER: "🥈",
        MilesClubTier.BRONZE: "🥉",
        MilesClubTier.NONE: "",
    }[tier]

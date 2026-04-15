"""Trail progress calculation service.

Converts total group steps into distance along a virtual trail.
Default trail: Appalachian Trail (~2,190 miles).
"""

from app.config import settings

# Trail definitions: name → total length in miles
TRAILS = {
    "appalachian": {"name": "Appalachian Trail", "length_miles": 2_190.0},
    "pacific_crest": {"name": "Pacific Crest Trail", "length_miles": 2_650.0},
    "continental_divide": {"name": "Continental Divide Trail", "length_miles": 3_100.0},
}

DEFAULT_TRAIL = "appalachian"


def steps_to_miles(steps: int) -> float:
    """Convert step count to miles using configured steps-per-mile."""
    return round(steps / settings.steps_per_mile, 2)


def calculate_trail_progress(
    total_group_steps: int, trail_key: str = DEFAULT_TRAIL
) -> dict:
    """Calculate group progress along the virtual trail."""
    trail = TRAILS.get(trail_key, TRAILS[DEFAULT_TRAIL])
    total_miles = steps_to_miles(total_group_steps)
    progress = min(total_miles / trail["length_miles"] * 100, 100.0)

    return {
        "total_group_steps": total_group_steps,
        "total_group_miles": total_miles,
        "trail_name": trail["name"],
        "trail_length_miles": trail["length_miles"],
        "progress_percent": round(progress, 2),
    }

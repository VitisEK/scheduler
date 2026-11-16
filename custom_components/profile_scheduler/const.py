"""Constants for Profile Scheduler."""

DOMAIN = "profile_scheduler"
PLATFORMS = ("switch", "select", "sensor")
STORAGE_VERSION = 1
PANEL_PATH = "profile-scheduler"
AUTOMATIC = "automatic"
SIGNAL_UPDATED = f"{DOMAIN}_updated"
ACTION_TIMEOUT = 60


def default_document() -> dict:
    """Return an empty, deliberately disabled schedule."""
    return {
        "enabled": False,
        "manual_profile": None,
        "profiles": [
            {"id": "home", "name": "Doma", "weekdays": [], "rows": []},
            {"id": "workweek", "name": "Pracovní týden", "weekdays": list(range(5)), "rows": []},
            {"id": "away_weekend", "name": "Víkend pryč", "weekdays": [5, 6], "rows": []},
            {"id": "holiday", "name": "Dovolená", "weekdays": [], "rows": []},
        ],
    }

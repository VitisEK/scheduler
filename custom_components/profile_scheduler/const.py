"""Constants for Profile Scheduler."""

DOMAIN = "profile_scheduler"
PLATFORMS = ("switch", "select", "sensor")
STORAGE_VERSION = 2
PANEL_PATH = "profile-scheduler"
INACTIVE_OPTION = "Inactive"
SIGNAL_UPDATED = f"{DOMAIN}_updated"
ACTION_TIMEOUT = 60


def default_document() -> dict:
    """Return an empty, deliberately disabled schedule."""
    return {"enabled": False, "topics": []}

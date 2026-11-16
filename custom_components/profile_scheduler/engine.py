"""Pure profile selection and wall-clock scheduling calculations.

Boundaries use the first occurrence of ambiguous local times. Nonexistent local
times advance to the first valid local minute. All interval comparisons happen
in UTC, so moving the clock backwards does not restart an interval.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, tzinfo
from typing import Any

Document = dict[str, Any]
ActiveBlock = tuple[Document, Document, str]


def _aware(now: datetime) -> None:
    """Reject accidental use of a host-local or naive clock."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("An aware datetime is required")


def _minute(value: str) -> int:
    """Parse a previously validated wall-clock boundary."""
    hours, minutes = map(int, value.split(":"))
    if not (0 <= hours <= 24 and 0 <= minutes < 60):
        raise ValueError("Invalid time boundary")
    if hours == 24 and minutes != 0:
        raise ValueError("Only 24:00 is a valid end-of-day boundary")
    return hours * 60 + minutes


def _boundary(day: date, minute: int, zone: tzinfo) -> datetime:
    """Resolve a wall-clock boundary to its earliest valid UTC instant."""
    local = datetime.combine(day, time.min) + timedelta(minutes=minute)
    # A skipped civil date also fits within this bound (for example Apia 2011).
    for _ in range(2 * 24 * 60 + 1):
        candidate = local.replace(tzinfo=zone, fold=0).astimezone(UTC)
        if candidate.astimezone(zone).replace(tzinfo=None) == local:
            return candidate
        local += timedelta(minutes=1)
    raise ValueError("Timezone has no valid boundary within two days")


def select_profile(document: Document, now: datetime) -> Document | None:
    """Select the manual override, or the first profile matching this weekday."""
    _aware(now)
    if not document.get("enabled", True):
        return None
    profiles = document.get("profiles", [])
    manual = document.get("manual_profile")
    if manual is not None:
        return next((profile for profile in profiles if profile["id"] == manual), None)
    return next(
        (profile for profile in profiles if now.weekday() in profile.get("weekdays", [])),
        None,
    )


def active_blocks(profile: Document | None, now: datetime) -> list[ActiveBlock]:
    """Return current blocks and stable occurrence identities.

    Weekdays select the profile for the current date. An overnight block belongs
    to the currently selected profile; switching profiles at midnight supersedes
    the previous profile, including its overnight work.
    """
    _aware(now)
    if profile is None:
        return []
    assert now.tzinfo is not None
    instant = now.astimezone(UTC)
    active: list[ActiveBlock] = []
    boundaries: dict[tuple[date, int], datetime] = {}

    def resolve(day: date, minute: int) -> datetime:
        """Resolve each shared row boundary only once for this evaluation."""
        if minute == 24 * 60:
            day, minute = day + timedelta(days=1), 0
        key = (day, minute)
        if key not in boundaries:
            assert now.tzinfo is not None
            boundaries[key] = _boundary(day, minute, now.tzinfo)
        return boundaries[key]

    for row in profile.get("rows", []):
        for block in row.get("blocks", []):
            start = _minute(block["start"])
            end = _minute(block["end"])
            if start == end:
                continue
            for anchor in (now.date() - timedelta(days=1), now.date()):
                end_day = anchor + timedelta(days=end < start)
                begins = resolve(anchor, start)
                ends = resolve(end_day, end)
                if begins <= instant < ends:
                    occurrence = f"{profile['id']}:{row['id']}:{block['id']}:{anchor.isoformat()}"
                    active.append((row, block, occurrence))
                    break
    return active


def is_block_start(block: Document, now: datetime) -> bool:
    """Whether now is exactly this day's effective block start.

    The effective start of a nonexistent local time is the first valid minute
    following it. A repeated local time only starts a block on its first fold.
    """
    _aware(now)
    assert now.tzinfo is not None
    return now.astimezone(UTC) == _boundary(now.date(), _minute(block["start"]), now.tzinfo)


def next_change(document: Document, now: datetime) -> datetime | None:
    """Return the next UTC boundary, including midnight profile re-evaluation.

    Scheduling midnight even without a matching profile ensures a future weekday
    rule becomes effective. The function never returns now or a past instant.
    """
    _aware(now)
    if not document.get("enabled", True):
        return None
    assert now.tzinfo is not None
    instant = now.astimezone(UTC)
    today = now.date()
    tomorrow = today + timedelta(days=1)
    boundaries = {(tomorrow, 0)}
    # Midnight is always a candidate, so no boundary after it can be the next
    # change. Current-day rules also govern overnight ends anchored yesterday.
    # Both today's normal ends and yesterday's overnight ends fall today.
    current_profile = select_profile(document, now)
    if current_profile is not None:
        for row in current_profile.get("rows", []):
            for block in row.get("blocks", []):
                for value in (block["start"], block["end"]):
                    minute = _minute(value)
                    boundaries.add((tomorrow, 0) if minute == 24 * 60 else (today, minute))
    candidates = {_boundary(day, minute, now.tzinfo) for day, minute in boundaries}
    return min(candidate for candidate in candidates if candidate > instant)

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


def select_profile(topic: Document, now: datetime) -> Document | None:
    """Return the profile explicitly selected for this topic."""
    _aware(now)
    selected = topic.get("active_profile")
    return next((p for p in topic.get("profiles", []) if p["id"] == selected), None)


def schedule_rows(profile: Document, day: date) -> tuple[str, list[Document]]:
    """Find the schedule anchored on a local calendar day."""
    key = "all" if profile["schedule_mode"] == "daily" else str(day.weekday())
    return key, profile["schedules"].get(key, [])


def active_blocks(profile: Document | None, now: datetime) -> list[ActiveBlock]:
    """Return active blocks, including overnight blocks anchored yesterday."""
    _aware(now)
    if profile is None:
        return []
    assert now.tzinfo is not None
    instant = now.astimezone(UTC)
    active: list[ActiveBlock] = []
    boundaries: dict[tuple[date, int], datetime] = {}

    def resolve(day: date, minute: int) -> datetime:
        if minute == 1440:
            day, minute = day + timedelta(days=1), 0
        key = (day, minute)
        if key not in boundaries:
            assert now.tzinfo is not None
            boundaries[key] = _boundary(day, minute, now.tzinfo)
        return boundaries[key]

    for anchor in (now.date() - timedelta(days=1), now.date()):
        day_key, rows = schedule_rows(profile, anchor)
        for row in rows:
            for block in row["blocks"]:
                start, end = _minute(block["start"]), _minute(block["end"])
                if start == end:
                    continue
                begins = resolve(anchor, start)
                ends = resolve(anchor + timedelta(days=end < start), end)
                if begins <= instant < ends:
                    occurrence = f"{day_key}:{row['id']}:{block['id']}:{anchor.isoformat()}"
                    active.append((row, block, occurrence))
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
    """Return the next boundary across all selected topics."""
    _aware(now)
    if not document.get("enabled", True):
        return None
    assert now.tzinfo is not None
    instant = now.astimezone(UTC)
    today = now.date()
    tomorrow = today + timedelta(days=1)
    profiles = [
        profile
        for topic in document.get("topics", [])
        if (profile := select_profile(topic, now)) is not None
    ]
    if not profiles:
        return None
    boundaries = {(tomorrow, 0)}
    for profile in profiles:
        for anchor in (today - timedelta(days=1), today):
            _, rows = schedule_rows(profile, anchor)
            for row in rows:
                for block in row["blocks"]:
                    start, end = _minute(block["start"]), _minute(block["end"])
                    if anchor == today:
                        boundaries.add((today, start))
                    end_day = anchor + timedelta(days=end < start)
                    if end == 1440:
                        end_day, end = end_day + timedelta(days=1), 0
                    if end_day >= today:
                        boundaries.add((end_day, end))
    candidates = {_boundary(day, minute, now.tzinfo) for day, minute in boundaries}
    return min(candidate for candidate in candidates if candidate > instant)

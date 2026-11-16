"""Deterministic pure-engine tests, runnable without Home Assistant installed."""

from __future__ import annotations

import importlib.util
import unittest
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

# Load the pure module without importing the integration's HA-dependent package.
SPEC = importlib.util.spec_from_file_location(
    "profile_scheduler_engine",
    Path(__file__).parents[1] / "custom_components/profile_scheduler/engine.py",
)
assert SPEC is not None and SPEC.loader is not None
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)


def plan(start: str = "08:00", end: str = "10:00") -> dict:
    """Build a minimal structured schedule."""
    return {
        "enabled": True,
        "manual_profile": None,
        "profiles": [
            {
                "id": "home",
                "name": "Home",
                "weekdays": list(range(7)),
                "rows": [
                    {
                        "id": "heat",
                        "name": "Heating",
                        "entity_ids": ["climate.test"],
                        "blocks": [
                            {
                                "id": "morning",
                                "start": start,
                                "end": end,
                                "mode": "state",
                                "label": "21 °C",
                                "color": "#ff9800",
                                "actions": [],
                            }
                        ],
                    }
                ],
            }
        ],
    }


class EngineTests(unittest.TestCase):
    """Exercise boundary behavior using explicit instants."""

    @staticmethod
    def active(document: dict, now: datetime) -> list:
        """Select a profile and its active intervals."""
        return engine.active_blocks(engine.select_profile(document, now), now)

    def test_start_inclusive_end_exclusive(self) -> None:
        document = plan()
        self.assertEqual(len(self.active(document, datetime(2026, 11, 16, 8, tzinfo=UTC))), 1)
        self.assertEqual(self.active(document, datetime(2026, 11, 16, 10, tzinfo=UTC)), [])

    def test_overnight_identity_survives_midnight(self) -> None:
        document = plan("22:00", "06:00")
        before = self.active(document, datetime(2026, 12, 31, 23, 59, tzinfo=UTC))
        after = self.active(document, datetime(2027, 1, 1, 0, tzinfo=UTC))
        self.assertEqual(before[0][2], after[0][2])
        self.assertTrue(after[0][2].endswith("2026-12-31"))
        self.assertEqual(self.active(document, datetime(2027, 1, 1, 6, tzinfo=UTC)), [])

    def test_full_day_starts_new_occurrence_at_midnight(self) -> None:
        document = plan("00:00", "24:00")
        before = self.active(document, datetime(2026, 11, 16, 23, 59, tzinfo=UTC))
        after = self.active(document, datetime(2026, 11, 17, 0, tzinfo=UTC))
        self.assertNotEqual(before[0][2], after[0][2])

    def test_manual_profile_ignores_weekday_and_automatic_uses_order(self) -> None:
        document = plan()
        document["profiles"][0]["weekdays"] = [0]
        away = deepcopy(document["profiles"][0])
        away.update(id="away", name="Away", weekdays=[5, 6])
        document["profiles"].append(away)
        monday = datetime(2026, 11, 16, 9, tzinfo=UTC)
        self.assertEqual(engine.select_profile(document, monday)["id"], "home")
        document["manual_profile"] = "away"
        self.assertEqual(engine.select_profile(document, monday)["id"], "away")
        document["manual_profile"] = None
        self.assertEqual(engine.select_profile(document, monday)["id"], "home")

    def test_automatic_profile_changes_at_midnight(self) -> None:
        document = plan("00:00", "24:00")
        home = document["profiles"][0]
        home["weekdays"] = [0]
        away = deepcopy(home)
        away.update(id="away", weekdays=[1])
        document["profiles"].append(away)
        before = datetime(2026, 11, 16, 23, 59, tzinfo=UTC)
        midnight = engine.next_change(document, before)
        self.assertEqual(midnight, datetime(2026, 11, 17, tzinfo=UTC))
        self.assertEqual(engine.select_profile(document, midnight)["id"], "away")

    def test_manual_profile_change_replaces_active_occurrence(self) -> None:
        document = plan("00:00", "24:00")
        away = deepcopy(document["profiles"][0])
        away.update(id="away", weekdays=[])
        away["rows"][0]["blocks"][0]["label"] = "16 °C"
        document["profiles"].append(away)
        now = datetime(2026, 11, 16, 9, tzinfo=UTC)
        before = self.active(document, now)[0]
        document["manual_profile"] = "away"
        after = self.active(document, now)[0]
        self.assertNotEqual(before[2], after[2])
        self.assertEqual(after[1]["label"], "16 °C")

    def test_new_weekday_profile_overnight_end_is_next_change(self) -> None:
        document = plan("22:00", "06:00")
        tuesday_profile = document["profiles"][0]
        tuesday_profile["weekdays"] = [1]
        monday_profile = {"id": "monday", "name": "Monday", "weekdays": [0], "rows": []}
        document["profiles"].insert(0, monday_profile)
        now = datetime(2026, 11, 17, 0, 1, tzinfo=UTC)
        self.assertEqual(len(self.active(document, now)), 1)
        self.assertEqual(engine.next_change(document, now), datetime(2026, 11, 17, 6, tzinfo=UTC))
        self.assertEqual(self.active(document, datetime(2026, 11, 17, 6, tzinfo=UTC)), [])

    def test_no_matching_weekday(self) -> None:
        document = plan()
        document["profiles"][0]["weekdays"] = []
        now = datetime(2026, 11, 16, 9, tzinfo=UTC)
        self.assertIsNone(engine.select_profile(document, now))
        self.assertEqual(engine.next_change(document, now), datetime(2026, 11, 17, tzinfo=UTC))

    def test_disabled_has_no_profile_or_next_change(self) -> None:
        document = plan()
        document["enabled"] = False
        now = datetime(2026, 11, 16, 9, tzinfo=UTC)
        self.assertIsNone(engine.select_profile(document, now))
        self.assertIsNone(engine.next_change(document, now))

    def test_next_change_is_strictly_future(self) -> None:
        document = plan()
        now = datetime(2026, 11, 16, 8, tzinfo=UTC)
        self.assertEqual(engine.next_change(document, now), datetime(2026, 11, 16, 10, tzinfo=UTC))
        self.assertTrue(engine.is_block_start(document["profiles"][0]["rows"][0]["blocks"][0], now))

    def test_spring_gap_shifts_start_to_first_valid_minute(self) -> None:
        zone = ZoneInfo("Europe/Prague")
        document = plan("02:30", "04:00")
        now = datetime(2026, 3, 29, 1, 59, tzinfo=zone)
        due = engine.next_change(document, now)
        self.assertEqual(due, datetime(2026, 3, 29, 1, tzinfo=UTC))
        local_due = due.astimezone(zone)
        self.assertEqual((local_due.hour, local_due.minute), (3, 0))
        self.assertEqual(len(self.active(document, local_due)), 1)
        self.assertTrue(
            engine.is_block_start(document["profiles"][0]["rows"][0]["blocks"][0], local_due)
        )

    def test_fall_fold_does_not_restart_or_deactivate_running_block(self) -> None:
        zone = ZoneInfo("Europe/Prague")
        document = plan("02:30", "03:30")
        block = document["profiles"][0]["rows"][0]["blocks"][0]
        first = datetime(2026, 10, 25, 2, 30, tzinfo=zone, fold=0)
        second = datetime(2026, 10, 25, 2, 30, tzinfo=zone, fold=1)
        repeated_two = datetime(2026, 10, 25, 2, tzinfo=zone, fold=1)
        self.assertTrue(engine.is_block_start(block, first))
        self.assertFalse(engine.is_block_start(block, second))
        self.assertEqual(self.active(document, first)[0][2], self.active(document, second)[0][2])
        self.assertEqual(len(self.active(document, repeated_two)), 1)
        self.assertEqual(
            engine.next_change(document, first), datetime(2026, 10, 25, 2, 30, tzinfo=UTC)
        )

    def test_folded_end_does_not_reenter_block(self) -> None:
        zone = ZoneInfo("Europe/Prague")
        document = plan("01:00", "02:30")
        self.assertEqual(
            self.active(document, datetime(2026, 10, 25, 2, 15, tzinfo=zone, fold=1)), []
        )

    def test_spring_interval_entirely_inside_gap_is_skipped(self) -> None:
        zone = ZoneInfo("Europe/Prague")
        document = plan("02:00", "02:30")
        self.assertEqual(self.active(document, datetime(2026, 3, 29, 3, tzinfo=zone)), [])

    def test_timezone_change_recalculates_absolute_boundary(self) -> None:
        document = plan()
        instant = datetime(2026, 11, 16, 6, tzinfo=UTC)
        utc_due = engine.next_change(document, instant)
        prague_due = engine.next_change(document, instant.astimezone(ZoneInfo("Europe/Prague")))
        self.assertEqual(utc_due, datetime(2026, 11, 16, 8, tzinfo=UTC))
        self.assertEqual(prague_due, datetime(2026, 11, 16, 7, tzinfo=UTC))

    def test_leap_day_and_non_dst_zone(self) -> None:
        zone = ZoneInfo("Asia/Kolkata")
        document = plan("23:30", "00:30")
        before = datetime(2028, 2, 28, 23, 45, tzinfo=zone)
        after = datetime(2028, 2, 29, 0, 15, tzinfo=zone)
        self.assertEqual(self.active(document, before)[0][2], self.active(document, after)[0][2])
        self.assertEqual(
            engine.next_change(document, before), datetime(2028, 2, 28, 18, 30, tzinfo=UTC)
        )

    def test_naive_datetimes_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            engine.next_change(plan(), datetime(2026, 11, 16))

    def test_many_shared_boundaries_are_resolved_once(self) -> None:
        document = plan()
        profile = document["profiles"][0]
        template = profile["rows"][0]
        profile["rows"] = [dict(template, id=f"row-{index}") for index in range(2000)]
        now = datetime(2026, 11, 16, 9, tzinfo=UTC)
        with patch.object(engine, "_boundary", wraps=engine._boundary) as boundary:
            self.assertEqual(
                engine.next_change(document, now), datetime(2026, 11, 16, 10, tzinfo=UTC)
            )
            self.assertLessEqual(boundary.call_count, 6)
        with patch.object(engine, "_boundary", wraps=engine._boundary) as boundary:
            self.assertEqual(len(engine.active_blocks(profile, now)), 2000)
            self.assertLessEqual(boundary.call_count, 6)


if __name__ == "__main__":
    unittest.main()

"""Topic contract, migration and scheduling regressions."""

from copy import deepcopy
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.profile_scheduler.engine import active_blocks, next_change
from custom_components.profile_scheduler.runtime import SchedulerRuntime
from custom_components.profile_scheduler.validation import async_validate_document

pytestmark = pytest.mark.freeze_time("2026-11-16T12:00:00+00:00")


def block(identifier="b", start="22:00", end="06:00"):
    return {
        "id": identifier,
        "start": start,
        "end": end,
        "mode": "state",
        "label": "On",
        "color": "#ffffff",
        "actions": [{"action": "switch.turn_on", "target": {"entity_id": "switch.test"}}],
    }


def topic(identifier="one"):
    return {
        "id": identifier,
        "name": identifier,
        "entities": [{"id": "row", "name": "Row", "entity_ids": ["switch.test"]}],
        "active_profile": "p",
        "profiles": [
            {
                "id": "p",
                "name": "Profile",
                "schedule_mode": "weekly",
                "schedules": {str(i): [] for i in range(7)},
            }
        ],
    }


@pytest.mark.parametrize("first,second", [(0, 1), (6, 0)])
async def test_weekly_overlaps_rejected(hass, first, second):
    t = topic()
    schedules = t["profiles"][0]["schedules"]
    schedules[str(first)] = [{"id": "row", "blocks": [block()]}]
    schedules[str(second)] = [{"id": "row", "blocks": [block("other", "05:00", "07:00")]}]
    with pytest.raises(HomeAssistantError, match="overlap"):
        await async_validate_document(hass, {"enabled": True, "topics": [t]})
    schedules[str(second)][0]["blocks"][0]["start"] = "06:00"
    await async_validate_document(hass, {"enabled": True, "topics": [t]})


async def test_daily_overlap_wrap_and_unknown_row(hass):
    t = topic()
    p = t["profiles"][0]
    p.update(
        schedule_mode="daily",
        schedules={"all": [{"id": "row", "blocks": [block(), block("other", "05:00", "07:00")]}]},
    )
    with pytest.raises(HomeAssistantError, match="overlap"):
        await async_validate_document(hass, {"enabled": True, "topics": [t]})
    p["schedules"]["all"][0]["id"] = "missing"
    with pytest.raises(HomeAssistantError, match="unknown"):
        await async_validate_document(hass, {"enabled": True, "topics": [t]})


def test_weekly_overnight_and_boundary():
    t = topic()
    t["profiles"][0]["schedules"]["0"] = [{"id": "row", "blocks": [block()]}]
    profile = t["profiles"][0]
    assert len(active_blocks(profile, datetime(2026, 11, 17, 5, tzinfo=UTC))) == 1
    assert active_blocks(profile, datetime(2026, 11, 17, 6, tzinfo=UTC)) == []
    assert next_change(
        {"enabled": True, "topics": [t]}, datetime(2026, 11, 17, 5, tzinfo=UTC)
    ) == datetime(2026, 11, 17, 6, tzinfo=UTC)


@pytest.mark.parametrize("manual", [None, "home"])
async def test_store_v1_migration_and_restart(
    hass, enable_custom_integrations, legacy_schedule_document, manual
):
    schedule_document = legacy_schedule_document
    schedule_document["manual_profile"] = manual
    await Store(hass, 1, "profile_scheduler.migration").async_save(
        {"document": schedule_document, "revision": 4}
    )
    runtime = SchedulerRuntime(hass, "migration")
    await runtime.async_load()
    t = runtime.document["topics"][0]
    assert t["active_profile"] == manual
    assert (
        t["profiles"][0]["schedules"]["all"][0]["blocks"]
        == schedule_document["profiles"][0]["rows"][0]["blocks"]
    )
    assert t["entities"][0]["entity_ids"] == ["climate.scheduler_test"]
    assert runtime.revision == 4
    restored = SchedulerRuntime(hass, "migration")
    await restored.async_load()
    assert restored.document == runtime.document


async def test_concurrent_topics_and_profile_selection(hass, runtime):
    calls = []

    async def turn_on(call):
        calls.append(call.data["entity_id"])

    hass.services.async_register("switch", "turn_on", turn_on)
    a, b = topic("a"), topic("b")
    for t in (a, b):
        t["profiles"][0].update(
            schedule_mode="daily",
            schedules={"all": [{"id": "row", "blocks": [block(start="00:00", end="24:00")]}]},
        )
    await runtime.async_save({"enabled": True, "topics": [a, b]}, runtime.revision)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(calls) == 2
    await runtime.async_set_profile("a", None)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(calls) == 2
    assert runtime.active_profile == {"a": None, "b": "p"}
    before = deepcopy(runtime.document)
    with pytest.raises(HomeAssistantError):
        await runtime.async_set_profile("a", "missing")
    assert runtime.document == before


async def test_dynamic_selects(hass, enable_custom_integrations):
    entry = MockConfigEntry(domain="profile_scheduler", unique_id="profile_scheduler", data={})
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.panel_custom.async_register_panel", new_callable=AsyncMock
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        runtime = entry.runtime_data
        a, b = topic("a"), topic("b")
        await runtime.async_save({"enabled": False, "topics": [a, b]}, 0)
        await hass.async_block_till_done()
        assert len(hass.states.async_entity_ids("select")) == 2
        for state in hass.states.async_all("select"):
            assert "Inactive" in state.attributes["options"]
            assert "automatic" not in state.attributes["options"]
        b["name"] = "Renamed"
        await runtime.async_save({"enabled": False, "topics": [b]}, 1)
        await hass.async_block_till_done()
        states = hass.states.async_all("select")
        assert len(states) == 1
        assert "Renamed" in states[0].attributes["friendly_name"]
        assert await hass.config_entries.async_unload(entry.entry_id)


async def test_profile_change_at_other_topics_boundary_runs_one_shot(hass, runtime, freezer):
    """Replacing a topic must process an already-due boundary for the others."""
    a, b = topic("a"), topic("b")
    once = block(start="14:00", end="15:00")
    once.update(mode="once", actions=[{"event": "other_topic_due"}])
    b["profiles"][0].update(
        schedule_mode="daily", schedules={"all": [{"id": "row", "blocks": [once]}]}
    )
    events = []
    hass.bus.async_listen("other_topic_due", events.append)
    await runtime.async_save({"enabled": True, "topics": [a, b]}, runtime.revision)
    freezer.move_to("2026-11-16T13:00:00+00:00")
    await runtime.async_set_profile("a", None)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(events) == 1
    await runtime.async_evaluate(due=datetime(2026, 11, 16, 13, tzinfo=UTC))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(events) == 1


async def test_migrate_maximum_legacy_rows(hass, enable_custom_integrations):
    profiles = []
    for i in range(32):
        rows = [
            {"id": f"row_{j}", "name": f"Row {i} {j}", "entity_ids": [], "blocks": []}
            for j in range(100)
        ]
        profiles.append(
            {"id": f"profile_{i}", "name": f"Profile {i}", "weekdays": [], "rows": rows}
        )
    old = {"enabled": True, "manual_profile": "profile_0", "profiles": profiles}
    await Store(hass, 1, "profile_scheduler.large").async_save({"document": old, "revision": 1})
    runtime = SchedulerRuntime(hass, "large")
    await runtime.async_load()
    t = runtime.document["topics"][0]
    assert len(t["entities"]) == 3200
    assert len(t["profiles"]) == 32
    assert all(len(p["schedules"]["all"]) == 100 for p in t["profiles"])
    assert t["active_profile"] == "profile_0"
    restored = SchedulerRuntime(hass, "large")
    await restored.async_load()
    assert restored.document == runtime.document


async def test_automatic_migration_notifies(
    hass, enable_custom_integrations, legacy_schedule_document
):
    from homeassistant.components import persistent_notification

    legacy_schedule_document["manual_profile"] = None
    await Store(hass, 1, "profile_scheduler.notice").async_save(
        {"document": legacy_schedule_document, "revision": 1}
    )
    runtime = SchedulerRuntime(hass, "notice")
    with patch.object(
        persistent_notification, "async_create", wraps=persistent_notification.async_create
    ) as create:
        await runtime.async_load()
    assert create.call_count == 1
    assert "inactive" in create.call_args.args[1]
    assert create.call_args.kwargs["notification_id"] == "profile_scheduler_migration_notice"


async def test_weekly_midnight_runs_once_without_switching_profile(hass, runtime, freezer):
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    t = topic()
    once = block(start="00:00", end="00:30")
    once.update(mode="once", actions=[{"event": "weekly_midnight"}])
    t["profiles"][0]["schedules"]["1"] = [{"id": "row", "blocks": [once]}]
    events = []
    hass.bus.async_listen("weekly_midnight", events.append)
    freezer.move_to("2026-11-16T22:59:00+00:00")
    await runtime.async_save({"enabled": True, "topics": [t]}, runtime.revision)
    due = datetime(2026, 11, 16, 23, tzinfo=UTC)
    freezer.move_to(due)
    async_fire_time_changed(hass, due)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(events) == 1
    assert runtime.active_profile == {"one": "p"}
    await runtime.async_evaluate(recover=True)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(events) == 1


async def test_websocket_selects_specific_topic(hass, runtime, hass_ws_client):
    from custom_components.profile_scheduler.websocket import async_register_websocket

    a, b = topic("a"), topic("b")
    await runtime.async_save({"enabled": False, "topics": [a, b]}, runtime.revision)
    hass.data["profile_scheduler"] = {"runtime": runtime}
    async_register_websocket(hass)
    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "profile_scheduler/set_profile", "topic_id": "a", "profile_id": None}
    )
    response = await client.receive_json()
    assert response["success"]
    assert [t["active_profile"] for t in response["result"]["document"]["topics"]] == [None, "p"]
    await client.send_json(
        {"id": 2, "type": "profile_scheduler/set_profile", "topic_id": "b", "profile_id": "missing"}
    )
    response = await client.receive_json()
    assert not response["success"]
    assert runtime.document["topics"][1]["active_profile"] == "p"


async def test_invalid_overlap_save_does_not_replace_running_or_stored_plan(hass, runtime):
    t = topic()
    plan = {"enabled": False, "topics": [t]}
    await runtime.async_save(plan, runtime.revision)
    invalid = deepcopy(plan)
    schedules = invalid["topics"][0]["profiles"][0]["schedules"]
    schedules["6"] = [{"id": "row", "blocks": [block()]}]
    schedules["0"] = [{"id": "row", "blocks": [block("overlap", "05:00", "07:00")]}]
    with pytest.raises(HomeAssistantError, match="overlap"):
        await runtime.async_save(invalid, runtime.revision)
    assert runtime.document == plan
    assert runtime.revision == 1
    reloaded = SchedulerRuntime(hass, "runtime-test")
    await reloaded.async_load()
    assert reloaded.document == plan
    assert reloaded.revision == 1

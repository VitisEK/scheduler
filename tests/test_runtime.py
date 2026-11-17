"""Behavioral tests for dispatch, recovery, persistence, and validation."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from copy import deepcopy
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import Event, HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.profile_scheduler.runtime import SchedulerRuntime
from custom_components.profile_scheduler.validation import async_validate_document

if TYPE_CHECKING:
    from freezegun.api import FrozenDateTimeFactory

pytestmark = pytest.mark.freeze_time("2026-11-16T11:00:00+00:00")


async def advance(hass: HomeAssistant, freezer: FrozenDateTimeFactory, timestamp: str) -> None:
    """Advance both the frozen clock and HA's actual timer callbacks."""
    instant = datetime.fromisoformat(timestamp).astimezone(UTC)
    freezer.move_to(instant)
    async_fire_time_changed(hass, instant)
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_save_applies_current_state_and_keeps_raw_actions(
    hass: HomeAssistant,
    runtime: SchedulerRuntime,
    schedule_document: dict[str, Any],
    action_calls: list[dict[str, Any]],
) -> None:
    """Saving a current state block applies it through HA's Script engine."""
    await runtime.async_save(schedule_document, runtime.revision)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert [call["temperature"] for call in action_calls] == [21]
    assert hass.states.get("climate.scheduler_test").attributes["temperature"] == 21
    snapshot = runtime.snapshot()
    assert snapshot["document"] == schedule_document
    assert snapshot["active_profile"] == {"topic": "home"}
    assert snapshot["next_change"] is not None
    assert snapshot["last_error"] is None


@pytest.mark.parametrize(
    ("domain", "service", "target", "data", "mode"),
    [
        (
            "light",
            "turn_on",
            "light.scheduler_test",
            {"brightness_pct": 35},
            "state",
        ),
        ("switch", "turn_off", "switch.scheduler_test", {}, "state"),
        ("number", "set_value", "number.ev_current", {"value": 8}, "state"),
        ("select", "select_option", "select.ev_mode", {"option": "Solar"}, "state"),
        ("scene", "turn_on", "scene.scheduler_test", {}, "once"),
        (
            "script",
            "turn_on",
            "script.test_charge",
            {"variables": {"limit": 8}},
            "once",
        ),
        ("script", "test_charge", None, {"limit": 8}, "once"),
    ],
    ids=[
        "light-brightness",
        "switch-off",
        "ev-current",
        "ev-mode",
        "scene-once",
        "script-turn-on-variables",
        "script-direct-call",
    ],
)
async def test_native_action_domains_dispatch_targets_and_parameters(
    hass: HomeAssistant,
    runtime: SchedulerRuntime,
    schedule_document: dict[str, Any],
    freezer: FrozenDateTimeFactory,
    domain: str,
    service: str,
    target: str | None,
    data: dict[str, Any],
    mode: str,
) -> None:
    """The same native Script boundary supports lighting, EV settings and one-shots."""
    calls: list[ServiceCall] = []

    async def capture(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(domain, service, capture)
    action: dict[str, Any] = {"action": f"{domain}.{service}", "data": data}
    if target is not None:
        action["target"] = {"entity_id": target}
    row = schedule_document["topics"][0]["profiles"][0]["schedules"]["all"][0]
    schedule_document["topics"][0]["entities"][0]["entity_ids"] = (
        [target] if target is not None else []
    )
    row["blocks"][0].update(start="13:00", end="14:00", mode=mode, actions=[action])
    schedule_document["topics"][0]["profiles"][0]["schedules"]["all"] = [row]

    await runtime.async_save(schedule_document, runtime.revision)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert calls == []

    await advance(hass, freezer, "2026-11-16T12:00:00+00:00")

    assert len(calls) == 1
    call = calls[0]
    assert (call.domain, call.service) == (domain, service)
    for key, value in data.items():
        assert call.data[key] == value
    if target is not None:
        entity_ids = call.data["entity_id"]
        assert target in ([entity_ids] if isinstance(entity_ids, str) else entity_ids)

    # Restorable device settings are reapplied on enable; scenes and both
    # forms of script invocation remain one-shots despite still being active.
    await runtime.async_set_enabled(False)
    await runtime.async_set_enabled(True)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(calls) == (2 if mode == "state" else 1)


async def test_reload_restores_state_without_replaying_once(
    hass: HomeAssistant,
    runtime: SchedulerRuntime,
    schedule_document: dict[str, Any],
    action_calls: list[dict[str, Any]],
    freezer: FrozenDateTimeFactory,
) -> None:
    """A new runtime loads stored data but never replays an active event block."""
    once_events: list[Event] = []
    hass.bus.async_listen("scheduler_test_once", once_events.append)
    await runtime.async_save(schedule_document, runtime.revision)
    revision = runtime.revision
    await runtime.async_stop()
    freezer.move_to("2026-11-16T12:15:00+00:00")
    action_calls.clear()

    restored = SchedulerRuntime(hass, "runtime-test")
    await restored.async_load()
    try:
        await restored.async_start()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert restored.document == schedule_document
        assert restored.revision == revision
        assert [call["temperature"] for call in action_calls] == [21]
        assert once_events == []
    finally:
        await restored.async_stop()


async def test_once_runs_at_boundary_only_and_not_on_enable(
    hass: HomeAssistant,
    runtime: SchedulerRuntime,
    schedule_document: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Timers execute one-shot actions once; re-enable is state recovery."""
    once_events: list[Event] = []
    hass.bus.async_listen("scheduler_test_once", once_events.append)
    await runtime.async_save(schedule_document, runtime.revision)
    await advance(hass, freezer, "2026-11-16T12:00:00+00:00")
    assert len(once_events) == 1

    # A duplicated timer evaluation cannot dispatch the same occurrence twice.
    await runtime.async_evaluate(due=datetime(2026, 11, 16, 12, tzinfo=UTC))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(once_events) == 1
    await runtime.async_set_enabled(False)
    await advance(hass, freezer, "2026-11-16T12:05:00+00:00")
    await runtime.async_set_enabled(True)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(once_events) == 1


async def test_profile_change_recomputes_state_without_once(
    hass: HomeAssistant,
    runtime: SchedulerRuntime,
    schedule_document: dict[str, Any],
    action_calls: list[dict[str, Any]],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Manual selection applies the other profile even during its one-shot block."""
    away = deepcopy(schedule_document["topics"][0]["profiles"][0])
    away["id"] = "away"
    away["name"] = "Away"
    away["schedules"]["all"][0]["blocks"][0]["actions"][0]["data"]["temperature"] = 17
    away["schedules"]["all"][1]["blocks"][0]["start"] = "12:00"
    away["schedules"]["all"][1]["blocks"][0]["end"] = "14:00"
    schedule_document["topics"][0]["profiles"].append(away)
    once_events: list[Event] = []
    hass.bus.async_listen("scheduler_test_once", once_events.append)
    await runtime.async_save(schedule_document, runtime.revision)
    action_calls.clear()
    freezer.move_to("2026-11-16T11:15:00+00:00")

    await runtime.async_set_profile("topic", "away")
    await hass.async_block_till_done(wait_background_tasks=True)

    assert runtime.snapshot()["active_profile"] == {"topic": "away"}
    assert [call["temperature"] for call in action_calls] == [17]
    assert once_events == []


async def test_stop_cancels_future_dispatch(
    hass: HomeAssistant,
    runtime: SchedulerRuntime,
    schedule_document: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    """No stale one-shot callback may dispatch after unload."""
    once_events: list[Event] = []
    hass.bus.async_listen("scheduler_test_once", once_events.append)
    await runtime.async_save(schedule_document, runtime.revision)
    await runtime.async_stop()

    await advance(hass, freezer, "2026-11-16T12:00:00+00:00")

    assert once_events == []


async def test_invalid_revision_or_profile_cannot_mutate_plan(
    runtime: SchedulerRuntime, schedule_document: dict[str, Any]
) -> None:
    """Concurrent editor saves and unknown selections fail without mutation."""
    await runtime.async_save(schedule_document, runtime.revision)
    original = deepcopy(runtime.document)
    revision = runtime.revision
    changed = deepcopy(original)
    changed["topics"][0]["profiles"][0]["name"] = "Stale editor"
    with pytest.raises(HomeAssistantError):
        await runtime.async_save(changed, revision - 1)
    with pytest.raises(HomeAssistantError):
        await runtime.async_set_profile("topic", "missing")
    assert runtime.document == original
    assert runtime.revision == revision


@pytest.mark.parametrize("invalid_kind", ["overlap", "bad_action", "unsafe_restore"])
async def test_document_validation_rejects_invalid_actions_and_overlap(
    hass: HomeAssistant, schedule_document: dict[str, Any], invalid_kind: str
) -> None:
    """Invalid schedules are rejected before persistence or device execution."""
    row = schedule_document["topics"][0]["profiles"][0]["schedules"]["all"][0]
    block = row["blocks"][0]
    if invalid_kind == "overlap":
        overlap = deepcopy(block)
        overlap["id"] = "overlapping"
        overlap["start"] = "12:00"
        overlap["end"] = "13:00"
        row["blocks"].append(overlap)
    elif invalid_kind == "bad_action":
        block["actions"] = [{"action": "not a valid service"}]
    else:
        block["actions"] = [{"event": "scheduler_test_once"}]
    with pytest.raises((HomeAssistantError, ValueError)):
        await async_validate_document(hass, schedule_document)


async def test_native_entry_setup_unload_reload(
    hass: HomeAssistant,
    enable_custom_integrations: None,
    schedule_document: dict[str, Any],
    action_calls: list[dict[str, Any]],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Exercise the entry lifecycle and real platforms, mocking only panel rendering."""
    entry = MockConfigEntry(domain="profile_scheduler", unique_id="profile_scheduler", data={})
    entry.add_to_hass(hass)
    await hass.config.async_update(time_zone="Europe/Prague")
    with patch(
        "homeassistant.components.panel_custom.async_register_panel",
        new_callable=AsyncMock,
    ) as panel:
        assert await hass.config_entries.async_setup(entry.entry_id)
        if not hass.is_running:
            await hass.async_start()
        await hass.async_block_till_done(wait_background_tasks=True)
        panel.assert_awaited_once()
        panel_file = (
            Path(__file__).parents[1] / "custom_components/profile_scheduler/frontend/panel.js"
        )
        digest = sha256(panel_file.read_bytes()).hexdigest()
        assert (
            panel.await_args.kwargs["module_url"]
            == f"/profile_scheduler_static/panel.js?v={digest}"
        )
        first = entry.runtime_data
        await first.async_save(schedule_document, first.revision)
        await hass.async_block_till_done(wait_background_tasks=True)
        revision = first.revision
        assert hass.states.async_entity_ids("switch")
        assert hass.states.async_entity_ids("select")
        assert len(hass.states.async_entity_ids("sensor")) >= 1

        assert await hass.config_entries.async_unload(entry.entry_id)
        action_calls.clear()
        await advance(hass, freezer, "2026-11-16T12:15:00+00:00")
        assert action_calls == []
        assert "runtime" not in hass.data["profile_scheduler"]

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        restored = entry.runtime_data
        assert restored is not first
        assert restored.document == schedule_document
        assert restored.revision == revision
        assert [call["temperature"] for call in action_calls] == [21]
        assert await hass.config_entries.async_unload(entry.entry_id)


async def test_websocket_mutations_require_admin(
    hass: HomeAssistant,
    runtime: SchedulerRuntime,
    hass_ws_client: Callable[..., Awaitable[Any]],
    hass_read_only_access_token: str,
) -> None:
    """A normal authenticated connection cannot enable or edit execution."""
    from custom_components.profile_scheduler.websocket import async_register_websocket

    hass.data["profile_scheduler"] = {"runtime": runtime}
    async_register_websocket(hass)
    client = await hass_ws_client(hass, hass_read_only_access_token)
    for message_id, message in enumerate(
        [
            {"type": "profile_scheduler/get"},
            {"type": "profile_scheduler/set_enabled", "enabled": True},
            {"type": "profile_scheduler/set_profile", "topic_id": "topic", "profile_id": "home"},
            {"type": "profile_scheduler/save", "revision": 0, "document": {}},
        ],
        start=1,
    ):
        await client.send_json({"id": message_id, **message})
        response = await client.receive_json()
        assert response["success"] is False
        assert response["error"]["code"] == "unauthorized"
    assert runtime.document["enabled"] is False
    assert runtime.revision == 0


async def test_admin_websocket_reports_revision_conflict(
    hass: HomeAssistant,
    runtime: SchedulerRuntime,
    schedule_document: dict[str, Any],
    hass_ws_client: Callable[..., Awaitable[Any]],
) -> None:
    """The panel round trip saves structured actions and rejects a stale writer."""
    from custom_components.profile_scheduler.websocket import async_register_websocket

    hass.data["profile_scheduler"] = {"runtime": runtime}
    async_register_websocket(hass)
    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "profile_scheduler/save",
            "document": schedule_document,
            "revision": runtime.revision,
        }
    )
    response = await client.receive_json()
    assert response["success"] is True
    assert response["result"]["document"] == schedule_document
    assert response["result"]["revision"] == 1
    await client.send_json(
        {
            "id": 2,
            "type": "profile_scheduler/save",
            "document": schedule_document,
            "revision": 0,
        }
    )
    response = await client.receive_json()
    assert response["success"] is False
    assert runtime.revision == 1


async def test_stale_callback_queued_during_save_cannot_cancel_new_actions(
    hass: HomeAssistant,
    runtime: SchedulerRuntime,
    schedule_document: dict[str, Any],
    action_calls: list[dict[str, Any]],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Recheck callback generation after waiting for a concurrent save's lock."""
    timers: list[tuple[Callable[..., Awaitable[None]], datetime]] = []

    def track_boundary(
        _hass: HomeAssistant,
        action: Callable[..., Awaitable[None]],
        due: datetime,
    ) -> Callable[[], None]:
        timers.append((action, due))
        return lambda: None

    with patch(
        "custom_components.profile_scheduler.runtime.async_track_point_in_utc_time",
        side_effect=track_boundary,
    ):
        await runtime.async_save(schedule_document, runtime.revision)
        await hass.async_block_till_done(wait_background_tasks=True)
        old_callback, old_due = timers[-1]
        replacement = deepcopy(schedule_document)
        replacement["topics"][0]["profiles"][0]["schedules"]["all"][0]["blocks"][0]["actions"][0][
            "data"
        ]["temperature"] = 23
        action_calls.clear()
        once_events: list[Event] = []
        hass.bus.async_listen("scheduler_test_once", once_events.append)
        freezer.move_to(old_due)

        save_entered = asyncio.Event()
        finish_save = asyncio.Event()
        callback_entered = asyncio.Event()
        original_save = runtime.store.async_save
        original_evaluate = runtime.async_evaluate

        async def delayed_save(data: dict[str, Any]) -> None:
            save_entered.set()
            await finish_save.wait()
            await original_save(data)

        async def observed_evaluate(*args: Any, **kwargs: Any) -> None:
            callback_entered.set()
            await original_evaluate(*args, **kwargs)

        with (
            patch.object(runtime.store, "async_save", side_effect=delayed_save),
            patch.object(runtime, "async_evaluate", side_effect=observed_evaluate),
        ):
            save_task = asyncio.create_task(runtime.async_save(replacement, runtime.revision))
            callback_task = None
            try:
                await asyncio.wait_for(save_entered.wait(), timeout=5)
                callback_task = asyncio.create_task(old_callback(old_due))
                await asyncio.wait_for(callback_entered.wait(), timeout=5)
                finish_save.set()
                await asyncio.wait_for(asyncio.gather(save_task, callback_task), timeout=5)
            finally:
                finish_save.set()
                for task in (save_task, callback_task):
                    if task is not None and not task.done():
                        task.cancel()
                await asyncio.gather(
                    *(task for task in (save_task, callback_task) if task is not None),
                    return_exceptions=True,
                )
        await hass.async_block_till_done(wait_background_tasks=True)

        # A stale callback must neither replace the new timer nor cancel its
        # just-created state dispatch before that task has started running.
        assert len(timers) == 2
        assert [call["temperature"] for call in action_calls] == [23]
        assert once_events == []
        assert runtime.document == replacement


async def test_state_action_rejects_templated_data_key(
    hass: HomeAssistant, schedule_document: dict[str, Any]
) -> None:
    """Templated dictionary keys cannot disguise relative, non-repeatable actions."""
    schedule_document["topics"][0]["profiles"][0]["schedules"]["all"][0]["blocks"][0]["actions"] = [
        {
            "action": "light.turn_on",
            "target": {"entity_id": "light.scheduler_test"},
            "data": {"{{ 'brightness_step' }}": 50},
        }
    ]
    with pytest.raises(HomeAssistantError, match="State mode"):
        await async_validate_document(hass, schedule_document)


async def test_native_switch_can_disable_its_own_running_scheduler(
    hass: HomeAssistant,
    enable_custom_integrations: None,
    schedule_document: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    """A native action targeting this scheduler must not await its own cancellation."""
    entry = MockConfigEntry(domain="profile_scheduler", unique_id="profile_scheduler", data={})
    entry.add_to_hass(hass)
    await hass.config.async_update(time_zone="Europe/Prague")
    with patch(
        "homeassistant.components.panel_custom.async_register_panel",
        new_callable=AsyncMock,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        if not hass.is_running:
            await hass.async_start()
        await hass.async_block_till_done(wait_background_tasks=True)
        registry = er.async_get(hass)
        switch_id = next(
            entity.entity_id
            for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
            if entity.domain == "switch"
        )
        disable_block = {
            "id": "disable",
            "start": "13:00",
            "end": "13:30",
            "mode": "once",
            "label": "Disable scheduler",
            "color": "#ff9800",
            "actions": [{"action": "switch.turn_off", "target": {"entity_id": switch_id}}],
        }
        later_block = deepcopy(disable_block)
        later_block.update(
            id="later",
            start="14:00",
            end="14:30",
            label="Must not execute",
            actions=[{"event": "scheduler_test_after_disable"}],
        )
        schedule_document["topics"][0]["entities"] = [
            {"id": "control", "name": "Scheduler control", "entity_ids": [switch_id]}
        ]
        schedule_document["topics"][0]["profiles"][0]["schedules"]["all"] = [
            {"id": "control", "blocks": [disable_block, later_block]}
        ]
        scheduler = entry.runtime_data
        later_events: list[Event] = []
        hass.bus.async_listen("scheduler_test_after_disable", later_events.append)
        await scheduler.async_save(schedule_document, scheduler.revision)
        try:
            # Advance the frozen monotonic clock before creating the timeout;
            # otherwise the one-hour jump immediately expires a five-second bound.
            boundary = datetime(2026, 11, 16, 12, tzinfo=UTC)
            freezer.move_to(boundary)
            async_fire_time_changed(hass, boundary)
            await asyncio.wait_for(
                hass.async_block_till_done(wait_background_tasks=True), timeout=5
            )
            assert scheduler.document["enabled"] is False
            assert hass.states.get(switch_id).state == "off"
            later_boundary = datetime(2026, 11, 16, 13, tzinfo=UTC)
            freezer.move_to(later_boundary)
            async_fire_time_changed(hass, later_boundary)
            await asyncio.wait_for(
                hass.async_block_till_done(wait_background_tasks=True), timeout=5
            )
            assert later_events == []
        finally:
            await asyncio.wait_for(hass.config_entries.async_unload(entry.entry_id), timeout=5)


@pytest.mark.freeze_time("2026-11-16T11:00:00+00:00", real_asyncio=True)
async def test_sequence_can_change_other_topic_then_disable_scheduler(
    hass: HomeAssistant,
    enable_custom_integrations: None,
    schedule_document: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    """A surviving script remains recognizable after another topic changes profile."""
    entry = MockConfigEntry(domain="profile_scheduler", unique_id="profile_scheduler", data={})
    entry.add_to_hass(hass)
    await hass.config.async_update(time_zone="Europe/Prague")
    with patch(
        "homeassistant.components.panel_custom.async_register_panel", new_callable=AsyncMock
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        if not hass.is_running:
            await hass.async_start()
        await hass.async_block_till_done(wait_background_tasks=True)
        scheduler = entry.runtime_data
        first = schedule_document["topics"][0]
        second = deepcopy(first)
        second.update(id="second", name="Second", active_profile=None)
        second["profiles"][0]["schedules"]["all"] = []
        first["profiles"][0]["schedules"]["all"] = []
        schedule_document["topics"].append(second)
        await scheduler.async_save(schedule_document, scheduler.revision)
        await hass.async_block_till_done(wait_background_tasks=True)
        registry = er.async_get(hass)
        select_id = registry.async_get_entity_id(
            "select", "profile_scheduler", f"{entry.entry_id}_topic_second_profile"
        )
        switch_id = registry.async_get_entity_id(
            "switch", "profile_scheduler", f"{entry.entry_id}_enabled"
        )
        assert select_id is not None and switch_id is not None
        first["entities"] = [{"id": "control", "name": "Control", "entity_ids": []}]
        first["profiles"][0]["schedules"]["all"] = [
            {
                "id": "control",
                "blocks": [
                    {
                        "id": "run",
                        "start": "13:01",
                        "end": "13:30",
                        "mode": "once",
                        "label": "Control scheduler",
                        "color": "#ffffff",
                        "actions": [
                            {
                                "action": "select.select_option",
                                "target": {"entity_id": select_id},
                                "data": {"option": "Home"},
                            },
                            {"action": "switch.turn_off", "target": {"entity_id": switch_id}},
                        ],
                    }
                ],
            }
        ]
        await scheduler.async_save(schedule_document, scheduler.revision)
        due = datetime(2026, 11, 16, 12, 1, tzinfo=UTC)
        freezer.move_to(due)
        async_fire_time_changed(hass, due)
        try:
            await asyncio.wait_for(
                hass.async_block_till_done(wait_background_tasks=True), timeout=3
            )
            assert scheduler.document["topics"][1]["active_profile"] == "home"
            assert scheduler.document["enabled"] is False
            assert hass.states.get(switch_id).state == "off"
            assert scheduler._tasks == {}
        finally:
            await asyncio.wait_for(hass.config_entries.async_unload(entry.entry_id), timeout=3)

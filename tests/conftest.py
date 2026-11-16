"""Shared fixtures; Home Assistant imports stay lazy for pure engine tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from custom_components.profile_scheduler.runtime import SchedulerRuntime


@pytest.fixture
def schedule_document() -> dict[str, Any]:
    """Return a state block plus a one-shot block in separate rows."""
    return {
        "enabled": True,
        "manual_profile": "home",
        "profiles": [
            {
                "id": "home",
                "name": "Home",
                "weekdays": list(range(7)),
                "rows": [
                    {
                        "id": "heating",
                        "name": "Heating",
                        "entity_ids": ["climate.scheduler_test"],
                        "blocks": [
                            {
                                "id": "warm",
                                "start": "00:00",
                                "end": "24:00",
                                "mode": "state",
                                "label": "21 °C",
                                "color": "#ff9800",
                                "actions": [
                                    {
                                        "action": "climate.set_temperature",
                                        "target": {"entity_id": "climate.scheduler_test"},
                                        "data": {"temperature": 21},
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "id": "once",
                        "name": "One-shot action",
                        "entity_ids": [],
                        "blocks": [
                            {
                                "id": "notify",
                                "start": "13:00",
                                "end": "13:30",
                                "mode": "once",
                                "label": "Fire event",
                                "color": "#2196f3",
                                "actions": [{"event": "scheduler_test_once"}],
                            }
                        ],
                    },
                ],
            }
        ],
    }


@pytest.fixture
def action_calls(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Capture only a synthetic service boundary, leaving HA Script real."""
    calls: list[dict[str, Any]] = []

    async def set_temperature(call: ServiceCall) -> None:
        calls.append(dict(call.data))
        hass.states.async_set(
            "climate.scheduler_test", "heat", {"temperature": call.data["temperature"]}
        )

    hass.services.async_register("climate", "set_temperature", set_temperature)
    return calls


@pytest.fixture
async def runtime(
    hass: HomeAssistant,
    enable_custom_integrations: None,
    action_calls: list[dict[str, Any]],
) -> AsyncGenerator[SchedulerRuntime]:
    """Use actual HA storage, event loop, Script, and callback helpers."""
    from custom_components.profile_scheduler.runtime import SchedulerRuntime

    await hass.config.async_update(time_zone="Europe/Prague")
    scheduler = SchedulerRuntime(hass, "runtime-test")
    await scheduler.async_load()
    await scheduler.async_start()
    try:
        yield scheduler
    finally:
        await scheduler.async_stop()

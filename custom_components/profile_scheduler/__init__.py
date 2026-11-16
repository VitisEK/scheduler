"""Profile Scheduler: structured schedules executed by Home Assistant."""

from pathlib import Path
from typing import Any

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_CORE_CONFIG_UPDATE,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PANEL_PATH
from .runtime import SchedulerRuntime
from .websocket import async_register_websocket

type SchedulerConfigEntry = ConfigEntry[SchedulerRuntime]

PLATFORMS = (Platform.SELECT, Platform.SENSOR, Platform.SWITCH)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Initialize process-scoped resources once."""
    data: dict[str, Any] = hass.data.setdefault(DOMAIN, {})
    if not data.get("registered"):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    "/profile_scheduler_static", str(Path(__file__).parent / "frontend"), False
                )
            ]
        )
        async_register_websocket(hass)
        data["registered"] = True
    return True


async def async_setup_entry(hass: HomeAssistant, entry: SchedulerConfigEntry) -> bool:
    """Load stored schedules, entities and the custom time editor."""
    runtime = SchedulerRuntime(hass, entry.entry_id)
    await runtime.async_load()
    entry.runtime_data = runtime
    hass.data[DOMAIN]["runtime"] = runtime
    try:
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_PATH,
            webcomponent_name="profile-scheduler-panel",
            sidebar_title="Scheduler",
            sidebar_icon="mdi:calendar-clock",
            module_url="/profile_scheduler_static/panel.js?v=0.1.0",
            require_admin=True,
            config_panel_domain=DOMAIN,
        )
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        async def stop(_: Event) -> None:
            await runtime.async_stop()

        entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop))

        async def core_config_changed(event: Event) -> None:
            if "time_zone" in event.data:
                await runtime.async_evaluate(recover=True)

        entry.async_on_unload(hass.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, core_config_changed))
        if hass.is_running:
            await runtime.async_start()
        else:

            async def start(_: Event) -> None:
                await runtime.async_start()

            entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start))
    except Exception:
        await runtime.async_stop()
        frontend.async_remove_panel(hass, PANEL_PATH)
        hass.data[DOMAIN].pop("runtime", None)
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SchedulerConfigEntry) -> bool:
    """Cancel execution and remove native entities and sidebar registration."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.async_stop()
    frontend.async_remove_panel(hass, PANEL_PATH)
    hass.data[DOMAIN].pop("runtime", None)
    return True


async def async_remove_entry(hass: HomeAssistant, entry: SchedulerConfigEntry) -> None:
    """Remove stored plans only when the integration is deleted."""
    from homeassistant.helpers.storage import Store

    from .const import STORAGE_VERSION

    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()

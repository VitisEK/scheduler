"""Enable and disable the stored scheduler with a native switch."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SchedulerConfigEntry
from .entity import SchedulerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: SchedulerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SchedulerSwitch(entry.runtime_data, "enabled")])


class SchedulerSwitch(SchedulerEntity, SwitchEntity):
    """Persist scheduler enablement and reconcile state when enabled."""

    _attr_icon = "mdi:calendar-check"

    @property
    def is_on(self) -> bool:
        return self.runtime.document["enabled"]

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_check_admin()
        await self.runtime.async_set_enabled(True, self._context)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_check_admin()
        await self.runtime.async_set_enabled(False, self._context)

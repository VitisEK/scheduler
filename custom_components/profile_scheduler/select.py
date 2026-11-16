"""Select a manual profile or automatic weekday selection."""

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SchedulerConfigEntry
from .const import AUTOMATIC
from .entity import SchedulerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: SchedulerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SchedulerSelect(entry.runtime_data, "profile")])


class SchedulerSelect(SchedulerEntity, SelectEntity):
    """Expose profile selection to normal HA dashboards and automations."""

    _attr_icon = "mdi:calendar-account"

    @property
    def options(self) -> list[str]:
        return [AUTOMATIC, *(profile["name"] for profile in self.runtime.document["profiles"])]

    @property
    def current_option(self) -> str:
        selected = self.runtime.document["manual_profile"]
        return next(
            (
                profile["name"]
                for profile in self.runtime.document["profiles"]
                if profile["id"] == selected
            ),
            AUTOMATIC,
        )

    async def async_select_option(self, option: str) -> None:
        await self.async_check_admin()
        profile_id = None
        if option != AUTOMATIC:
            profile_id = next(
                (
                    profile["id"]
                    for profile in self.runtime.document["profiles"]
                    if profile["name"] == option
                ),
                None,
            )
            if profile_id is None:
                raise HomeAssistantError("The selected profile does not exist")
        await self.runtime.async_set_profile(profile_id, self._context)

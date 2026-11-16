"""Expose the active profile and next boundary as native sensors."""

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SchedulerConfigEntry
from .entity import SchedulerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: SchedulerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            ActiveProfileSensor(entry.runtime_data, "active_profile"),
            NextChangeSensor(entry.runtime_data, "next_change"),
        ]
    )


class ActiveProfileSensor(SchedulerEntity, SensorEntity):
    """Report the selected profile name, independent of enablement."""

    _attr_icon = "mdi:calendar-account"

    @property
    def native_value(self) -> str | None:
        return next(
            (
                profile["name"]
                for profile in self.runtime.document["profiles"]
                if profile["id"] == self.runtime.active_profile
            ),
            None,
        )

    @property
    def extra_state_attributes(self) -> dict:
        return {"profile_id": self.runtime.active_profile, "last_error": self.runtime.last_error}


class NextChangeSensor(SchedulerEntity, SensorEntity):
    """Report the next scheduled recalculation boundary."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        return self.runtime.next_transition

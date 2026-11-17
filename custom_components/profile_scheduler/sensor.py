"""Expose the next boundary as a native sensor."""

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SchedulerConfigEntry
from .entity import SchedulerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: SchedulerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([NextChangeSensor(entry.runtime_data, "next_change")])


class NextChangeSensor(SchedulerEntity, SensorEntity):
    """Report the next scheduled recalculation boundary."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        return self.runtime.next_transition

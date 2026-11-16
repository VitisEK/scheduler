"""Shared native entity lifecycle and administrative controls."""

from homeassistant.exceptions import Unauthorized
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SIGNAL_UPDATED
from .runtime import SchedulerRuntime


class SchedulerEntity(Entity):
    """Represent the local scheduler as a logical service device."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, runtime: SchedulerRuntime, key: str) -> None:
        self.runtime = runtime
        self._attr_unique_id = f"{runtime.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, runtime.entry_id)},
            name="Profile Scheduler",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_UPDATED, self.async_write_ha_state)
        )

    async def async_check_admin(self) -> None:
        """Allow HA automations and administrators, not untrusted UI callers."""
        if user_id := self._context.user_id:
            user = await self.hass.auth.async_get_user(user_id)
            if user is None or not user.is_admin:
                raise Unauthorized

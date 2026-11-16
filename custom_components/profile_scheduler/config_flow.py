"""Configure the single local Profile Scheduler."""

from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .const import DOMAIN


class ProfileSchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up one scheduler from the UI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm creation without requiring YAML or credentials."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Profile Scheduler", data={})
        return self.async_show_form(step_id="user")

"""Config-flow tests for the single profile scheduler instance."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "profile_scheduler"


async def test_user_flow(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """Confirm the native UI flow creates an entry with no YAML configuration."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    with patch(
        "custom_components.profile_scheduler.async_setup_entry",
        new_callable=AsyncMock,
        return_value=True,
    ) as setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {}
    assert result["result"].unique_id is not None
    setup.assert_awaited_once()


async def test_duplicate_user_flow(hass: HomeAssistant, enable_custom_integrations: None) -> None:
    """A second entry cannot contend for the same sidebar panel or plan."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data={})
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    if result["type"] is FlowResultType.FORM:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

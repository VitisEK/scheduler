"""Administrative JSON API for the native sidebar panel."""

from typing import Any

import probatio as vol
from homeassistant.components import websocket_api
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .runtime import RevisionConflict, SchedulerRuntime


def _runtime(hass: HomeAssistant) -> SchedulerRuntime:
    runtime = hass.data.get(DOMAIN, {}).get("runtime")
    if runtime is None:
        raise HomeAssistantError("Profile Scheduler is not loaded")
    return runtime


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    """Register stable handlers once per HA process."""
    for handler in (websocket_get, websocket_save, websocket_set_profile, websocket_set_enabled):
        websocket_api.async_register_command(hass, handler)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get"})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_get(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    connection.send_result(msg["id"], _runtime(hass).snapshot())


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save",
        vol.Required("document"): dict,
        vol.Required("revision"): vol.All(int, vol.Range(min=0)),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_save(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _runtime(hass)
    try:
        await runtime.async_save(
            msg["document"], msg["revision"], Context(user_id=connection.user.id)
        )
    except RevisionConflict as err:
        connection.send_error(msg["id"], "conflict", str(err))
        return
    connection.send_result(msg["id"], runtime.snapshot())


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_profile",
        vol.Required("topic_id"): str,
        vol.Required("profile_id"): vol.Any(str, None),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_set_profile(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _runtime(hass)
    await runtime.async_set_profile(
        msg["topic_id"], msg["profile_id"], Context(user_id=connection.user.id)
    )
    connection.send_result(msg["id"], runtime.snapshot())


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/set_enabled", vol.Required("enabled"): bool}
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_set_enabled(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    runtime = _runtime(hass)
    await runtime.async_set_enabled(msg["enabled"], Context(user_id=connection.user.id))
    connection.send_result(msg["id"], runtime.snapshot())

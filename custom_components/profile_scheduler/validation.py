"""Validate storage documents and compile native Home Assistant actions."""

import json
import re
from copy import deepcopy
from typing import Any

import probatio as vol
from homeassistant.core import HomeAssistant, valid_entity_id
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.script import async_validate_actions_config

# Only known state setters can be restored automatically. Arbitrary actions,
# including scenes, scripts, toggles and waits, must use one-shot mode.
RESTORABLE = {
    "climate": {
        "set_temperature",
        "set_hvac_mode",
        "set_preset_mode",
        "set_fan_mode",
        "set_swing_mode",
        "turn_on",
        "turn_off",
    },
    "light": {"turn_on", "turn_off"},
    "switch": {"turn_on", "turn_off"},
    "input_boolean": {"turn_on", "turn_off"},
    "number": {"set_value"},
    "input_number": {"set_value"},
    "select": {"select_option"},
    "input_select": {"select_option"},
    "fan": {"turn_on", "turn_off", "set_percentage", "set_preset_mode"},
    "humidifier": {"turn_on", "turn_off", "set_humidity", "set_mode"},
    "water_heater": {"set_temperature", "set_operation_mode", "turn_on", "turn_off"},
}
IDENTIFIER = re.compile(r"^[a-zA-Z0-9_-]{1,80}$")
TIME = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def invalid(message: str) -> None:
    """Raise a message suitable for the administrative editor."""
    raise HomeAssistantError(message)


def _text(value: Any, label: str, maximum: int = 120) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        invalid(f"{label}: expected nonempty text up to {maximum} characters")
    return value


def _id(value: Any, seen: set[str], label: str) -> None:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value) or value in seen:
        invalid(f"{label}: invalid or duplicate ID")
    seen.add(value)


def _minute(value: Any, *, end: bool = False) -> int:
    if end and value == "24:00":
        return 1440
    if not isinstance(value, str) or not TIME.fullmatch(value):
        invalid("Time must be HH:MM; 24:00 is valid only as an end")
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def _restorable(actions: list[dict[str, Any]]) -> bool:
    for action in actions:
        if not isinstance(action, dict):
            return False
        service = action.get("action", action.get("service"))
        if not isinstance(service, str) or service.count(".") != 1:
            return False
        domain, name = service.split(".")
        if name not in RESTORABLE.get(domain, set()):
            return False
        if set(action) - {"action", "service", "target", "data", "alias", "enabled", "metadata"}:
            return False
        # Restorable operations need an explicit target. The HA action schema
        # performs detailed target/data validation, including template syntax.
        data = action.get("data", {})
        if not isinstance(data, dict):
            return False
        if domain == "light" and set(data).intersection(
            {"brightness_step", "brightness_step_pct", "flash"}
        ):
            return False
        if _has_template(action):
            return False
        if not action.get("target") and not data.get("entity_id"):
            return False
    return True


def _has_template(value: Any) -> bool:
    """Restore only literal targets/values; dynamic actions remain one-shots."""
    if isinstance(value, str):
        return "{{" in value or "{%" in value or "{#" in value
    if isinstance(value, dict):
        return any(_has_template(key) or _has_template(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_template(item) for item in value)
    return False


async def async_validate_document(
    hass: HomeAssistant, value: Any
) -> tuple[dict[str, Any], dict[tuple[str, str, str], list[dict[str, Any]]]]:
    """Return a JSON document plus separately compiled HA action sequences."""
    try:
        encoded = json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as err:
        raise HomeAssistantError("Plan must contain JSON values only") from err
    if len(encoded.encode()) > 1_000_000:
        invalid("Plan exceeds the 1 MB limit")
    document = deepcopy(value)
    if not isinstance(document, dict) or set(document) != {"enabled", "manual_profile", "profiles"}:
        invalid("Invalid plan document")
    if type(document["enabled"]) is not bool:
        invalid("enabled must be boolean")
    profiles = document["profiles"]
    if not isinstance(profiles, list) or len(profiles) > 32:
        invalid("Expected at most 32 profiles")
    profile_ids: set[str] = set()
    names: set[str] = set()
    compiled = {}
    total_blocks = 0
    for profile in profiles:
        if not isinstance(profile, dict) or set(profile) != {"id", "name", "weekdays", "rows"}:
            invalid("Invalid profile")
        _id(profile["id"], profile_ids, "Profile")
        name = _text(profile["name"], "Profile name")
        if name in names or name.casefold() == "automatic":
            invalid("Profile names must be unique and cannot be Automatic")
        names.add(name)
        days = profile["weekdays"]
        if (
            not isinstance(days, list)
            or any(type(day) is not int or day not in range(7) for day in days)
            or len(days) != len(set(days))
        ):
            invalid("weekdays must be unique integers from 0 to 6")
        rows = profile["rows"]
        if not isinstance(rows, list) or len(rows) > 100:
            invalid("Expected at most 100 rows per profile")
        row_ids: set[str] = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"id", "name", "entity_ids", "blocks"}:
                invalid("Invalid row")
            _id(row["id"], row_ids, "Row")
            _text(row["name"], "Row name")
            targets = row["entity_ids"]
            if (
                not isinstance(targets, list)
                or len(targets) > 100
                or any(
                    not isinstance(target, str) or not valid_entity_id(target) for target in targets
                )
            ):
                invalid("entity_ids must contain valid entity IDs")
            blocks = row["blocks"]
            if not isinstance(blocks, list) or len(blocks) > 100:
                invalid("Expected at most 100 blocks per row")
            block_ids: set[str] = set()
            occupied: list[tuple[int, int]] = []
            for block in blocks:
                total_blocks += 1
                if total_blocks > 2000:
                    invalid("Expected at most 2000 blocks")
                if not isinstance(block, dict) or set(block) != {
                    "id",
                    "start",
                    "end",
                    "mode",
                    "label",
                    "color",
                    "actions",
                }:
                    invalid("Invalid time block")
                _id(block["id"], block_ids, "Block")
                _text(block["label"], "Block label")
                if not isinstance(block["color"], str) or not COLOR.fullmatch(block["color"]):
                    invalid("Block color must be a six-digit hex color")
                start, end = _minute(block["start"]), _minute(block["end"], end=True)
                if start == end:
                    invalid("Empty block; use 00:00–24:00 for a full day")
                spans = [(start, end)] if start < end else [(start, 1440), (0, end)]
                if any(
                    max(left, old_left) < min(right, old_right)
                    for left, right in spans
                    for old_left, old_right in occupied
                ):
                    invalid("Time blocks in the same row must not overlap")
                occupied.extend(spans)
                if not isinstance(block["mode"], str) or block["mode"] not in {"state", "once"}:
                    invalid("Block mode must be state or once")
                actions = block["actions"]
                if not isinstance(actions, list) or not actions or len(actions) > 50:
                    invalid("A block needs 1 to 50 native Home Assistant actions")
                if block["mode"] == "state" and not _restorable(actions):
                    invalid(
                        "State mode accepts only repeatable state-setting actions with targets; use once for scenes, scripts and other actions"
                    )
                try:
                    normalized = await cv.async_validate(hass, cv.SCRIPT_SCHEMA, deepcopy(actions))
                    compiled[
                        (profile["id"], row["id"], block["id"])
                    ] = await async_validate_actions_config(hass, normalized)
                except (vol.Invalid, ValueError, HomeAssistantError) as err:
                    raise HomeAssistantError("Invalid Home Assistant action configuration") from err
    manual = document["manual_profile"]
    if manual is not None and (not isinstance(manual, str) or manual not in profile_ids):
        invalid("The manual profile does not exist")
    return document, compiled

"""Expose a dynamically managed profile selector for every topic."""

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SchedulerConfigEntry
from .const import DOMAIN, INACTIVE_OPTION, SIGNAL_UPDATED
from .entity import SchedulerEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: SchedulerConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runtime = entry.runtime_data
    entities: dict[str, SchedulerSelect] = {}

    @callback
    def reconcile() -> None:
        topics = {topic["id"]: topic for topic in runtime.document["topics"]}
        for topic_id in entities.keys() - topics.keys():
            entity = entities.pop(topic_id)
            registry = er.async_get(hass)
            assert entity.unique_id is not None
            entity_id = registry.async_get_entity_id("select", DOMAIN, entity.unique_id)
            if entity_id:
                registry.async_remove(entity_id)
        added = []
        for topic_id in topics.keys() - entities.keys():
            entity = SchedulerSelect(runtime, topic_id)
            entities[topic_id] = entity
            added.append(entity)
        if added:
            async_add_entities(added)

    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_UPDATED, reconcile))
    reconcile()


class SchedulerSelect(SchedulerEntity, SelectEntity):
    """Expose the selected profile and an inactive option for one topic."""

    _attr_icon = "mdi:calendar-account"
    _attr_translation_key = None

    def __init__(self, runtime, topic_id: str) -> None:
        super().__init__(runtime, f"topic_{topic_id}_profile")
        self.topic_id = topic_id
        self._attr_translation_key = None

    @property
    def topic(self) -> dict:
        return next((t for t in self.runtime.document["topics"] if t["id"] == self.topic_id), {})

    @property
    def name(self) -> str:
        return f"{self.topic.get('name', self.topic_id)} profile"

    @property
    def inactive_option(self) -> str:
        names = {profile["name"] for profile in self.topic.get("profiles", [])}
        option = INACTIVE_OPTION
        while option in names:
            option += "_"
        return option

    @property
    def options(self) -> list[str]:
        return [self.inactive_option, *(p["name"] for p in self.topic.get("profiles", []))]

    @property
    def current_option(self) -> str:
        return next(
            (
                p["name"]
                for p in self.topic.get("profiles", [])
                if p["id"] == self.topic.get("active_profile")
            ),
            self.inactive_option,
        )

    async def async_select_option(self, option: str) -> None:
        await self.async_check_admin()
        profile_id = None
        if option != self.inactive_option:
            profile_id = next(
                (p["id"] for p in self.topic.get("profiles", []) if p["name"] == option), None
            )
            if profile_id is None:
                raise HomeAssistantError("The selected profile does not exist")
        await self.runtime.async_set_profile(self.topic_id, profile_id, self._context)

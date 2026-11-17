"""Stored schedules, cancellable boundaries and native action execution."""

import asyncio
import logging
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.script import Script
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import ACTION_TIMEOUT, DOMAIN, SIGNAL_UPDATED, STORAGE_VERSION, default_document
from .engine import active_blocks, is_block_start, next_change, select_profile
from .validation import async_validate_document

_LOGGER = logging.getLogger(__name__)


class RevisionConflict(HomeAssistantError):
    """The client attempted to overwrite a newer plan."""


class SchedulerStore(Store[dict[str, Any]]):
    """Migrate legacy documents before Store commits the upgraded version."""

    migrated_automatic = False

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict[str, Any]
    ) -> dict[str, Any]:
        if (
            old_major_version != 1
            or not isinstance(old_data, dict)
            or set(old_data) != {"document", "revision"}
        ):
            raise HomeAssistantError("Unsupported Profile Scheduler storage version")
        old = old_data["document"]
        if (
            not isinstance(old, dict)
            or set(old) != {"enabled", "manual_profile", "profiles"}
            or not isinstance(old["profiles"], list)
        ):
            raise HomeAssistantError("Invalid legacy Profile Scheduler document")
        entities: list[dict[str, Any]] = []
        profiles: list[dict[str, Any]] = []
        used: set[str] = set()
        for profile_index, profile in enumerate(old["profiles"]):
            if (
                not isinstance(profile, dict)
                or set(profile) != {"id", "name", "weekdays", "rows"}
                or not isinstance(profile["rows"], list)
            ):
                raise HomeAssistantError("Invalid legacy profile")
            rows = []
            for row_index, row in enumerate(profile["rows"]):
                if not isinstance(row, dict) or set(row) != {"id", "name", "entity_ids", "blocks"}:
                    raise HomeAssistantError("Invalid legacy row")
                entity = {key: deepcopy(row[key]) for key in ("id", "name", "entity_ids")}
                existing = next((item for item in entities if item == entity), None)
                if existing is None:
                    if not isinstance(entity["id"], str):
                        raise HomeAssistantError("Invalid legacy row ID")
                    if entity["id"] in used:
                        candidate = f"migrated_{profile_index}_{row_index}"
                        while candidate in used:
                            candidate += "_x"
                        entity["id"] = candidate
                    used.add(entity["id"])
                    entities.append(entity)
                    existing = entity
                rows.append({"id": existing["id"], "blocks": deepcopy(row["blocks"])})
            profiles.append(
                {
                    "id": profile["id"],
                    "name": profile["name"],
                    "schedule_mode": "daily",
                    "schedules": {"all": rows},
                }
            )
        document = {
            "enabled": old["enabled"],
            "topics": [
                {
                    "id": "migrated",
                    "name": "Migrated",
                    "entities": entities,
                    "active_profile": old["manual_profile"],
                    "profiles": profiles,
                }
            ],
        }
        if type(old_data["revision"]) is not int or old_data["revision"] < 0:
            raise HomeAssistantError("Invalid legacy revision")
        validated, _ = await async_validate_document(self.hass, document)
        self.migrated_automatic = old["manual_profile"] is None
        return {"document": validated, "revision": old_data["revision"]}


class SchedulerRuntime:
    """Own one scheduler document and its lifecycle resources."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.store = SchedulerStore(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")
        self.document = default_document()
        self.revision = 0
        self.active_profile: dict[str, str | None] = {}
        self.next_transition: datetime | None = None
        self.last_error: str | None = None
        self._compiled: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
        self._timer: Callable[[], None] | None = None
        self._tasks: dict[asyncio.Task[None], tuple[str, Context]] = {}
        self._active_keys: set[str] = set()
        self._generation = 0
        self._started = False
        self._closed = False
        self.context = Context()

    async def async_load(self) -> None:
        """Read and validate data before enabling any execution."""
        stored = await self.store.async_load()
        if self.store.migrated_automatic:
            persistent_notification.async_create(
                self.hass,
                "Your previous automatic weekday profile selection could not be preserved. "
                "The migrated topic is inactive; select a profile for it to resume scheduling.",
                title="Profile Scheduler migration",
                notification_id=f"profile_scheduler_migration_{self.entry_id}",
            )
        if stored is not None:
            if (
                not isinstance(stored, dict)
                or set(stored) != {"document", "revision"}
                or type(stored["revision"]) is not int
                or stored["revision"] < 0
            ):
                raise HomeAssistantError("Invalid Profile Scheduler storage")
            self.document, self._compiled = await async_validate_document(
                self.hass, stored["document"]
            )
            self.revision = stored["revision"]
        else:
            self.document, self._compiled = await async_validate_document(self.hass, self.document)

    def snapshot(self) -> dict[str, Any]:
        """Return isolated JSON values for the panel."""
        return {
            "document": deepcopy(self.document),
            "revision": self.revision,
            "active_profile": deepcopy(self.active_profile),
            "next_change": self.next_transition.isoformat() if self.next_transition else None,
            "last_error": self.last_error,
        }

    @callback
    def _notify(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATED)

    async def async_start(self) -> None:
        """Restore only the currently active state, never historical one-shots."""
        if self._closed or self._started:
            return
        self._started = True
        await self.async_evaluate(recover=True)

    async def _cancel_work(self, *, wait: bool = True, topic_id: str | None = None) -> None:
        self._generation += 1
        if self._timer is not None:
            self._timer()
            self._timer = None
        current = asyncio.current_task()
        tasks = [
            task
            for task, (owner, _) in self._tasks.items()
            if task is not current and not task.done() and (topic_id is None or owner == topic_id)
        ]
        for task in tasks:
            task.cancel()
        if tasks and wait:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def async_stop(self) -> None:
        """Block new execution immediately, then cancel pending callbacks/runs."""
        self._closed = True
        self._started = False
        async with self._lock:
            await self._cancel_work()
            self.next_transition = None

    async def _replace(
        self,
        document: dict[str, Any],
        revision: int | None,
        context: Context | None,
        topic_id: str | None = None,
    ) -> None:
        if self._closed:
            raise HomeAssistantError("Scheduler is unloaded")
        if revision is not None and revision != self.revision:
            raise RevisionConflict("Plan changed in another editor; reload before saving")
        validated, compiled = await async_validate_document(self.hass, document)
        # Persist before replacing the running plan. Failed writes leave the
        # previous schedule intact and surface to the caller.
        next_revision = self.revision + 1
        await self.store.async_save({"document": validated, "revision": next_revision})
        # A scheduled action may operate our own switch/select. Its service
        # task is awaited by the Script task we are cancelling. Waiting for
        # that Script here would deadlock; let it clean up after this service
        # returns. Generation invalidation and cancellation happen immediately.
        self_control = context is not None and any(
            not task.done() and (context.id == origin.id or context.parent_id == origin.id)
            for task, (_, origin) in self._tasks.items()
        )
        previous_due = self.next_transition if topic_id is not None else None
        await self._cancel_work(wait=not self_control, topic_id=topic_id)
        self.document, self._compiled = validated, compiled
        self.revision = next_revision
        self.context = Context(parent_id=context.id if context else None)
        if topic_id is None:
            self._active_keys.clear()
        else:
            self._active_keys = {
                key for key in self._active_keys if not key.startswith(f"{topic_id}:")
            }
        self.last_error = None
        await self._evaluate_locked(
            recover=True, due=previous_due, cancel_running=False, recover_topic=topic_id
        )

    async def async_save(
        self, document: dict[str, Any], revision: int, context: Context | None = None
    ) -> None:
        """Validate and atomically replace the complete structured plan."""
        async with self._lock:
            await self._replace(document, revision, context)

    async def async_set_profile(
        self, topic_id: str, profile_id: str | None, context: Context | None = None
    ) -> None:
        """Select a profile independently for one topic."""
        async with self._lock:
            document = deepcopy(self.document)
            topic = next((t for t in document["topics"] if t["id"] == topic_id), None)
            if topic is None:
                raise HomeAssistantError("The topic does not exist")
            if profile_id is not None and not any(p["id"] == profile_id for p in topic["profiles"]):
                raise HomeAssistantError("The profile does not exist in this topic")
            if topic["active_profile"] == profile_id:
                return
            topic["active_profile"] = profile_id
            await self._replace(document, None, context, topic_id)

    async def async_set_enabled(self, enabled: bool, context: Context | None = None) -> None:
        """Enable/disable and persist the scheduler."""
        async with self._lock:
            if enabled == self.document["enabled"]:
                return
            document = deepcopy(self.document)
            document["enabled"] = enabled
            await self._replace(document, None, context)

    async def async_evaluate(
        self,
        recover: bool = False,
        due: datetime | None = None,
        *,
        expected_generation: int | None = None,
    ) -> None:
        """Reconcile current state at an injected/frozen HA time."""
        async with self._lock:
            if self._closed or (
                expected_generation is not None and expected_generation != self._generation
            ):
                return
            await self._evaluate_locked(recover=recover, due=due)

    async def _evaluate_locked(
        self,
        recover: bool,
        due: datetime | None = None,
        *,
        cancel_running: bool = True,
        recover_topic: str | None = None,
    ) -> None:
        if self._closed:
            return
        now = dt_util.as_local(dt_util.utcnow())
        selected_topics = [(topic, select_profile(topic, now)) for topic in self.document["topics"]]
        self.active_profile = {
            topic["id"]: profile["id"] if profile else None for topic, profile in selected_topics
        }
        if not self._started or not self.document["enabled"]:
            self.next_transition = None
            self._active_keys.clear()
            self._notify()
            return
        recover_state = recover
        if cancel_running:
            await self._cancel_work()
        generation = self._generation
        active = []
        for topic, profile in selected_topics:
            if profile is not None:
                for row, block, occurrence in active_blocks(profile, now):
                    day = occurrence.split(":", 1)[0]
                    name = next(
                        entity["name"] for entity in topic["entities"] if entity["id"] == row["id"]
                    )
                    active.append(
                        (
                            topic["id"],
                            profile["id"],
                            day,
                            row,
                            block,
                            f"{topic['id']}:{profile['id']}:{occurrence}",
                            name,
                        )
                    )
        due_local = dt_util.as_local(due) if due is not None else None
        timely = due is not None and timedelta(0) <= dt_util.as_utc(now) - dt_util.as_utc(
            due
        ) < timedelta(minutes=1)
        for topic_id, profile_id, day, row, block, occurrence, name in active:
            if block["mode"] == "state":
                should_run = (
                    recover_state and (recover_topic is None or topic_id == recover_topic)
                ) or occurrence not in self._active_keys
            else:
                should_run = (
                    (not recover or (recover_topic is not None and topic_id != recover_topic))
                    and timely
                    and occurrence not in self._active_keys
                    and due_local is not None
                    and is_block_start(block, due_local)
                )
            if should_run:
                actions = self._compiled[(topic_id, profile_id, day, row["id"], block["id"])]
                action_context = Context(parent_id=self.context.id)
                task = self.hass.async_create_background_task(
                    self._execute(actions, name, action_context),
                    f"{DOMAIN}:action:{row['id']}:{block['id']}",
                )
                self._tasks[task] = (topic_id, action_context)
                task.add_done_callback(lambda done: self._tasks.pop(done, None))
        self._active_keys = {occurrence for _, _, _, _, _, occurrence, _ in active}
        self.next_transition = next_change(self.document, now)
        if self.next_transition is not None:
            scheduled = self.next_transition

            async def boundary(_: datetime) -> None:
                if not self._closed and generation == self._generation:
                    await self.async_evaluate(due=scheduled, expected_generation=generation)

            self._timer = async_track_point_in_utc_time(self.hass, boundary, scheduled)
        self._notify()

    async def _execute(self, actions: list[dict[str, Any]], name: str, context: Context) -> None:
        if self._closed:
            return
        script = Script(self.hass, deepcopy(actions), name, DOMAIN, log_exceptions=False)
        try:
            async with asyncio.timeout(ACTION_TIMEOUT):
                await script.async_run(context=context)
        except asyncio.CancelledError:
            raise
        except Exception as err:
            # Do not include payloads or template-expanded service data in logs.
            self.last_error = (
                f"Action failed ({type(err).__name__}); check the selected action and target"
            )
            _LOGGER.warning("Profile Scheduler action failed (%s)", type(err).__name__)
            self._notify()
        finally:
            try:
                await script.async_unload()
            except Exception as err:
                self.last_error = f"Action cleanup failed ({type(err).__name__})"
                _LOGGER.warning("Profile Scheduler action cleanup failed (%s)", type(err).__name__)
                self._notify()

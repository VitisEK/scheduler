"""Stored schedules, cancellable boundaries and native action execution."""

import asyncio
import logging
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

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


class SchedulerRuntime:
    """Own one scheduler document and its lifecycle resources."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")
        self.document = default_document()
        self.revision = 0
        self.active_profile: str | None = None
        self.next_transition: datetime | None = None
        self.last_error: str | None = None
        self._compiled: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
        self._timer: Callable[[], None] | None = None
        self._tasks: set[asyncio.Task[None]] = set()
        self._active_keys: set[str] = set()
        self._generation = 0
        self._started = False
        self._closed = False
        self.context = Context()

    async def async_load(self) -> None:
        """Read and validate data before enabling any execution."""
        stored = await self.store.async_load()
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
            "active_profile": self.active_profile,
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

    async def _cancel_work(self, *, wait: bool = True) -> None:
        self._generation += 1
        if self._timer is not None:
            self._timer()
            self._timer = None
        current = asyncio.current_task()
        tasks = [task for task in self._tasks if task is not current and not task.done()]
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
        self, document: dict[str, Any], revision: int | None, context: Context | None
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
        self_control = context is not None and (
            context.id == self.context.id or context.parent_id == self.context.id
        )
        await self._cancel_work(wait=not self_control)
        self.document, self._compiled = validated, compiled
        self.revision = next_revision
        self.context = Context(parent_id=context.id if context else None)
        self._active_keys.clear()
        self.last_error = None
        await self._evaluate_locked(recover=True, cancel_running=False)

    async def async_save(
        self, document: dict[str, Any], revision: int, context: Context | None = None
    ) -> None:
        """Validate and atomically replace the complete structured plan."""
        async with self._lock:
            await self._replace(document, revision, context)

    async def async_set_profile(
        self, profile_id: str | None, context: Context | None = None
    ) -> None:
        """Set a manual override, or return to weekday-based selection."""
        async with self._lock:
            if profile_id == self.document["manual_profile"]:
                return
            document = deepcopy(self.document)
            document["manual_profile"] = profile_id
            await self._replace(document, None, context)

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
        self, recover: bool, due: datetime | None = None, *, cancel_running: bool = True
    ) -> None:
        if self._closed:
            return
        now = dt_util.as_local(dt_util.utcnow())
        profile = select_profile(self.document, now)
        selected = profile["id"] if profile is not None else None
        profile_changed = selected != self.active_profile
        self.active_profile = selected
        if not self._started or not self.document["enabled"]:
            self.next_transition = None
            self._active_keys.clear()
            self._notify()
            return
        if profile_changed:
            recover = True
        if cancel_running:
            await self._cancel_work()
        generation = self._generation
        active = active_blocks(profile, now) if profile is not None else []
        due_local = dt_util.as_local(due) if due is not None else None
        timely = due is not None and timedelta(0) <= dt_util.as_utc(now) - dt_util.as_utc(
            due
        ) < timedelta(minutes=1)
        for row, block, occurrence in active:
            if block["mode"] == "state":
                should_run = recover or occurrence not in self._active_keys
            else:
                should_run = (
                    not recover
                    and timely
                    and occurrence not in self._active_keys
                    and due_local is not None
                    and is_block_start(block, due_local)
                )
            if should_run:
                assert selected is not None
                actions = self._compiled[(selected, row["id"], block["id"])]
                task = self.hass.async_create_background_task(
                    self._execute(actions, generation, row["name"]),
                    f"{DOMAIN}:action:{row['id']}:{block['id']}",
                )
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        self._active_keys = {occurrence for _, _, occurrence in active}
        self.next_transition = next_change(self.document, now)
        if self.next_transition is not None:
            scheduled = self.next_transition

            async def boundary(_: datetime) -> None:
                if not self._closed and generation == self._generation:
                    await self.async_evaluate(due=scheduled, expected_generation=generation)

            self._timer = async_track_point_in_utc_time(self.hass, boundary, scheduled)
        self._notify()

    async def _execute(self, actions: list[dict[str, Any]], generation: int, name: str) -> None:
        if self._closed or generation != self._generation:
            return
        script = Script(self.hass, deepcopy(actions), name, DOMAIN, log_exceptions=False)
        try:
            async with asyncio.timeout(ACTION_TIMEOUT):
                await script.async_run(context=self.context)
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

# Scheduler: agent instructions

## Project and communication

- Build the `profile_scheduler` custom Home Assistant integration for scheduling actions. Implementation lives in `custom_components/profile_scheduler`, with tests in `tests` and CI in `.github/workflows`.
- Reply to the user in Czech. Use English for Python identifiers, code comments, commit messages, and agent instructions.
- Read `docs/DEVELOPMENT.md` before implementing code. Keep its environment commands and project status accurate as tooling is introduced.
- `scheduler` is the repository name; `profile_scheduler` is the integration domain. See the domain decision in `docs/DEVELOPMENT.md`; keep persisted IDs and storage keys stable.
- Verify version-sensitive APIs against official Home Assistant documentation and the selected HA version. Do not copy private HA internals or stale integration templates.

## Working together

- The main agent owns the task, interfaces, integration of changes, and final verification.
- For substantial features, delegate bounded, independent work to the roles in `.codex/agents/`: `ha_architect`, `scheduler_engine`, `ha_integration`, `ha_tests`, `ha_reviewer`. Use one agent for small changes.
- Before delegation, provide the goal, acceptance criteria, relevant decisions, exact file ownership, and expected output. Agree interfaces before parallel implementation.
- Run at most three subagents concurrently, subject to the current session limit. Do not recursively delegate. Avoid concurrent edits to the same files; the main agent owns shared configuration, dependencies, and migrations unless explicitly assigned otherwise.
- Architectural exploration and review are non-editing tasks by instruction. They do not have a separate sandbox. All agents follow current permissions.
- Require each delegate to report changed files, decisions, commands and results, and remaining risks. The main agent reviews the combined diff and resolves failures before completion.
- Request an independent `ha_reviewer` pass for changes to scheduling, persistence, migrations, or action execution. Fix material findings and rerun affected checks.

## Home Assistant implementation

- Keep deterministic recurrence/time calculations separate from HA lifecycle, storage, and action dispatch. Inject the current time into calculations.
- Use async HA APIs and supported event/time helpers; avoid blocking I/O, `time.sleep`, and a permanent polling loop when a scheduled callback suffices.
- Use config entries and a UI config flow. Store per-entry runtime objects in typed `ConfigEntry.runtime_data` when supported by the target version. Use a coordinator only when shared data fetching warrants one.
- Register callbacks, subscriptions, tasks, and cleanup with the appropriate entry/entity lifecycle. Unloading, disabling, removing, or reloading an entry must cancel outstanding work and prevent stale action dispatch. Handle partial setup failures.
- Keep stable unique IDs independent of editable names. Validate action targets and data through supported HA mechanisms; report actionable errors without swallowing exceptions.
- Use HA storage helpers for persisted schedules, with explicit schema versions and migrations. Keep configuration and runtime state separate. Never edit a user's `.storage` files directly.
- Add manifest metadata, config-flow strings, and English/Czech translations as features are introduced. Document services/actions and validate their schemas.
- Use the Integration Quality Scale as a checklist where applicable, without claiming a tier or HACS compatibility that has not been verified.

## Scheduler correctness

- Before implementing relevant behavior, record the selected semantics in `docs/DEVELOPMENT.md`: recurrence, timezone, DST gaps/folds, overnight periods, overlap, missed runs, and concurrent action execution. Ask about decisions that materially change user-visible behavior while continuing independent work.
- Distinguish local calendar recurrence from elapsed durations. Use timezone-aware instants and UTC for ordering/persisted instants; preserve the IANA timezone and wall-clock rule for recurring schedules. Use the configured HA timezone, never the host timezone implicitly.
- Test nonexistent and repeated local times, midnight, week/year boundaries, leap days, clock jumps, timezone changes, and exact due-time boundaries when affected.
- Define missed-run behavior on startup and resume; never silently replay a backlog of device actions. Document the default before enabling execution.
- Prevent duplicate dispatch from duplicate callbacks or reloads. Invalidate stale callbacks when schedules change. Do not promise exactly-once execution across crashes unless a durable protocol actually provides it.
- Define action overlap, cancellation, timeout, and failure behavior. Retrying an action that may already have taken effect requires explicit semantics.
- Persist only necessary data. Never log credentials, access tokens, or full sensitive action payloads. Use synthetic fixtures; do not operate real HA devices for automated verification.

## Verification and delivery

- Before code exists, validate changed TOML/Markdown and inspect the diff; do not report pytest, hassfest, or integration tests as passed.
- When introducing code, establish a compatible Python/HA test environment and reproducible dependency versions first. Use Ruff, pytest, and `pytest-homeassistant-custom-component`; configure type checking for project code with a compatible HA environment.
- Test observable behavior with HA fixtures, frozen/controlled time, and mocked action dispatch. Do not wait for wall-clock time or patch the entire HA lifecycle away.
- Cover config-flow branches, setup/unload/reload, persistence/restart/migration, and scheduler edge cases affected by the change. Add a regression test for a behavioral bug.
- Run focused tests while iterating and the configured checks before delivery. On Linux CI, add hassfest when a manifest exists and HACS validation only when HACS distribution is selected.
- Preserve unrelated work. Do not deploy to a live HA instance, publish releases, or change remote repository settings unless the user requested that work.
- Finish with what changed, verification performed, and any unverified behavior. A configured role is not evidence that it has run.

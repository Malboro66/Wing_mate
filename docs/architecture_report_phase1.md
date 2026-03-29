# Phase 1 — Architecture Analysis (Short Report)

## Current modules observed
- **UI-heavy modules** under `app/ui/*` handle rendering and part of business orchestration.
- **Application services** in `app/application/*` already provide partial DI and coordination.
- **Infrastructure access** (JSON, SQLite, external cache) under `app/infrastructure/*`.
- **Cross-cutting concerns** in `utils/*` (observability, cache, notifications, file operations).

## Main dependencies
- PyQt5 (desktop UI)
- diskcache (persistent cache)
- sqlite3 (standard lib)
- pytest + pytest-qt (testing)

## Architectural pain points
1. **UI + orchestration coupling**: tabs/windows call data logic directly in several flows.
2. **Domain model fragmentation**: mission/pilot/squadron concepts spread across parsers/viewmodels and dict payloads.
3. **Infrastructure leakage**: persistence details can cross boundaries into application/UI flows.
4. **Event flow inconsistencies**: Qt signals coexist with direct calls without a central internal event bus.
5. **Bootstrap concerns mixed** in startup/runtime module.

## Refactoring direction
- Introduce **new `wingmate/` architecture layers** incrementally while keeping legacy runtime intact.
- Add **domain entities + repository interfaces + use-case contracts** first.
- Add **analytics engine and pipeline contracts** next, then adapters to legacy modules.

# WingMate Migration Strategy (Incremental)

1. Introduce new layered scaffold under `wingmate/`.
2. Add domain entities and value objects.
3. Add repository interfaces and adapters.
4. Add analytics engine contracts and reports.
5. Add use-case orchestration classes.
6. Introduce event bus + service container.
7. Add bootstrap app factory and keep legacy startup bridge.
8. Gradually migrate existing `app/*` modules to consume new layers.
9. Decommission legacy direct couplings after parity validation.

This repository currently remains backward-compatible with the existing runtime while the migration is in progress.

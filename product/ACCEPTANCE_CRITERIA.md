# Acceptance criteria

The deterministic definition of done for the whole product.

Rules:
- One row per objectively testable condition. Derived from `specs/*/spec.md` acceptance scenarios and success criteria.
- `Verify` is a single shell command in backticks that exits 0 only when the criterion holds. No pipes (`|`) in the command; wrap complex checks in a script under `scripts/` or a test file.
- `Status`: `todo` | `done` | `deferred` | `blocked`.
- `done` rows are regression-locked: CI fails if they stop passing.
- Only the planner adds rows. Builders flip `todo` to `done` after the verify command passes. Nobody weakens a verify command.
- The product is DONE when `python3 scripts/check_acceptance.py --strict` passes on `main`.

<!-- AC-TABLE:START -->
| ID | Feature | Criterion | Verify | Status |
|---|---|---|---|---|
| AC-000 | harness | Quality gate passes (build, lint, types, unit, integration, E2E) | `bash scripts/verify.sh` | done |
<!-- AC-TABLE:END -->

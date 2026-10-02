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
| ID | Feature | Criterion | Verify | Status | Journey |
|---|---|---|---|---|---|
| AC-000 | harness | Quality gate passes (build, lint, types, unit, integration, E2E) | `bash scripts/verify.sh` | done | |
| AC-001 | harness | Acceptance parser supports legacy tables and optional Journey cells | `python3 scripts/tests/test_check_acceptance.py` | done | |
| AC-002 | harness | App run contract skips cleanly or reports unhealthy startup with log tail | `python3 scripts/tests/test_serve.py` | done | |
<!-- AC-TABLE:END -->

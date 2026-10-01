# Copilot instructions

Read `AGENTS.md` first. It is binding. This file is the quick reference; sections marked `ONBOARD` are filled in by the harness onboarding task and must reflect the real repo.

## What this application does
See `product/PRODUCT.md`. <!-- ONBOARD: one-paragraph summary -->

## Architecture and important directories
See `product/ARCHITECTURE.md`.
<!-- ONBOARD: list the 5-10 directories that matter and what each owns -->
- `product/`: source of truth for requirements and state
- `specs/`: spec-kit feature specs (`spec.md`, `plan.md`, `tasks.md`)
- `scripts/verify.sh`: the single quality gate
- `scripts/check_acceptance.py`: runs every acceptance criterion
- `.github/agents/`: planner, builder, test-engineer, reviewer
- `.github/hooks/`: deterministic guardrails
- `.github/workflows/*.md`: agentic workflows (compiled to `.lock.yml`, never edit lock files)

## Stack and commands
<!-- ONBOARD: replace every "auto" with the exact command -->
| Purpose | Command |
|---|---|
| Package manager | auto (detected from lockfile) |
| Setup | auto |
| Dev server / start app | auto |
| App run contract | `product/RUN.md` (planner fills for UI/API apps; `SERVE_MODE=none` for libraries/CLIs) |
| Lint | auto |
| Format check | auto |
| Type check | auto |
| Unit tests | auto |
| Integration tests | auto |
| E2E tests | auto (Playwright) |
| Build | auto |
| **Validate everything** | `bash scripts/verify.sh` (or `npm run verify`) |
| **Acceptance criteria** | `python3 scripts/check_acceptance.py` |

## Coding conventions
<!-- ONBOARD: naming, error handling, logging, file layout, test placement -->
- Match the surrounding code before inventing a pattern.
- Tests next to code for unit, `tests/integration/` for integration, `e2e/` for Playwright.
- E2E tests cover real user journeys (create, edit, delete, permissions, error states), not "page loads".

## How to validate a change
1. `bash scripts/verify.sh`
2. `python3 scripts/check_acceptance.py`
3. Start the app and exercise the changed journey (Playwright or curl) when UI/API behaviour changed.
4. For UI/API changes, configure and use `bash scripts/serve.sh`, then run the affected AC Journeys with Playwright before marking the PR ready.

## Security constraints
No secrets in code or logs. No `.env` reads. No prod access. No weakening auth or tests to go green. Full list in `AGENTS.md`.

## Behaviour
Act autonomously on routine engineering decisions. Do not stop to ask questions the repo, docs, tests or conventions can answer. Pick the conventional reversible option, record it in `product/DECISIONS.md`, keep going. Escalate only genuine external blockers (see `AGENTS.md`).

## Definition of done
`verify.sh` green, `check_acceptance.py` green, ACs flipped to `done` with real verify commands, `PROGRESS.md` and `tasks.md` updated. Anything less: say what is missing in the PR.

# Harness onboarding (existing repository)

Run by the planner for a "Harness onboarding" issue. Goal: make this repo's harness reflect reality. Do NOT rewrite the product.

## 1. Inspect first (write findings into the PR description)
- Framework(s), language(s), package manager (lockfile), monorepo layout
- Build, dev/start, lint, format, typecheck, unit, integration, E2E commands (read `package.json` scripts / `pyproject.toml` / `Makefile` / CI files)
- Existing tests and where they live; coverage of critical journeys
- Deployment config (Dockerfile, IaC, Vercel/Azure/Fly config) and which workflows deploy
- Existing `.github/` config: workflows, issue templates, CODEOWNERS, copilot instructions, agents
- Existing docs that already describe product or architecture

## 2. Reconcile, reuse, do not duplicate
- Existing product/architecture docs: move or link them into `product/PRODUCT.md` / `product/ARCHITECTURE.md` so there is ONE source of truth. Delete nothing a human wrote; replace it with a pointer if moved.
- Existing CI: keep it. If it already runs build/lint/test on PRs, make `gate.yml` call `scripts/verify.sh` only for what is missing, or make the existing workflow call `scripts/verify.sh` and delete the duplicate job. Never run the same suite twice.
- Existing deploy workflows: leave them. Ensure none runs on agent branches.

## 3. Make it concrete
- Fill every `ONBOARD` section of `.github/copilot-instructions.md` with exact commands.
- Replace auto-detection in `scripts/verify.sh` with the exact commands if detection is wrong or incomplete. Keep it the single entry point. Add `"verify": "bash scripts/verify.sh"` to `package.json` scripts if Node.
- Update `copilot-setup-steps.yml` so the agent sandbox has every tool `verify.sh` needs.
- `git update-index --chmod=+x scripts/*.sh scripts/hooks/* .specify/scripts/bash/*.sh`
- Web app without E2E: add Playwright with ONE real critical journey test now; list the rest as tasks.

## 4. Capture the product as it is
- `product/PRODUCT.md`: users, journeys, features, inferred from code, routes, UI and docs. Mark inferences `(inferred)`.
- `product/ACCEPTANCE_CRITERIA.md`: rows for behaviour that EXISTS and is tested (`done`), exists but is untested (`todo`, verify points at a test to write), and is clearly intended but missing (`todo`).
- `product/PROGRESS.md`: done / remaining based on the above.
- `.specify/memory/constitution.md`: adapt principles to the real stack.

## 5. Prove it
`bash scripts/verify.sh` and `python3 scripts/check_acceptance.py` pass on the PR. Pre-existing failures are recorded as `todo` ACs plus issues in the PR description, not hidden.

## 6. Stop
Open the PR. List repo settings the human must enable (see README). Do not start feature work.

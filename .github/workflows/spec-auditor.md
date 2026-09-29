---
name: Spec Auditor
description: Daily audit for drift between product docs, acceptance criteria, tests and code. Files deduplicated follow-up task issues for real gaps.
on:
  schedule: daily
  workflow_dispatch:
permissions:
  contents: read
  issues: read
  pull-requests: read
  copilot-requests: write
engine: copilot
timeout-minutes: 20
tools:
  github:
    toolsets: [default]
  bash: true
safe-outputs:
  create-issue:
    title-prefix: "[audit] "
    labels: [agent-task]
    max: 3
---

# Spec Auditor

Read `AGENTS.md`, `product/*.md`, `specs/*/`, and the code. Find the three most important REAL gaps, preferring:

1. `done` ACs whose verify test would still pass if the feature were removed (asserts on mocks, trivial assertions).
2. Spec acceptance scenarios, error states or journeys with no AC row or no test.
3. TODO / FIXME / stub / placeholder / mock code in production paths.
4. `product/PROGRESS.md` or `tasks.md` checkboxes that contradict the code or the AC table.
5. Critical user journeys in `product/PRODUCT.md` with no Playwright coverage.

For each gap: search ALL issues (open and closed) for the same file/AC first; skip if covered. Create an issue using the task format in `AGENTS.md` (CONTEXT, REQUIREMENT, ACCEPTANCE CRITERIA, DEPENDENCIES, FILES/COMPONENTS, VERIFICATION) with concrete evidence (file:line).

No gaps worth fixing: noop. Never file style nits.

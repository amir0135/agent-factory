---
name: CI Doctor
description: When the gate fails, diagnoses the root cause from logs and sends a precise fix request back to the Copilot agent that owns the branch; opens a task issue for failures on main.
on:
  workflow_run:
    workflows: ["gate"]
    types: [completed]
    conclusion: [failure]
  roles: all
permissions:
  contents: read
  actions: read
  issues: read
  pull-requests: read
  copilot-requests: write
engine: copilot
timeout-minutes: 15
tools:
  github:
    toolsets: [default, actions]
safe-outputs:
  add-comment:
    target: "*"
    max: 1
    github-token: ${{ secrets.GH_AW_AGENT_TOKEN }}
  add-labels:
    allowed: [stuck]
    target: "*"
    max: 1
  create-issue:
    title-prefix: "[ci] "
    labels: [agent-task, bug]
    max: 1
---

# CI Doctor

The `gate` workflow run ${{ github.event.workflow_run.id }} failed on branch `${{ github.event.workflow_run.head_branch }}` at `${{ github.event.workflow_run.head_sha }}`.

1. Fetch the failed jobs' logs. Identify the FIRST real failure (not cascading ones). Classify: compile/type, lint/format, unit test, integration, E2E, acceptance regression (a `done` AC now fails), secret scan, dependency/audit, infrastructure/flake.
2. Find the root cause: read the failing test and the code it exercises at that SHA. Quote the key log lines (max 20).
3. If an open PR has this head SHA and it was authored by Copilot:
   - Count earlier CI Doctor comments on that PR (they start with `@copilot CI Doctor`). If there are already 3, add label `stuck` and stop.
   - Otherwise comment, starting exactly with `@copilot CI Doctor:` then: root cause, evidence (file:line, log excerpt), the specific fix, and the command to prove it (`bash scripts/verify.sh`). Remind: do not skip or weaken tests.
4. If the branch is `main`: search open issues titled `[ci]` for the same failure; if none, create one with the diagnosis, sections as in AGENTS.md task format, AC `AC-000`.
5. If the failure is infrastructure or flake with clear evidence (network timeout, runner error): say so in the comment and ask Copilot to push an empty re-run commit only if nothing else is wrong.
6. Otherwise noop. Never approve, never merge.

---
name: Feature Intake
description: Hands feature requests, onboarding and re-plan issues to the planner custom agent.
on:
  issues:
    types: [opened, labeled]
permissions:
  contents: read
  issues: read
  copilot-requests: write
engine: copilot
tools:
  github:
    toolsets: [default]
safe-outputs:
  assign-to-agent:
    name: copilot
    custom-agent: planner
    target: triggering
    max: 1
    github-token: ${{ secrets.GH_AW_AGENT_TOKEN }}
  add-comment:
    max: 1
---

# Feature Intake

Issue #${{ github.event.issue.number }} was opened or labeled.

Proceed ONLY if the issue currently has one of the labels `feature`, `onboard`, or `needs-replan`, is open, and is not already assigned to Copilot. Otherwise do nothing (noop).

If it qualifies:
1. Assign it to Copilot with the `planner` custom agent (assign-to-agent, triggering issue).
2. Add one short comment stating which planner mode applies: `feature` -> Mode A (idea to specs, ACs, tasks), `onboard` -> Mode B (harness onboarding), `needs-replan` -> Mode C (split or fix a stuck task).

Do not ask the author clarifying questions. The planner resolves routine ambiguity itself and escalates only genuine blockers.

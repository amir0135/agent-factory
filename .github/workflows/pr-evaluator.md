---
name: PR Evaluator
description: Independent evidence-based evaluation of Copilot PRs against acceptance criteria after the gate passes. Stamps a verdict for the exact head SHA; PASS enables auto-merge, FAIL sends numbered fixes back to Copilot.
on:
  workflow_run:
    workflows: ["gate"]
    types: [completed]
    conclusion: [success]
    branches: ["copilot/**"]
  roles: all
permissions:
  contents: read
  actions: read
  issues: read
  pull-requests: read
  copilot-requests: write
engine: copilot
timeout-minutes: 20
tools:
  github:
    toolsets: [default, actions]
  bash: true
safe-outputs:
  add-comment:
    target: "*"
    max: 1
    github-token: ${{ secrets.GH_AW_AGENT_TOKEN }}
  add-labels:
    allowed: [eval:pass, eval:fail, stuck]
    target: "*"
    max: 2
  remove-labels:
    allowed: [eval:pass, eval:fail]
    target: "*"
    max: 2
---

# PR Evaluator

The gate passed for commit `${{ github.event.workflow_run.head_sha }}`.

Find the open pull request whose head SHA is exactly that commit. Stop (noop) if: there is none, it is a draft, it was not authored by Copilot, or it already has an evaluator comment containing `Evaluated-SHA: ${{ github.event.workflow_run.head_sha }}`.

Otherwise act as the reviewer defined in `.github/agents/reviewer.agent.md` (read it now and follow it exactly). Also read `AGENTS.md`, the linked issue, the AC rows it names in `product/ACCEPTANCE_CRITERIA.md`, and the spec scenarios they come from. Inspect the full diff including tests. Trust nothing the PR description claims without evidence in the diff or CI logs.

Automatic FAIL: deleted/skipped/loosened tests, edited verify commands, disabled lint/type rules, TODO/stub/mock in a production path, missing required error states, AC flipped to done without a test that would fail without the change, `product/PROGRESS.md` not updated.

Output ONE comment in exactly this shape:

```
<!-- evaluator -->
VERDICT: PASS | FAIL
Evaluated-SHA: ${{ github.event.workflow_run.head_sha }}
Evidence:
- AC-xxx: PASS/FAIL - <evidence>
```

- PASS: remove `eval:fail`, add `eval:pass`. Do not mention @copilot.
- FAIL: remove `eval:pass`, add `eval:fail`. Start the comment with `@copilot` on its own first line and add `Required fixes:` as a numbered list with file paths and expected behaviour. If this PR already has 3 earlier `VERDICT: FAIL` evaluator comments, do not mention @copilot; add `stuck` instead.

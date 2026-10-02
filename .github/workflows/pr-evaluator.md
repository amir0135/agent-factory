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
timeout-minutes: 30
tools:
  github:
    toolsets: [default, actions]
  bash: true
  playwright:
    allowed_domains: [localhost, 127.0.0.1]
# Registries are needed to install dependencies before serve.sh can start the app.
# The browser itself stays restricted to loopback via tools.playwright.allowed_domains.
network:
  allowed: [defaults, node, python, playwright, local]
safe-outputs:
  add-comment:
    target: "*"
    max: 1
    github-token: ${{ secrets.GH_AW_AGENT_TOKEN }}
  upload-artifact:
    allowed-paths: ["/tmp/eval/*.png"]
    max-uploads: 1
    retention-days: 7
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

Before judging, inspect the changed-file list and `product/RUN.md`. Skip browser evaluation when the PR changes no application code (docs, tests, or harness-only changes) or `SERVE_MODE=none`; state the reason in the comment. Otherwise run `bash scripts/serve.sh` before judging. A nonzero exit is an automatic FAIL: quote the visible startup symptom and the log tail from `/tmp/eval/app.log`, and do not claim any browser journey passed.

For each AC the PR claims or flips to `done` that has a `Journey`, drive the running app through its steps as a user with Playwright. Check the specified success and error states and try the obvious unhappy path (empty/invalid input, double submit, or reload mid-flow as relevant). Record what you did and observed, including any visible symptom and the likely file/function on failure. At the end of each journey, save a screenshot as `/tmp/eval/<AC-ID>.png` (also capture immediately when a journey fails). When browser evaluation runs, publish the screenshots once via the `upload_artifact` safe output with `name: "pr-evaluator-screenshots"` and `path: "/tmp/eval"`; link `${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}` in the comment.

Automatic FAIL: deleted/skipped/loosened tests, edited verify commands, disabled lint/type rules, TODO/stub/mock in a production path, missing required error states, AC flipped to done without a test that would fail without the change, `product/PROGRESS.md` not updated.

Output ONE comment in exactly this shape:

```
<!-- evaluator -->
VERDICT: PASS | FAIL
Evaluated-SHA: ${{ github.event.workflow_run.head_sha }}
Evidence:
- AC-xxx: PASS/FAIL - journey: <what I did> -> <what I saw>
```

For ACs without a Journey, retain the existing command/diff evidence format. If browser evaluation was skipped, explicitly say `Browser journeys skipped: <reason>`.

- PASS: remove `eval:fail`, add `eval:pass`. Do not mention @copilot.
- FAIL: remove `eval:pass`, add `eval:fail`. Start the comment with `@copilot` on its own first line and add `Required fixes:` as a numbered list with file paths and expected behaviour. If this PR already has 3 earlier `VERDICT: FAIL` evaluator comments, do not mention @copilot; add `stuck` instead.

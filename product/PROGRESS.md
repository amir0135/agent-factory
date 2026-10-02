# Progress

> Updated by every PR. The reviewer rejects PRs that change behaviour without updating this file.

## Phase
planning

## Done
<!-- - [NNN-USx] summary (#PR) -->

## Active
<!-- - [NNN-USx] summary (#issue, @copilot) -->

## Blocked (human)
<!-- Mirror of BLOCKERS.md entries, with issue links -->

## Remaining
<!-- Ordered by priority. Planner maintains. -->

## Log
<!-- - YYYY-MM-DD: one line -->
- 2026-10-01: pinned "📊 Status" issue added (`.github/workflows/status.yml` + `scripts/status.py`); owner overview is now that issue, not this file.
- 2026-10-01: Factory board setup, project-sync workflow, and change-request intake added; live project creation needs the owner's classic PAT.
- 2026-10-01: Factory drafts now convert hourly only in the hub; app repos reconcile open and closed board cards daily. Live PAT-backed verification remains pending.
- 2026-10-01: PR evaluator browser journeys, app run contract (`product/RUN.md`, `scripts/serve.sh`), and optional AC Journey column added (#10).
- 2026-10-02: harness-sync run 36857810445 failed because `GH_AW_AGENT_TOKEN` was missing (owner has since set it); harness-sync now reports the failing step and its log, retries rebased pushes, and closes its issue on success (#2).

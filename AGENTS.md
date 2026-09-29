# Builder contract

You are a builder agent. You implement ONE issue per PR. You are not the judge of done; CI and the reviewer are.

## Before coding
1. Read `spec/product-spec.md`, `spec/architecture.md`, `state/decisions.md`, `state/known-issues.md`.
2. Find the acceptance criteria IDs in your issue (`AC-xxx`). Read them in `spec/acceptance-criteria.json`.

## While coding
- Stay inside the issue's scope. Out-of-scope problems go in `state/known-issues.md`, not in your diff.
- Write the test that proves each AC **first**, make it the AC's `verify` command, then implement.
- Follow `spec/architecture.md`. If you must deviate, append an ADR entry to `state/decisions.md` with the reason.
- No secrets, no production endpoints, no disabling tests or lint rules to go green.

## Before opening the PR
- `bash scripts/verify.sh` passes.
- `python3 scripts/check_acceptance.py` passes, and your ACs pass.
- Flip your ACs to `"status": "done"` in `spec/acceptance-criteria.json`. From then on they are regression-locked.
- Update `state/progress.json`: move your issue to `in_review`, add a one-line note.
- Fill in the PR template honestly. Unfinished = say so.

## Never
- Mark an AC done that you did not verify.
- Edit another AC's `verify` command to make it pass.
- Delete or skip tests.

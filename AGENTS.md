# AGENTS.md: operating rules for every agent in this repo

GitHub is the control plane. Chat history is not memory. If it is not in git, an issue, a PR, or `product/`, it does not exist for the next session.

## Sources of truth (read before acting)

| File | Holds | Who writes |
|---|---|---|
| `product/PRODUCT.md` | What the product is, users, journeys | planner |
| `product/ARCHITECTURE.md` | How it is built, constraints | planner, builder (via ADR) |
| `product/ACCEPTANCE_CRITERIA.md` | Every requirement as an executable check | planner adds, builder flips to `done` |
| `product/PROGRESS.md` | Done / active / blocked / remaining | every agent, every PR |
| `product/DECISIONS.md` | Settled decisions (ADR log) | any agent that decides something non-trivial |
| `product/BLOCKERS.md` | ONLY things a human must do | any agent, rarely |
| `specs/NNN-*/` | spec-kit feature specs: `spec.md`, `plan.md`, `tasks.md` | planner |
| `.specify/memory/constitution.md` | Engineering principles | human + planner |

Read `product/DECISIONS.md` before reopening any architectural question. Settled means settled.

## The loop

When given any engineering goal:

```
READ -> PLAN -> IMPLEMENT -> TEST -> INSPECT FAILURE -> FIX -> RETEST
     -> VERIFY AGAINST ACCEPTANCE CRITERIA -> UPDATE PROJECT STATE -> CONTINUE
```

- A failed test is not a reason to stop. Read the output, find the root cause, fix, rerun.
- A build failure is not a reason to stop.
- A first unsuccessful approach is not a reason to stop. Try the next conventional approach.
- When the assigned scope is done, continue with the next unchecked task in the same scope. Stop only at a real stop condition (below).

## Autonomy

Decide routine engineering questions yourself. Do NOT ask the human anything answerable by:
inspecting the repo, reading docs, following existing conventions, running tests, looking at similar code, or picking a conventional reversible option. Record the choice in `product/DECISIONS.md` if it matters later.

Escalate (add to `product/BLOCKERS.md` and label the issue `blocked:human`) ONLY for:
ambiguous product decisions with no reasonable default, missing credentials, irreversible or destructive operations, production access, legal/compliance, billing.

Ordinary bugs, failing tests, flaky tooling, and hard problems are NEVER human blockers.

## Definition of done

A task is done only when ALL hold:
1. `bash scripts/verify.sh` exits 0 (build, lint, format, typecheck, unit, integration, E2E).
2. `python3 scripts/check_acceptance.py` exits 0.
3. Every AC for the task has a real `Verify` command that fails without your change and passes with it, and its status is `done`.
4. `product/PROGRESS.md` and the feature's `tasks.md` checkboxes are updated.

NOT done if any of these are true:
- tests were not run, or fail
- the build fails
- ACs are only partially met
- placeholders, `TODO`, stubs, or `NotImplemented` remain in the delivered path
- mocks stand in for required production behaviour
- specified error states are unimplemented
- it only works on the happy path when other paths are specified

"Code exists" is not "feature complete". Say what is unfinished in the PR instead of claiming done.

## Security boundary

Allowed without asking: read files, edit app code, write tests, run dev/build/test commands, refactor, create branches/issues/PRs, fix CI, update dev docs.

Never:
- expose, print, or commit secrets; read `.env*` files
- weaken auth/security to make tests pass
- delete production data or run destructive prod migrations
- touch billing or rotate production credentials
- bypass branch protection, force-push to `main`, or use `--no-verify`
- delete, skip (`.skip`, `xit`, `@pytest.mark.skip`) or loosen failing tests to go green
- edit another AC's `Verify` command to make it pass
- disable lint rules, type checks, or security controls to get a passing build
- deploy to production (separate explicit human gate)

Hooks in `.github/hooks/` enforce part of this deterministically. Do not work around them.

## Task format

Every implementation issue contains: CONTEXT, REQUIREMENT, ACCEPTANCE CRITERIA (AC IDs), DEPENDENCIES, FILES/COMPONENTS, VERIFICATION. Titles are `[NNN-USx] <summary>` for spec-kit stories or `[AC-xxx] <summary>` for single criteria. Search open and closed issues for the ID before creating one. Never create duplicates.

For a `change-request`, the planner amends the existing feature spec and adds AC rows; create a new `specs/NNN-*` only when the request introduces a genuinely new capability.

## Agents

| Agent | Job | Never |
|---|---|---|
| `planner` | Spec, ACs, task breakdown, dependencies | Marks implementation done |
| `builder` | Implements one scoped task end to end | Grades its own work as final |
| `test-engineer` | Derives tests from ACs, reproduces failures | Fixes product code to fit a broken test |
| `reviewer` | Evidence-based evaluation against ACs | Trusts the builder's claims |

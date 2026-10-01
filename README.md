# agent-factory

An autonomous software-engineering harness on GitHub. You describe what you want in plain words; Copilot agents specify, build, test, debug, evaluate and merge it, until every acceptance criterion passes. GitHub (issues, PRs, Actions, files in this repo) is the control plane and the memory.

## The loop

```
 you: "Feature request" issue (plain words)          or  VS Code: /idea <text>
          |
   Feature Intake ──assign──> planner agent
          |                     spec-kit: specify > clarify > plan > tasks > analyze
          |                     writes specs/NNN-*/, product/*, AC rows (todo)
          v                     opens 1 PR  ──> gate ──> evaluator ──> auto-merge
   Backlog Dispatcher  (every 2h, and after every merge)
          |  creates [NNN-USx] task issues (deduped), respects dependencies
          |  assigns up to 3 to the builder agent in parallel
          v
   builder agent (Copilot cloud agent, sandboxed)
          |  READ > PLAN > TEST FIRST > IMPLEMENT > VERIFY > FIX > RETEST > UPDATE STATE
          |  preToolUse hook: blocks force-push, secrets, skipped tests, prod deploys
          |  agentStop hook: cannot finish while verify.sh is red (3 forced retries)
          v
   PR ready ──> gate (verify.sh + AC ratchet + gitleaks)
          |           fail ──> CI Doctor: root cause ──> "@copilot fix ..." (max 3, then stuck)
          v pass
   PR Evaluator (reviewer protocol, evidence only, stamps Evaluated-SHA)
          |           FAIL ──> "@copilot" numbered fixes (max 3, then stuck ──> planner re-plans)
          v PASS
   auto-merge (gate green on exact SHA + PASS verdict) ──> Dispatcher runs again
          |
   Spec Auditor (daily): finds hollow tests, missing coverage, stubs, doc drift ──> task issues
          |
   Done = `check_acceptance.py --strict` green on main ──> "[DONE]" issue for you
```

Humans are pulled in only through `product/BLOCKERS.md` / `blocked:human` issues: credentials, real product ambiguity, prod, billing, legal.

## What lives where

| Path | Purpose |
|---|---|
| `AGENTS.md` | Binding rules: the loop, autonomy, definition of done, security boundary |
| `.github/copilot-instructions.md` | Repo quick reference (commands, conventions). `ONBOARD` sections filled per repo |
| `product/` | Source of truth: PRODUCT, ARCHITECTURE, ACCEPTANCE_CRITERIA, PROGRESS, DECISIONS, BLOCKERS |
| `specs/NNN-*/` | spec-kit feature specs: `spec.md`, `plan.md`, `tasks.md` |
| `.specify/`, `.github/skills/speckit-*` | spec-kit (installed by `harness-sync`) |
| `.github/agents/` | `planner`, `builder`, `test-engineer`, `reviewer` |
| `.github/hooks/harness.json` + `scripts/hooks/` | Deterministic guardrails (human-owned; agents cannot edit) |
| `scripts/verify.sh` | THE quality gate: install, lint, format, types, unit, integration, build, E2E, audit |
| `scripts/check_acceptance.py` | Runs every AC; `done` rows are regression-locked; `--strict` = product done |
| `.github/workflows/gate.yml` | CI judge (skips drafts to save minutes) |
| `.github/workflows/*.md` | Agentic workflows (gh-aw): Feature Intake, Backlog Dispatcher, PR CI Doctor, PR Evaluator, Spec Auditor, plus upstream githubnext/agentics CI Failure Doctor and `/pr-fix` |
| `scripts/new-app.sh` | One command to start a new app from this template |
| `.github/workflows/auto-merge.yml` | Merge gate that replaces paid branch protection |
| `.github/workflows/harness-sync.yml` | Installs spec-kit, compiles `.md` workflows to `.lock.yml`, fixes exec bits |
| `.github/prompts/` | VS Code: `/idea` (plan something), `/continue` (keep building) |

## Start a new app (one command)

One-time, on your Mac:
1. `gh auth login`
2. Create a fine-grained PAT: Repository access **All repositories**; Actions, Contents, Issues, Pull requests, Workflows = **Read and write**. Store it: `security add-generic-password -a "$USER" -s agent-factory-pat -w` (paste when prompted).
3. Install the command: `gh api repos/amir0135/agent-factory/contents/scripts/new-app.sh --jq .content | base64 -d | sudo tee /usr/local/bin/new-app >/dev/null && sudo chmod +x /usr/local/bin/new-app`

Every new app:
```
new-app my-app "A booking tool for my yoga studio: members book classes, I see attendance"
```
It creates the repo from this template, sets the secret, Actions permissions and labels, runs harness-sync, and files your idea as a Feature request. The only manual step left is the one link it prints (Copilot workflow approval has no API).

## Setup (manual, if not using new-app)

1. **Secret** `GH_AW_AGENT_TOKEN`: fine-grained PAT, resource owner = you, only this repo. Repository permissions: Actions, Contents, Issues, Pull requests, Workflows = Read and write; Metadata = Read. Settings > Secrets and variables > Actions > New repository secret.
2. **Copilot cloud agent** on for this repo: profile > Copilot settings > Cloud agent > Repository access.
3. **Skip workflow approval** for Copilot: repo Settings > Copilot > Cloud agent > turn off "Require approval for workflow runs".
4. **Allow auto-merge flow**: Settings > Actions > General > Workflow permissions > "Read and write" + "Allow GitHub Actions to create and approve pull requests".
5. Actions tab > **harness-sync** > Run workflow. Installs spec-kit and compiles the agentic workflows. Check it goes green.
6. If agentic workflows fail with a Copilot auth error: add secret `COPILOT_GITHUB_TOKEN` (fine-grained PAT, Account permissions > Copilot Requests: Read).

Optional: repo variable `AUTO_MERGE=false` to review merges yourself (label `eval:pass` PRs are then yours to merge).

## Daily use

- **New product or feature**: open a *Feature request* issue. Plain words. That's it.
- **Existing repo**: copy this harness in, then open a *Harness onboarding* issue. The planner inspects the repo and adapts everything without replacing working architecture.
- **Nudge**: Actions > Backlog Dispatcher > Run workflow.
- **In VS Code**: `/idea <what you want>` or `/continue`.
- **Watch**: `product/PROGRESS.md`, the Actions tab, `blocked:human` issues.

## Honest limits

- gh-aw agentic workflows are in technical preview; syntax may shift. `harness-sync` reports compile errors as an issue.
- Every agent run costs Copilot premium requests and Actions minutes (private repos: free-plan minute cap applies). Dispatcher caps parallel builders at 3.
- Without paid branch protection, `main` is not hard-locked against you. The auto-merge workflow is the gate for agents.
- The evaluator is an LLM. It is the second opinion, not the first: `verify.sh` and the AC ratchet are the deterministic judges.

## Related
- [spec-kit](https://github.com/github/spec-kit) powers specification.
- [agent-forge](https://github.com/amir0135/agent-forge) can add stack-specific `.github/instructions/*` after onboarding (`forge generate --mode on-demand --types instruction,skill`). Do not let it overwrite `AGENTS.md`, `.github/agents/`, or `.github/hooks/`.

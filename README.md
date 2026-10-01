# agent-factory

You write one sentence describing an app. Copilot agents plan it, build it, test it, fix it and merge it until every acceptance criterion passes. You only get pulled in when a human is truly needed.

GitHub (issues, PRs, Actions, files in this repo) is the control plane and the memory.

---

## How to use it

**Your overview: the pinned 📊 Status issue in each app repo. Start there.** Goal, progress, what is in flight, what needs you — one screen, works on the GitHub mobile app.

### 1. One-time setup (on your Mac, ~5 min)

1. Log in to GitHub CLI:
   ```
   gh auth login
   ```
2. Create a **fine-grained PAT**: Repository access = **All repositories**. Actions, Contents, Issues, Pull requests, Workflows = **Read and write**. Save it to Keychain (paste when prompted):
   ```
   security add-generic-password -a "$USER" -s agent-factory-pat -w
   ```
3. Install the `new-app` command:
   ```
   gh api repos/amir0135/agent-factory/contents/scripts/new-app.sh --jq .content | base64 -d | sudo tee /usr/local/bin/new-app >/dev/null && sudo chmod +x /usr/local/bin/new-app
   ```

### 2. Start a new app (one command)

```
new-app my-app "A booking tool for my yoga studio: members book classes, I see attendance"
```

This creates the repo from this template, sets the secret, Actions permissions and labels, runs `harness-sync`, and files your idea as a Feature request.

**Then click the one link it prints** (Copilot workflow approval has no API). After that, walk away.

### 3. What happens without you

1. **Planner** turns your idea into specs, product docs and acceptance criteria, and opens a PR.
2. **Backlog Dispatcher** splits the work into task issues and assigns up to 3 Copilot builders in parallel.
3. Each PR goes through **gate** (`verify.sh` + AC ratchet + gitleaks), then the **PR Evaluator**, then **auto-merge**.
4. If something fails, **CI Doctor** / the evaluator tell Copilot exactly what to fix (max 3 tries, then it is marked stuck and re-planned).
5. When `check_acceptance.py --strict` is green on main, you get a **`[DONE]` issue**.

### 4. Day to day

| You want to... | Do this |
|---|---|
| Add a feature | Open a **Feature request** issue. Plain words. That's it. |
| Use it on an existing repo | Copy this harness in, then open a **Harness onboarding** issue. The planner adapts it without replacing working architecture. |
| Unstick it | Actions > **Backlog Dispatcher** > Run workflow |
| Work from VS Code | `/idea <what you want>` or `/continue` |
| See progress | The pinned **📊 Status** issue (auto-updated, never commented on) |
| Know when you're needed | `blocked:human` issues and `product/BLOCKERS.md` (credentials, real ambiguity, prod, billing, legal) |
| Review merges yourself | Set repo variable `AUTO_MERGE=false`. PRs labelled `eval:pass` are then yours to merge. |

### 5. Watch your budget

Every agent run costs **Copilot premium requests** and **Actions minutes**. On private repos the free-plan minute cap runs out fast with this loop. **Make app repos public when you can**: Actions minutes on public repos are free. The dispatcher caps parallel builders at 3.

---

## The loop (detail)

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
| `.github/workflows/status.yml` + `scripts/status.py` | Rewrites the pinned **📊 Status** issue. Plain script, no LLM |
| `.github/workflows/*.md` | Agentic workflows (gh-aw): Feature Intake, Backlog Dispatcher, PR CI Doctor, PR Evaluator, Spec Auditor, plus upstream githubnext/agentics CI Failure Doctor and `/pr-fix` |
| `scripts/new-app.sh` | One command to start a new app from this template |
| `.github/workflows/auto-merge.yml` | Merge gate that replaces paid branch protection |
| `.github/workflows/harness-sync.yml` | Installs spec-kit, compiles `.md` workflows to `.lock.yml`, fixes exec bits |
| `.github/prompts/` | VS Code: `/idea` (plan something), `/continue` (keep building) |

## Manual setup (only if not using `new-app`)

1. **Secret** `GH_AW_AGENT_TOKEN`: fine-grained PAT, resource owner = you, only this repo. Repository permissions: Actions, Contents, Issues, Pull requests, Workflows = Read and write; Metadata = Read. Settings > Secrets and variables > Actions > New repository secret.
2. **Copilot cloud agent** on for this repo: profile > Copilot settings > Cloud agent > Repository access.
3. **Skip workflow approval** for Copilot: repo Settings > Copilot > Cloud agent > turn off "Require approval for workflow runs".
4. **Allow auto-merge flow**: Settings > Actions > General > Workflow permissions > "Read and write" + "Allow GitHub Actions to create and approve pull requests".
5. Actions tab > **harness-sync** > Run workflow. Installs spec-kit and compiles the agentic workflows. Check it goes green.
6. If agentic workflows fail with a Copilot auth error: add secret `COPILOT_GITHUB_TOKEN` (fine-grained PAT, Account permissions > Copilot Requests: Read).

## Honest limits

- gh-aw agentic workflows are in technical preview; syntax may shift. `harness-sync` reports compile errors as an issue.
- Every agent run costs Copilot premium requests and Actions minutes (see **Watch your budget** above).
- Without paid branch protection, `main` is not hard-locked against you. The auto-merge workflow is the gate for agents.
- The evaluator is an LLM. It is the second opinion, not the first: `verify.sh` and the AC ratchet are the deterministic judges.

## Related
- [spec-kit](https://github.com/github/spec-kit) powers specification.
- [agent-forge](https://github.com/amir0135/agent-forge) can add stack-specific `.github/instructions/*` after onboarding (`forge generate --mode on-demand --types instruction,skill`). Do not let it overwrite `AGENTS.md`, `.github/agents/`, or `.github/hooks/`.

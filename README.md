# agent-factory

Spec in, tested app out. Planner/builder/evaluator loop on GitHub.

```
spec/product-spec.md ─▶ Claude (planner) ─▶ issues + AC-xxx
                                   │
                  assign Copilot coding agent (parallel, 1 issue = 1 branch)
                                   │
                                  PRs
                                   │
         gate.yml (verify.sh + acceptance ratchet)  +  Claude review vs spec
                    │                                   │
                  FAIL ─▶ @copilot fix comment        PASS ─▶ merge
                                   │
             check_acceptance.py --strict on main == DONE
```

| Role | Who | Why |
|---|---|---|
| Planner | Claude | Spec to issues, dependency order, ACs |
| Builders | Copilot coding agent | Parallel, sandboxed, no permission prompts |
| Evaluator | CI gate + Claude review | Builder never grades itself |
| Memory | `spec/`, `state/`, issues | Not chat history |

## Durable state
- `spec/product-spec.md`, `spec/architecture.md`: what and how
- `spec/acceptance-criteria.json`: every requirement has an executable `verify` command. `done` ACs are regression-locked.
- `state/progress.json`, `state/decisions.md`, `state/known-issues.md`

## New project
1. **Use this template** on GitHub (Settings > Template repository is on).
2. Write `spec/product-spec.md`. Rough is fine.
3. Tell Claude: "plan <repo>". It writes architecture + ACs, files issues, assigns Copilot.
4. Tell Claude "run the loop on <repo>" (or let the scheduled task do it).

## One-time repo settings
- Settings > Copilot > Coding agent: enabled for this repo.
- Settings > Actions > General: allow workflows to run on Copilot PRs without approval (otherwise every gate run waits on you).
- Branch protection on `main`: require `gate / evaluate`.
- Keep secrets out; the Copilot firewall stays on.

# Blockers requiring a human

ONLY: missing credentials, ambiguous product decisions with no sane default, irreversible/destructive ops, production access, legal/compliance, billing.
NEVER: bugs, failing tests, build errors, hard problems. Those are work, not blockers.

Format: `- [ ] <what is needed> | why agents cannot resolve it | issue #N | opened YYYY-MM-DD`

- [ ] Add the repo secret `GH_AW_AGENT_TOKEN` using a fine-grained PAT with Contents: write and Workflows: write | only the repository owner can configure Actions secrets | issue #2 | opened 2026-10-01

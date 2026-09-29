# Project Constitution

## Core Principles

### I. Acceptance criteria are executable
Every requirement becomes a row in `product/ACCEPTANCE_CRITERIA.md` with a shell command that proves it. No requirement is done until its command passes in CI. Done criteria are regression-locked.

### II. Test-first, journey-level
Write the failing test before the code. Web features need Playwright coverage of the real user journey, including required error states and permissions, not only unit tests.

### III. One quality gate
`scripts/verify.sh` is the single definition of mechanically healthy (build, lint, format, types, unit, integration, E2E). Agents, hooks and CI all run the same script.

### IV. Small, independently verifiable slices
Tasks are sized to one PR reviewable in under 10 minutes. Foundations before features. Parallel tasks must not touch the same files.

### V. Boring, reversible choices
Prefer the conventional, well-supported option. Record non-obvious choices as ADRs in `product/DECISIONS.md` and do not relitigate them.

### VI. Independent evaluation
The implementer never grades its own work. CI plus the reviewer agent decide, on evidence.

## Security Boundary
Agents may change code, tests, docs, branches, issues and PRs. Agents may not: expose secrets, weaken auth or tests to pass, touch production data, deploy to production, change billing, rotate credentials, bypass protections. Production deploy is a separate human gate.

## Governance
This constitution and `AGENTS.md` bind every agent. Amendments via PR with an ADR.

**Version**: 1.0.0 | **Ratified**: 2026-09-29 | **Last Amended**: 2026-09-29

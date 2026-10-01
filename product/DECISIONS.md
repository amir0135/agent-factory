# Decisions (ADR log)

Append-only. Future sessions must not relitigate a decision here without new evidence; supersede it with a new ADR instead.

## ADR-001: Agent harness (2026-09-29)
Context: autonomous build loop with GitHub as control plane.
Decision: spec-kit for specs, Markdown AC table as executable definition of done, Copilot cloud agent as builder, gh-aw agentic workflows for dispatch / CI recovery / evaluation, label-gated auto-merge instead of paid branch protection.
Consequence: all state lives in `product/`, `specs/`, issues and PRs.

## ADR-002: Local app-run contract (2026-10-01)
Context: PR evaluation needs a predictable way to start a candidate UI or HTTP API before browser journeys.
Decision: keep the app command, fixed loopback base URL, and health path in `product/RUN.md`; `scripts/serve.sh` reads that contract and treats `SERVE_MODE=none` as the explicit no-server case.
Consequence: onboarding must fill the contract for UI/API apps, and the evaluator can skip server startup for libraries and CLIs.

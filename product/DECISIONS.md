# Decisions (ADR log)

Append-only. Future sessions must not relitigate a decision here without new evidence; supersede it with a new ADR instead.

## ADR-001: Agent harness (2026-09-29)
Context: autonomous build loop with GitHub as control plane.
Decision: spec-kit for specs, Markdown AC table as executable definition of done, Copilot cloud agent as builder, gh-aw agentic workflows for dispatch / CI recovery / evaluation, label-gated auto-merge instead of paid branch protection.
Consequence: all state lives in `product/`, `specs/`, issues and PRs.

## ADR-002: User-owned Factory board (2026-10-01)
Context: per-repo pinned Status issues cannot provide cross-app intake or overview.
Decision: use one user-owned Projects v2 board with single-select App, Status and Type fields. A plain Actions workflow uses a separate classic PAT to reconcile repo items and convert board drafts; Status remains the per-app detail and the existing status script supplies shared label/assignment logic.
Consequence: GitHub's API creates views and sets their filters, but cannot set grouping or the default view; the setup command prints manual steps. Without the owner's PAT, project sync is a warning-only no-op.

## ADR-003: Local app-run contract (2026-10-01)
Context: PR evaluation needs a predictable way to start a candidate UI or HTTP API before browser journeys.
Decision: keep the app command, fixed loopback base URL, and health path in `product/RUN.md`; `scripts/serve.sh` reads that contract and treats `SERVE_MODE=none` as the explicit no-server case.
Consequence: onboarding must fill the contract for UI/API apps, and the evaluator can skip server startup for libraries and CLIs.

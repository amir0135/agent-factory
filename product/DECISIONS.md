# Decisions (ADR log)

Append-only. Future sessions must not relitigate a decision here without new evidence; supersede it with a new ADR instead.

## ADR-001: Agent harness (2026-09-29)
Context: autonomous build loop with GitHub as control plane.
Decision: spec-kit for specs, Markdown AC table as executable definition of done, Copilot cloud agent as builder, gh-aw agentic workflows for dispatch / CI recovery / evaluation, label-gated auto-merge instead of paid branch protection.
Consequence: all state lives in `product/`, `specs/`, issues and PRs.

## ADR-002: User-owned Factory board (2026-10-01)
Context: per-repo pinned Status issues cannot provide cross-app intake or overview.
Decision: use one user-owned Projects v2 board with single-select App, Status and Type fields. A plain Actions workflow uses a separate classic PAT to reconcile repo items and convert board drafts; Status remains the per-app detail and the existing status script supplies shared label/assignment logic.
Consequence: GitHub's API cannot configure board views; the setup command prints manual view steps. Without the owner's PAT, project sync is a warning-only no-op.

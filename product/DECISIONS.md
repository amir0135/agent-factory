# Decisions (ADR log)

Append-only. Future sessions must not relitigate a decision here without new evidence; supersede it with a new ADR instead.

## ADR-001: Agent harness (2026-09-29)
Context: autonomous build loop with GitHub as control plane.
Decision: spec-kit for specs, Markdown AC table as executable definition of done, Copilot cloud agent as builder, gh-aw agentic workflows for dispatch / CI recovery / evaluation, label-gated auto-merge instead of paid branch protection.
Consequence: all state lives in `product/`, `specs/`, issues and PRs.

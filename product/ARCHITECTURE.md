# Architecture

> The ACTUAL system, not the aspiration. Changes need an ADR in `DECISIONS.md`.

## Stack
| Layer | Choice | Why (ADR) |
|---|---|---|
| | | |

## Components and boundaries
<component>: owns <what>. Talks to <what> via <interface>.

## Data model

## Runtime
- Start locally:
- Environments: dev (agents allowed), staging, production (human gate only)

## Constraints agents must respect
- No new runtime dependency without an ADR.
- Keep module boundaries above; cross them only through the listed interfaces.

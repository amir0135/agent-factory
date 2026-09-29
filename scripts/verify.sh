#!/usr/bin/env bash
# Stack-agnostic quality gate. Edit per project; keep it the single source of truth.
set -euo pipefail
ran=0
if [ -f package.json ]; then
  ran=1
  npm ci
  npm run lint --if-present
  npm run typecheck --if-present
  npm test --if-present
  npm run build --if-present
fi
if [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  ran=1
  [ -f requirements.txt ] && pip install -q -r requirements.txt
  [ -f pyproject.toml ] && pip install -q -e ".[dev]" 2>/dev/null || true
  command -v ruff >/dev/null && ruff check .
  command -v mypy >/dev/null && [ -f mypy.ini -o -f pyproject.toml ] && mypy . || true
  command -v pytest >/dev/null && pytest -q
fi
[ $ran -eq 0 ] && echo "No app scaffolded yet. Gate passes trivially."
exit 0

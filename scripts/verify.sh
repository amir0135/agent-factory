#!/usr/bin/env bash
# The ONE quality gate. CI, hooks and agents all call this.
# Auto-detects Node (npm/pnpm/yarn/bun) and Python (uv/poetry/pip).
# Onboarding may replace detection with explicit commands; keep it one script.
# Flags: --quick (no build/e2e/audit), --no-e2e, --no-install
# Agent sandboxes are firewalled: deps come from copilot-setup-steps, so installs are skipped when present.
set -euo pipefail
cd "$(dirname "$0")/.."
E2E=1; INSTALL=1; QUICK=0
for a in "$@"; do case $a in --quick) QUICK=1; E2E=0;; --no-e2e) E2E=0;; --no-install) INSTALL=0;; esac; done
step() { echo; echo "==> $*"; }
ran=0

if [ -f package.json ]; then
  ran=1
  if   [ -f pnpm-lock.yaml ]; then PM=pnpm; INST="pnpm install --frozen-lockfile"
  elif [ -f yarn.lock ];      then PM=yarn; INST="yarn install --frozen-lockfile"
  elif [ -f bun.lockb ] || [ -f bun.lock ]; then PM=bun; INST="bun install --frozen-lockfile"
  else PM=npm; INST=$([ -f package-lock.json ] && echo "npm ci" || echo "npm install"); fi
  has() { node -e "process.exit(require('./package.json').scripts?.['$1']?0:1)"; }
  run() { if has "$1"; then step "$PM run $1"; $PM run "$1"; fi; }
  if [ $INSTALL = 1 ] && [ ! -d node_modules ]; then step "$INST"; $INST; fi
  run lint
  if has format:check; then run format:check; elif has "format-check"; then run format-check; fi
  run typecheck
  if ! has typecheck && [ -f tsconfig.json ]; then step "tsc --noEmit"; npx --no-install tsc --noEmit; fi
  if has test:unit; then run test:unit; elif has test; then step "$PM test"; $PM test; fi
  run test:integration
  [ $QUICK = 0 ] && run build
  if [ $E2E = 1 ]; then
    if has test:e2e; then run test:e2e
    elif ls playwright.config.* >/dev/null 2>&1; then step "playwright test"; npx --no-install playwright test; fi
  fi
  if [ $QUICK = 0 ] && [ "$PM" = npm ] && [ -f package-lock.json ]; then step "npm audit (critical)"; npm audit --omit=dev --audit-level=critical; fi
fi

if [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  ran=1
  if [ -f uv.lock ]; then PY="uv run"; [ $INSTALL = 1 ] && [ ! -d .venv ] && { step "uv sync"; uv sync --all-extras --dev; }
  elif [ -f poetry.lock ]; then PY="poetry run"; [ $INSTALL = 1 ] && { step "poetry install"; poetry install; }
  else PY=""; if [ $INSTALL = 1 ]; then
    [ -f requirements.txt ] && { step "pip install -r requirements.txt"; pip install -q -r requirements.txt; }
    [ -f requirements-dev.txt ] && pip install -q -r requirements-dev.txt
    [ -f pyproject.toml ] && { pip install -q -e ".[dev]" 2>/dev/null || pip install -q -e .; }
  fi; fi
  pyhas() { $PY python -c "import $1" 2>/dev/null; }
  if pyhas ruff || command -v ruff >/dev/null; then step "ruff"; $PY ruff check .; $PY ruff format --check .; fi
  if grep -qs "\[tool.mypy\]" pyproject.toml || [ -f mypy.ini ]; then step "mypy"; $PY mypy .; fi
  if grep -qs "\[tool.pyright\]" pyproject.toml || [ -f pyrightconfig.json ]; then step "pyright"; $PY pyright; fi
  if pyhas pytest; then
    step "pytest"
    if [ $E2E = 1 ]; then $PY pytest -q; else $PY pytest -q -m "not e2e"; fi
  fi
fi

[ $ran = 0 ] && echo "No application scaffolded yet. Gate passes trivially."
step "verify.sh: ALL GATES PASSED"

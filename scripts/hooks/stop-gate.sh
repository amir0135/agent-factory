#!/usr/bin/env bash
# agentStop hook: the agent may not finish while the gate is red.
# Returns {"decision":"block","reason":...} to force another turn (max 3 per session),
# then lets go so CI + CI Doctor take over instead of burning the job timeout.
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
IN=$(cat)
SID=$(printf '%s' "$IN" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("sessionId","x"))
except Exception: print("x")' 2>/dev/null)
CNT=/tmp/harness-stop-${SID:-x}
n=$(cat "$CNT" 2>/dev/null || echo 0)

base=$(git merge-base HEAD origin/HEAD 2>/dev/null || git merge-base HEAD origin/main 2>/dev/null || echo "")
changed=$( { [ -n "$base" ] && git diff --name-only "$base"; git diff --name-only; git ls-files --others --exclude-standard; } 2>/dev/null | sort -u)
[ -z "$changed" ] && exit 0   # nothing changed: Q&A or no-op session

fail=""
log=$(timeout 840 bash scripts/verify.sh 2>&1) || fail="scripts/verify.sh failed:\n$(printf '%s' "$log" | tail -40)"
if [ -z "$fail" ]; then
  log=$(AC_SKIP=AC-000 python3 scripts/check_acceptance.py 2>&1) || fail="check_acceptance.py failed (a done AC regressed or the table is invalid):\n$(printf '%s' "$log" | tail -40)"
fi
if [ -z "$fail" ] && [ -n "$base" ]; then
  if git diff "$base" -U0 | grep -E '^\+' | grep -qE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'; then
    fail="Secret-like string in your diff. Remove it and use configuration/env instead."
  fi
fi
if [ -z "$fail" ] && ! printf '%s\n' "$changed" | grep -q '^product/PROGRESS.md$'; then
  if printf '%s\n' "$changed" | grep -qvE '^(product/|specs/|\.specify/|docs/|README)'; then
    fail="You changed code but not product/PROGRESS.md. Update it (and tasks.md checkboxes / AC statuses) before finishing."
  fi
fi

if [ -n "$fail" ] && [ "$n" -lt 3 ]; then
  echo $((n+1)) > "$CNT"
  python3 -c 'import json,sys; print(json.dumps({"decision":"block","reason":"Definition of done not met (attempt '"$((n+1))"'/3). "+sys.argv[1]+"\nDiagnose the root cause, fix it, rerun, then finish. Do not skip tests or weaken checks."}))' "$(printf '%b' "$fail")"
  exit 0
fi
[ -n "$fail" ] && echo "stop-gate: still failing after 3 forced retries; handing over to CI" >&2
exit 0

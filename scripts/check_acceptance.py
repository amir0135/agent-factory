#!/usr/bin/env python3
"""Evaluator gate. Runs every acceptance criterion's verify command.

Ratchet rule:
  status "done"    -> MUST pass (regression = hard fail)
  status "todo"    -> reported only (unless --strict)
  status "deferred"-> skipped
--strict: every non-deferred criterion must pass. That is the DONE condition.
"""
import json, os, subprocess, sys, time

PATH = os.environ.get("CRITERIA", "spec/acceptance-criteria.json")
STRICT = "--strict" in sys.argv

data = json.load(open(PATH))
rows, hard_fail, open_count = [], False, 0

for c in data["criteria"]:
    status = c.get("status", "todo")
    if status == "deferred":
        rows.append((c["id"], status, "SKIP", c["requirement"]))
        continue
    t = time.time()
    try:
        r = subprocess.run(c["verify"], shell=True, capture_output=True, text=True,
                           timeout=c.get("timeout", 600))
        ok = r.returncode == 0
        tail = (r.stdout + r.stderr)[-800:]
    except subprocess.TimeoutExpired:
        ok, tail = False, "timeout"
    result = "PASS" if ok else "FAIL"
    rows.append((c["id"], status, result, c["requirement"]))
    if not ok:
        print(f"::group::{c['id']} FAIL ({time.time()-t:.0f}s)\n{tail}\n::endgroup::")
        if status == "done" or STRICT:
            hard_fail = True
    if status != "done" or not ok:
        open_count += 1

md = ["| id | status | result | requirement |", "|---|---|---|---|"]
md += [f"| {i} | {s} | {r} | {q} |" for i, s, r, q in rows]
passed = sum(1 for r in rows if r[2] == "PASS")
md.append(f"\n**{passed}/{len(rows)} passing, {open_count} open.**")
if open_count == 0 and not hard_fail:
    md.append("\n## DONE: all acceptance criteria verified.")
out = "\n".join(md)
print(out)
if os.environ.get("GITHUB_STEP_SUMMARY"):
    open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(out + "\n")
sys.exit(1 if hard_fail else 0)

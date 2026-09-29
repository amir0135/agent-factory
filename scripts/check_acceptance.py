#!/usr/bin/env python3
"""Evaluator gate: runs every acceptance criterion in product/ACCEPTANCE_CRITERIA.md.

Ratchet:
  done     -> must pass (regression = exit 1)
  todo     -> reported; fails only with --strict
  deferred -> skipped
  blocked  -> skipped, listed
--strict: every todo/done criterion must pass. That is the product DONE condition.
--list:   print table without running.
"""
import os, re, subprocess, sys, time

PATH = os.environ.get("AC_FILE", "product/ACCEPTANCE_CRITERIA.md")
STRICT, LIST = "--strict" in sys.argv, "--list" in sys.argv
# IDs already proven earlier in the same job (e.g. AC-000 = verify.sh), comma-separated
SKIP = {x.strip() for x in os.environ.get("AC_SKIP", "").split(",") if x.strip()}


def parse(text):
    m = re.search(r"<!-- AC-TABLE:START -->(.*?)<!-- AC-TABLE:END -->", text, re.S)
    if not m:
        sys.exit(f"{PATH}: AC-TABLE markers missing")
    rows = []
    for line in m.group(1).strip().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0] in ("ID", "") or set(cells[0]) <= set("-: "):
            continue
        ac_id, feature, crit, verify, status = cells[:5]
        verify = verify.strip().strip("`").strip()
        rows.append(dict(id=ac_id, feature=feature, crit=crit, verify=verify, status=status.lower()))
    ids = [r["id"] for r in rows]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        sys.exit(f"duplicate AC ids: {sorted(dup)}")
    return rows


rows = parse(open(PATH, encoding="utf-8").read())
out, hard_fail, open_n = [], False, 0
for r in rows:
    st = r["status"]
    if st not in ("todo", "done", "deferred", "blocked"):
        print(f"::error::{r['id']} has invalid status '{st}'")
        hard_fail = True
        continue
    if r["id"] in SKIP and st == "done":
        out.append((r, "PASS"))
        continue
    if st in ("deferred", "blocked") or LIST:
        out.append((r, "SKIP" if not LIST else "-"))
        if st == "blocked" or (LIST and st == "todo"):
            open_n += 1
        continue
    if not r["verify"]:
        out.append((r, "NO-VERIFY"))
        open_n += 1
        hard_fail = hard_fail or st == "done" or STRICT
        continue
    t = time.time()
    try:
        p = subprocess.run(r["verify"], shell=True, capture_output=True, text=True, timeout=900)
        ok, tail = p.returncode == 0, (p.stdout + p.stderr)[-1500:]
    except subprocess.TimeoutExpired:
        ok, tail = False, "timeout after 900s"
    out.append((r, "PASS" if ok else "FAIL"))
    if not ok:
        print(f"::group::{r['id']} FAIL ({time.time()-t:.0f}s): {r['verify']}\n{tail}\n::endgroup::")
        if st == "done":
            print(f"::error::REGRESSION {r['id']} was done and now fails")
            hard_fail = True
        elif STRICT:
            hard_fail = True
    if st != "done" or not ok:
        open_n += 1

md = ["| ID | Feature | Status | Result | Criterion |", "|---|---|---|---|---|"]
md += [f"| {r['id']} | {r['feature']} | {r['status']} | {res} | {r['crit']} |" for r, res in out]
passed = sum(1 for _, res in out if res == "PASS")
md.append(f"\n**{passed}/{len(out)} passing, {open_n} open.**")
if not LIST and open_n == 0 and not hard_fail:
    md.append("\n## DONE: every acceptance criterion verified.")
report = "\n".join(md)
print(report)
if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write(report + "\n")
sys.exit(1 if hard_fail else 0)

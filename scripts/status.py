#!/usr/bin/env python3
"""Owner dashboard: builds the body of the pinned "📊 Status" issue and updates it.

Deterministic, stdlib only, no LLM and no premium requests.
Progress numbers come only from the AC table (same parser as check_acceptance.py);
everything else comes from the GitHub API with GITHUB_TOKEN.

  python3 scripts/status.py            # render + create/update/pin the issue
  python3 scripts/status.py --dry-run  # render to stdout, no API writes
  python3 scripts/status.py --offline  # render from files only (no API at all)
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_acceptance import parse as parse_ac_table  # noqa: E402

TITLE = "📊 Status"
LABEL = "status"
API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
AC_FILE = os.environ.get("AC_FILE", "product/ACCEPTANCE_CRITERIA.md")
PROGRESS_FILE = os.environ.get("PROGRESS_FILE", "product/PROGRESS.md")
PRODUCT_FILE = os.environ.get("PRODUCT_FILE", "product/PRODUCT.md")
NOT_READY = ("blocked:human", "needs-replan", "stuck")


# ---------------------------------------------------------------- file inputs
def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def progress_bar(done, total, width=10):
    """`done`/`total` as a fixed-width block bar, e.g. '███████░░░'."""
    filled = 0 if total <= 0 else min(width, round(width * done / total))
    return "█" * filled + "░" * (width - filled)


def ac_summary(text):
    """Counts and per-feature breakdown from the AC table. The only source of progress."""
    rows = parse_ac_table(text) if text.strip() else []
    counted = [r for r in rows if r["status"] != "deferred"]
    features = {}
    for r in counted:
        f = features.setdefault(r["feature"] or "-", {"done": 0, "todo": 0, "blocked": 0})
        if r["status"] in f:
            f[r["status"]] += 1
    done = sum(1 for r in counted if r["status"] == "done")
    return {"done": done, "total": len(counted), "features": features}


def goal(text):
    """First real paragraph of PRODUCT.md: the one-liner, or the first prose line."""
    section, fallback = [], ""
    in_one_liner = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            if in_one_liner and section:
                break
            in_one_liner = s.lower().lstrip("# ").startswith("one-liner")
            continue
        if not s or s.startswith(">") or s.startswith("<!--"):
            if in_one_liner and section:
                break
            continue
        if in_one_liner:
            section.append(s)
        elif not fallback:
            fallback = s
    out = " ".join(section) or fallback
    if not out or out.startswith("<"):
        return "_Not defined yet. Open a Feature request issue and the planner fills this in._"
    return out


def phase(text):
    m = re.search(r"^##\s*Phase\s*$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    for line in (m.group(1) if m else "").splitlines():
        s = line.strip()
        if s and not s.startswith("<!--"):
            return s
    return "unknown"


# ------------------------------------------------------------------ GitHub IO
def api(path, method="GET", payload=None):
    url = path if path.startswith("http") else f"{API}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read().decode()
    return json.loads(body) if body else {}


def graphql(query, variables):
    return api(f"{API}/graphql", "POST", {"query": query, "variables": variables})


def issues(**params):
    params.setdefault("state", "open")
    params.setdefault("per_page", 100)
    q = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    return [i for i in api(f"/repos/{REPO}/issues?{q}") if "pull_request" not in i]


def pulls(**params):
    params.setdefault("state", "open")
    params.setdefault("per_page", 50)
    q = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    return api(f"/repos/{REPO}/pulls?{q}")


def gate_status(pr):
    """Conclusion of the gate check runs on the PR head, in one word."""
    try:
        runs = api(f"/repos/{REPO}/commits/{pr['head']['sha']}/check-runs?per_page=50")["check_runs"]
    except (urllib.error.URLError, KeyError, OSError):
        return "unknown"
    if not runs:
        return "no checks"
    if any(r["status"] != "completed" for r in runs):
        return "running"
    bad = [r for r in runs if r["conclusion"] not in ("success", "neutral", "skipped")]
    return "❌ failing" if bad else "✅ green"


def labels_of(item):
    return {la["name"] for la in item.get("labels", [])}


def assigned_to_copilot(item):
    return any("copilot" in (a.get("login") or "").lower() for a in item.get("assignees", []))


def verdict(pr):
    la = labels_of(pr)
    return "eval:pass" if "eval:pass" in la else "eval:fail" if "eval:fail" in la else "no verdict"


def link(item):
    return f"[#{item['number']}]({item['html_url']})"


# -------------------------------------------------------------------- render
def section(title, lines, empty):
    return f"## {title}\n" + ("\n".join(lines) if lines else empty) + "\n"


def render(data):
    ac, ts = data["ac"], data["now"]
    pct = round(100 * ac["done"] / ac["total"]) if ac["total"] else 0
    body = [f"## 🎯 Goal\n{data['goal']}\n"]

    body.append(
        section(
            f"🙋 Needs you  ({len(data['needs_you'])})",
            [f"- {link(i)} {i['title']}" for i in data["needs_you"]],
            "Nothing. 🎉",
        )
    )

    bar = progress_bar(ac["done"], ac["total"])
    body.append(
        f"## 📈 Progress   {bar} {ac['done']}/{ac['total']} acceptance criteria done ({pct}%)\n"
        f"Phase: {data['phase']}\n"
    )
    if ac["features"]:
        rows = ["| Feature | Done | Todo | Blocked |", "|---|---|---|---|"]
        rows += [
            f"| {name} | {c['done']} | {c['todo']} | {c['blocked']} |"
            for name, c in sorted(ac["features"].items())
        ]
        body.append("\n".join(rows) + "\n")

    in_progress = [
        f"- {link(p)} {p['title']} — gate: {p['gate']}, {p['verdict']}" for p in data["open_prs"]
    ] + [f"- {link(i)} {i['title']} — @copilot building" for i in data["building"]]
    body.append(section("🔨 In progress", in_progress, "Nothing in flight."))

    body.append(
        section("📋 Up next", [f"- {link(i)} {i['title']}" for i in data["up_next"]], "Backlog empty.")
    )

    body.append(
        section(
            "✅ Recently done",
            [f"- {link(p)} {p['title']} ({p['merged_at'][:10]})" for p in data["merged"]],
            "Nothing merged yet.",
        )
    )

    body.append(section("⚠️ Stuck", [f"- {link(i)} {i['title']}" for i in data["stuck"]], "Nothing stuck."))

    body.append(
        f"_Updated {ts} by status.yml. Source of truth: ACCEPTANCE_CRITERIA.md + issues/PRs._"
    )
    return "\n".join(body)


def collect(offline=False):
    data = {
        "ac": ac_summary(read(AC_FILE)),
        "goal": goal(read(PRODUCT_FILE)),
        "phase": phase(read(PROGRESS_FILE)),
        "now": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "needs_you": [],
        "open_prs": [],
        "building": [],
        "up_next": [],
        "merged": [],
        "stuck": [],
    }
    if offline or not REPO:
        return data

    data["needs_you"] = issues(labels="blocked:human")[:10]
    data["stuck"] = issues(labels="stuck")[:10]

    open_prs = [p for p in pulls(sort="created", direction="desc") if not p.get("draft")][:10]
    for p in open_prs:
        p["gate"], p["verdict"] = gate_status(p), verdict(p)
    data["open_prs"] = open_prs

    tasks = issues(labels="agent-task", sort="created", direction="asc")
    data["building"] = [i for i in tasks if assigned_to_copilot(i)][:10]
    data["up_next"] = [
        i
        for i in tasks
        if not i.get("assignees") and not (labels_of(i) & set(NOT_READY))
    ][:5]

    closed = pulls(state="closed", sort="updated", direction="desc", per_page=60)
    merged = sorted(
        (p for p in closed if p.get("merged_at")), key=lambda p: p["merged_at"], reverse=True
    )
    data["merged"] = merged[:10]
    return data


def find_issue():
    for i in issues(labels=LABEL, state="all"):
        if i["title"].strip() == TITLE:
            return i
    return None


def pin(node_id):
    try:
        graphql("mutation($id:ID!){pinIssue(input:{issueId:$id}){issue{number}}}", {"id": node_id})
    except (urllib.error.URLError, OSError) as e:  # already pinned / pin limit reached
        print(f"note: could not pin the issue ({e})")


def main():
    offline = "--offline" in sys.argv
    dry = "--dry-run" in sys.argv or offline
    body = render(collect(offline))
    if dry:
        print(body)
        return
    if not TOKEN or not REPO:
        sys.exit("GITHUB_TOKEN and GITHUB_REPOSITORY are required")
    existing = find_issue()
    if existing:
        api(f"/repos/{REPO}/issues/{existing['number']}", "PATCH", {"body": body, "state": "open"})
        print(f"updated {existing['html_url']}")
        return
    created = api(
        f"/repos/{REPO}/issues", "POST", {"title": TITLE, "body": body, "labels": [LABEL]}
    )
    pin(created["node_id"])
    print(f"created {created['html_url']}")


if __name__ == "__main__":
    main()

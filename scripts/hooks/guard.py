#!/usr/bin/env python3
"""preToolUse guardrail for Copilot agents. Denies a small set of dangerous actions.

Fail-open on its own errors (a crashing preToolUse hook would deny EVERY tool call).
Keep this list short: it must stop disasters, not slow normal development.
"""
import json, re, sys


def decide(decision, reason=""):
    out = {"permissionDecision": decision}
    if reason:
        out["permissionDecisionReason"] = reason
    print(json.dumps(out))
    sys.exit(0)


try:
    evt = json.load(sys.stdin)
    tool = str(evt.get("toolName", "")).lower()
    args = evt.get("toolArgs", "")
    blob = args if isinstance(args, str) else json.dumps(args)
    if isinstance(args, dict) and isinstance(args.get("command"), str):
        cmd = args["command"]
    elif isinstance(args, dict):
        cmd = "\n".join(v for v in args.values() if isinstance(v, str))
    else:
        cmd = blob
    # Only NEW content is checked for skips/secrets, so removing a skip is allowed.
    NEW_KEYS = ("new_str", "file_text", "content", "text", "new_content", "insert_text")
    if isinstance(args, dict):
        parts = [v for k, v in args.items() if k in NEW_KEYS and isinstance(v, str)]
        patch = args.get("patch") or args.get("input")
        if isinstance(patch, str):
            parts += [l[1:] for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")]
        added = "\n".join(parts) if parts else blob
    else:
        lines = [l[1:] for l in blob.splitlines() if l.startswith("+") and not l.startswith("+++")]
        added = "\n".join(lines) if lines else blob
except Exception:
    decide("allow")

SHELL = [
    (r"\brm\s+-[a-z]*r[a-z]*f?[a-z]*\s+(/|~|\$HOME)(\s|$|/\s)", "recursive delete of / or home"),
    (r"\bgit\s+push\b[^\n]*(--force\b|--force-with-lease\b|\s-f\b)", "force push"),
    (r"\bgit\s+push\b[^\n;&|]*(\s|:)(main|master)(\s|$|;|&)", "direct push to main"),
    (r"--no-verify\b", "--no-verify bypasses checks"),
    (r"\b(curl|wget)\b[^\n]*\|\s*(sudo\s+)?(ba|z)?sh\b", "piping remote script to shell"),
    (r"\bDROP\s+(DATABASE|SCHEMA)\b", "dropping a database"),
    (r"(^|[;&|]\s*)(printenv|env)\s*($|[;&|])", "dumping environment (secrets)"),
    (r"\bcat\s+[^\n]*\.env(\.(local|production|prod))?\b(?!\.example)", "reading .env secrets"),
    (r"\bgh\s+(secret|repo\s+delete|release\s+delete|api\s+[^\n]*-X\s*DELETE)", "destructive/secret gh command"),
    (r"\b(terraform|tofu)\s+(apply|destroy)\b", "infrastructure change"),
    (r"\bkubectl\s+(delete|apply)\b[^\n]*(prod|production)", "production cluster change"),
    (r"\b(npm|pnpm|yarn)\s+publish\b", "publishing a package"),
    (r"\b(vercel\s+[^\n]*--prod|fly\s+deploy|az\s+webapp\s+deploy|firebase\s+deploy)\b", "production deploy"),
]
EDIT_PATHS = [
    (r"(^|[\"'/\s])\.env(\.(local|production|prod|development))?[\"'\s]", "editing .env secrets file"),
    (r"\.github/hooks/|scripts/hooks/", "guardrails are human-owned"),
    (r"\.lock\.yml", "compiled agentic workflow: edit the .md source instead"),
]
EDIT_CONTENT = [
    (r"\b(it|test|describe)\.(skip|only)\(|\bxit\(|\bxdescribe\(|@pytest\.mark\.skip\b|pytest\.skip\(", "skipping/focusing tests"),
    (r"AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9]{32,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----", "secret in file content"),
]

if tool in ("bash", "shell", "powershell"):
    for pat, why in SHELL:
        if re.search(pat, cmd, re.I | re.M):
            decide("deny", f"Blocked by harness guard: {why}. See AGENTS.md security boundary; find a safe alternative.")
elif tool in ("edit", "create", "str_replace_editor", "apply_patch", "write"):
    for pat, why in EDIT_PATHS:
        if re.search(pat, blob):
            decide("deny", f"Blocked by harness guard: {why}.")
    for pat, why in EDIT_CONTENT:
        if re.search(pat, added):
            decide("deny", f"Blocked by harness guard: {why}. Fix the code or the test properly; never skip.")
decide("allow")

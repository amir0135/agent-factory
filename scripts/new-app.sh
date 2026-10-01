#!/usr/bin/env bash
# Start a new autonomously-built app in one command.
#
#   new-app <repo-name> "<what you want, in plain words>"
#
# One-time setup per machine (see README "Start a new app"):
#   1. gh auth login
#   2. Store a fine-grained PAT (All repositories; Actions, Contents, Issues,
#      Pull requests, Workflows = Read and write) in the macOS Keychain:
#        security add-generic-password -a "$USER" -s agent-factory-pat -w
#      (it prompts for the token; it never lands in shell history)
#      Elsewhere: export AGENT_FACTORY_PAT=... instead.
set -euo pipefail
NAME=${1:?usage: new-app <repo-name> "<idea>"}
IDEA=${2:?usage: new-app <repo-name> "<idea>"}
VISIBILITY=${VISIBILITY:-private}
OWNER=$(gh api user --jq .login)
TEMPLATE=${TEMPLATE:-$OWNER/agent-factory}
REPO="$OWNER/$NAME"
say() { printf '\n==> %s\n' "$*"; }

PAT=${AGENT_FACTORY_PAT:-}
if [ -z "$PAT" ] && command -v security >/dev/null; then
  PAT=$(security find-generic-password -a "$USER" -s agent-factory-pat -w 2>/dev/null || true)
fi
[ -n "$PAT" ] || { echo "No PAT found. See the setup notes at the top of this script."; exit 1; }

say "Making sure $TEMPLATE is a template"
gh api -X PATCH "repos/$TEMPLATE" -F is_template=true >/dev/null

say "Creating $REPO ($VISIBILITY) from $TEMPLATE"
gh repo create "$REPO" "--$VISIBILITY" --template "$TEMPLATE"
for i in $(seq 1 30); do gh api "repos/$REPO/contents/AGENTS.md" >/dev/null 2>&1 && break; sleep 2; done

say "Secret GH_AW_AGENT_TOKEN"
printf '%s' "$PAT" | gh secret set GH_AW_AGENT_TOKEN -R "$REPO"

say "Actions: read/write token, allowed to create and approve PRs"
gh api -X PUT "repos/$REPO/actions/permissions/workflow" \
  -f default_workflow_permissions=write -F can_approve_pull_request_reviews=true >/dev/null

say "Labels"
for l in feature onboard needs-replan agent-task bug blocked:human stuck regression eval:pass eval:fail product-done status; do
  gh label create "$l" -R "$REPO" --force >/dev/null
done

say "harness-sync (spec-kit + compiled agentic workflows)"
for i in $(seq 1 20); do gh workflow run harness-sync.yml -R "$REPO" >/dev/null 2>&1 && break; sleep 3; done
sleep 8
RUN=$(gh run list -R "$REPO" --workflow harness-sync.yml --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$RUN" -R "$REPO" --exit-status >/dev/null && echo "harness-sync green"

say "Pinned 'Status' issue (your overview)"
gh workflow run status.yml -R "$REPO" >/dev/null 2>&1 || echo "status.yml did not start; run it from the Actions tab"

say "Feature request (the planner picks it up)"
TITLE=$(printf '%s' "$IDEA" | head -c 70)
gh issue create -R "$REPO" --title "$TITLE" --label feature --body "$IDEA" >/dev/null

cat <<MSG

Done. $REPO is building itself.

One click GitHub has no API for (Copilot's CI would otherwise wait for you):
  https://github.com/$REPO/settings  ->  Copilot > Cloud agent
  -> turn OFF "Require approval for workflow runs"

Your overview: the pinned 📊 Status issue -> https://github.com/$REPO/issues
Watch: https://github.com/$REPO/actions
MSG

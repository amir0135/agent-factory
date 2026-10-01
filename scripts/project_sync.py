#!/usr/bin/env python3
"""Synchronize repository issues, PRs and Factory project drafts without an LLM."""
import os
import re
import sys

import status

TITLE = "🏭 Factory"
STATUSES = ("📥 Inbox", "🧠 Planning", "📋 Ready", "🔨 Building",
            "👀 In review", "🙋 Needs you", "✅ Done")
NOTE = "Set App to send this to the factory"


def map_status(item, linked_open_pr=False):
    """First matching state wins; None means remove a not-planned item."""
    if item.get("pull_request") and item.get("state") == "closed" and not item.get("merged_at"):
        return None
    if item.get("state") == "closed" or item.get("closed_at"):
        if item.get("state_reason") == "not_planned":
            return None
        return STATUSES[6]
    if item.get("merged_at"):
        return STATUSES[6]
    labels = status.labels_of(item)
    if labels & {"blocked:human", "stuck"}:
        return STATUSES[5]
    if "pull_request" in item or linked_open_pr:
        return STATUSES[4]
    if "agent-task" in labels and status.assigned_to_copilot(item):
        return STATUSES[3]
    if "agent-task" in labels and not item.get("assignees"):
        return STATUSES[2]
    if ("feature" in labels or "change-request" in labels) and status.assigned_to_copilot(item):
        return STATUSES[1]  # Feature Intake assigns the planner as Copilot.
    if status.assigned_to_copilot(item):
        return STATUSES[3]
    return STATUSES[0]


def graphql(query, **variables):
    return status.graphql(query, variables)["data"]


def project(owner):
    data = graphql(
        "query($owner:String!){user(login:$owner){projectsV2(first:100)"
        "{nodes{id number title url fields(first:100){nodes{... on ProjectV2SingleSelectField"
        "{id name options{id name}} ... on ProjectV2Field{id name}}}}}}}",
        owner=owner,
    )
    return next((p for p in data["user"]["projectsV2"]["nodes"] if p["title"] == TITLE), None)


def items(project_id):
    cursor = None
    while True:
        data = graphql(
            "query($id:ID!,$after:String){node(id:$id){... on ProjectV2{items(first:100,"
            "after:$after){nodes{id content{... on Issue{id} ... on PullRequest{id}"
            " ... on DraftIssue{id title body}} fieldValueByName(name:\"App\")"
            "{... on ProjectV2ItemFieldSingleSelectValue{name}}}"
            "} pageInfo{hasNextPage endCursor}}}}}",
            id=project_id, after=cursor,
        )["node"]["items"]
        yield from data["nodes"]
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]


def field_value(project_id, item_id, field, option):
    graphql(
        "mutation($project:ID!,$item:ID!,$field:ID!,$option:String!)"
        "{updateProjectV2ItemFieldValue(input:{projectId:$project,itemId:$item,"
        "fieldId:$field,value:{singleSelectOptionId:$option}}){projectV2Item{id}}}",
        project=project_id, item=item_id, field=field, option=option,
    )


def sync_item(board, fields, existing, item, linked_open_pr=False):
    value = map_status(item, linked_open_pr)
    found = next((i for i in existing if (i.get("content") or {}).get("id") == item["node_id"]), None)
    if value is None:
        if found:
            graphql("mutation($p:ID!,$i:ID!){deleteProjectV2Item(input:{projectId:$p,"
                    "itemId:$i}){deletedItemId}}", p=board["id"], i=found["id"])
        return
    if not found:
        found = graphql(
            "mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,"
            "contentId:$c}){item{id}}}", p=board["id"], c=item["node_id"],
        )["addProjectV2ItemById"]["item"]
        existing.append({"id": found["id"], "content": {"id": item["node_id"]}})
    kinds = status.labels_of(item)
    kind = ("Bug" if "bug" in kinds else "Change" if "change-request" in kinds
            else "Feature" if "feature" in kinds else "Task")
    for name, desired in (("Status", value), ("App", os.environ["GITHUB_REPOSITORY"].split("/")[1]),
                          ("Type", kind)):
        field = fields[name]
        option = next((o["id"] for o in field["options"] if o["name"] == desired), None)
        if option:
            field_value(board["id"], found["id"], field["id"], option)
        elif name == "App":
            print(f"::warning::Add {desired} to the Factory App field with factory-board.sh")


def linked_pr(issue):
    data = graphql(
        "query($id:ID!){node(id:$id){... on Issue"
        "{closedByPullRequestsReferences(first:20){nodes{state}}}}}", id=issue["node_id"],
    )
    return any(p["state"] == "OPEN" for p in data["node"]["closedByPullRequestsReferences"]["nodes"])


def convert_drafts(board, existing, owner):
    for item in existing:
        draft = item.get("content") or {}
        if "title" not in draft:
            continue
        app = (item.get("fieldValueByName") or {}).get("name")
        if not app:
            if NOTE not in (draft.get("body") or ""):
                body = ((draft.get("body") or "").rstrip() + "\n\n" + NOTE).strip()
                graphql("mutation($id:ID!,$body:String!){updateProjectV2DraftIssue("
                        "input:{draftIssueId:$id,body:$body}){draftIssue{id}}}",
                        id=draft["id"], body=body)
            continue
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", app):
            print(f"::warning::Invalid App option: {app}")
            continue
        # Ensure the target is owned by this user and accessible before creating.
        repo = status.api(f"/repos/{owner}/{app}")
        if repo["owner"]["login"].lower() != owner.lower():
            continue
        body = (draft.get("body") or "").replace(NOTE, "").strip()
        status.api(f"/repos/{owner}/{app}/issues", "POST",
                   {"title": draft["title"], "body": body, "labels": ["change-request"]})
        graphql("mutation($p:ID!,$i:ID!){deleteProjectV2Item(input:{projectId:$p,"
                "itemId:$i}){deletedItemId}}", p=board["id"], i=item["id"])


def main():
    owner, repo = os.environ["GITHUB_REPOSITORY"].split("/", 1)
    board = project(owner)
    if not board:
        sys.exit(f"Factory project missing for {owner}; run scripts/factory-board.sh")
    fields = {f["name"]: f for f in board["fields"]["nodes"] if f and "options" in f}
    existing = list(items(board["id"]))
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event in ("schedule", "workflow_dispatch", "projects_v2_item"):
        convert_drafts(board, existing, owner)
        return
    import json
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        payload = json.load(f)
    item = payload.get("issue") or payload.get("pull_request")
    if not item or "node_id" not in item:
        return
    if event == "issues":
        sync_item(board, fields, existing, item, linked_pr(item))
    else:
        item["pull_request"] = True
        sync_item(board, fields, existing, item)
        # Reconcile issues linked to this PR when it opens or merges.
        data = graphql(
            "query($id:ID!){node(id:$id){... on PullRequest"
            "{closingIssuesReferences(first:20){nodes{number}}}}}", id=item["node_id"],
        )
        for issue in data["node"]["closingIssuesReferences"]["nodes"]:
            detail = status.api(f"/repos/{owner}/{repo}/issues/{issue['number']}")
            sync_item(board, fields, existing, detail, linked_pr(detail))


if __name__ == "__main__":
    main()

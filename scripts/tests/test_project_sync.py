#!/usr/bin/env python3
"""Pure, table-driven Factory status mapping regression tests."""
import os
import sys
import unittest
from unittest.mock import mock_open, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import project_sync  # noqa: E402
from project_sync import STATUSES, map_status  # noqa: E402


class StatusMapping(unittest.TestCase):
    def test_first_matching_rule(self):
        cases = [
            ("completed", {"state": "closed", "state_reason": "completed",
                            "labels": [{"name": "stuck"}]}, False, STATUSES[6]),
            ("not planned", {"state": "closed", "state_reason": "not_planned"}, False, None),
            ("closed unmerged PR", {"state": "closed", "pull_request": True}, False, None),
            ("merged", {"merged_at": "2026-01-01", "pull_request": True}, False, STATUSES[6]),
            ("blocked PR", {"pull_request": True, "labels": [{"name": "blocked:human"}]},
             False, STATUSES[5]),
            ("stuck", {"labels": [{"name": "stuck"}]}, False, STATUSES[5]),
            ("open PR", {"pull_request": True}, False, STATUSES[4]),
            ("linked PR", {}, True, STATUSES[4]),
            ("building", {"labels": [{"name": "agent-task"}],
                          "assignees": [{"login": "copilot-swe-agent"}]}, False, STATUSES[3]),
            ("ready", {"labels": [{"name": "agent-task"}]}, False, STATUSES[2]),
            ("planning change", {"labels": [{"name": "change-request"}],
                                 "assignees": [{"login": "copilot-swe-agent"}]},
             False, STATUSES[1]),
            ("planning feature", {"labels": [{"name": "feature"}],
                                  "assignees": [{"login": "copilot"}]}, False, STATUSES[1]),
            ("other copilot", {"assignees": [{"login": "copilot"}]}, False, STATUSES[3]),
            ("change inbox", {"labels": [{"name": "change-request"}]}, False, STATUSES[0]),
            ("default", {}, False, STATUSES[0]),
        ]
        for name, item, linked, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(map_status(item, linked), expected)


class DraftConversion(unittest.TestCase):
    def test_without_app_adds_note_once(self):
        draft = {"id": "draft", "title": "Change", "body": ""}
        item = {"id": "item", "content": draft}
        with patch.object(project_sync, "graphql") as gql:
            project_sync.convert_drafts({}, [item], "owner")
            self.assertEqual(gql.call_args.kwargs["body"], project_sync.NOTE)
            draft["body"] = project_sync.NOTE
            gql.reset_mock()
            project_sync.convert_drafts({}, [item], "owner")
            gql.assert_not_called()

    def test_with_app_converts_and_labels_issue(self):
        item = {"id": "item", "content": {"id": "draft", "title": "Change",
                                            "body": "Please change this"},
                "fieldValueByName": {"name": "my-app"}}
        with patch.object(project_sync.status, "api", side_effect=[
            {"node_id": "repo-id", "owner": {"login": "owner"}}, {}
        ]) as api, patch.object(project_sync, "graphql", return_value={
            "convertProjectV2DraftIssueItemToIssue": {"item": {"content": {"number": 42}}}
        }) as gql:
            project_sync.convert_drafts({}, [item], "owner")
        self.assertIn("convertProjectV2DraftIssueItemToIssue", gql.call_args.args[0])
        self.assertEqual(api.call_args.args[0], "/repos/owner/my-app/issues/42/labels")
        self.assertEqual(api.call_args.args[2]["labels"], ["change-request"])


class PullRequestSync(unittest.TestCase):
    def test_cross_repo_closing_issue_does_not_update_same_number_locally(self):
        event = '{"pull_request":{"node_id":"pr-id","number":8,"state":"open"}}'
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/my-app",
                                      "GITHUB_EVENT_NAME": "pull_request",
                                      "GITHUB_EVENT_PATH": "/tmp/event.json"}), \
             patch("builtins.open", mock_open(read_data=event)), \
             patch.object(project_sync, "project", return_value={"id": "board", "fields": {"nodes": []}}), \
             patch.object(project_sync, "items", return_value=[]), \
             patch.object(project_sync, "sync_item") as sync, \
             patch.object(project_sync, "graphql", return_value={
                 "node": {"closingIssuesReferences": {"nodes": [
                     {"number": 8, "repository": {"nameWithOwner": "owner/other-app"}}
                 ]}}
             }), patch.object(project_sync.status, "api") as api:
            project_sync.main()
        sync.assert_called_once()
        api.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Pure, table-driven Factory status mapping regression tests."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from project_sync import STATUSES, map_status  # noqa: E402


class StatusMapping(unittest.TestCase):
    def test_first_matching_rule(self):
        cases = [
            ("completed", {"state": "closed", "state_reason": "completed",
                            "labels": [{"name": "stuck"}]}, False, STATUSES[6]),
            ("not planned", {"state": "closed", "state_reason": "not_planned"}, False, None),
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

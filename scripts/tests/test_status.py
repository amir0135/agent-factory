#!/usr/bin/env python3
"""Harness self-test: AC-table parsing and progress-bar rendering in scripts/status.py.

Stdlib only, no network. Run directly or via scripts/verify.sh.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import status  # noqa: E402

TABLE = """# Acceptance criteria
<!-- AC-TABLE:START -->
| ID | Feature | Criterion | Verify | Status |
|---|---|---|---|---|
| AC-000 | harness | Quality gate passes | `bash scripts/verify.sh` | done |
| AC-001 | booking | Member books a class | `npm run test:e2e` | todo |
| AC-002 | booking | Waitlist promotes | `npm run test:unit` | done |
| AC-003 | billing | Invoice emailed | `npm run test:unit` | blocked |
| AC-004 | billing | Refunds | `npm run test:unit` | deferred |
<!-- AC-TABLE:END -->
"""


class ProgressBar(unittest.TestCase):
    def test_width_and_fill(self):
        self.assertEqual(status.progress_bar(0, 20), "░" * 10)
        self.assertEqual(status.progress_bar(20, 20), "█" * 10)
        self.assertEqual(status.progress_bar(14, 20), "█" * 7 + "░" * 3)
        self.assertEqual(len(status.progress_bar(3, 7)), 10)

    def test_no_criteria_is_empty_bar(self):
        self.assertEqual(status.progress_bar(0, 0), "░" * 10)

    def test_never_overflows(self):
        self.assertEqual(status.progress_bar(99, 20), "█" * 10)


class AcSummary(unittest.TestCase):
    def test_counts_exclude_deferred(self):
        s = status.ac_summary(TABLE)
        self.assertEqual((s["done"], s["total"]), (2, 4))

    def test_grouped_by_feature(self):
        s = status.ac_summary(TABLE)
        self.assertEqual(s["features"]["booking"], {"done": 1, "todo": 1, "blocked": 0})
        self.assertEqual(s["features"]["billing"], {"done": 0, "todo": 0, "blocked": 1})
        self.assertNotIn("", s["features"])

    def test_empty_file(self):
        self.assertEqual(status.ac_summary("")["total"], 0)

    def test_repo_table_matches_check_acceptance_counts(self):
        import check_acceptance

        with open(status.AC_FILE, encoding="utf-8") as f:
            text = f.read()
        rows = [r for r in check_acceptance.parse(text) if r["status"] != "deferred"]
        s = status.ac_summary(text)
        self.assertEqual(s["total"], len(rows))
        self.assertEqual(s["done"], sum(1 for r in rows if r["status"] == "done"))


class Render(unittest.TestCase):
    def body(self):
        data = status.collect(offline=True)
        data["ac"] = status.ac_summary(TABLE)
        return status.render(data)

    def test_progress_line(self):
        self.assertIn("## 📈 Progress   █████░░░░░ 2/4 acceptance criteria done (50%)", self.body())

    def test_sections_in_order(self):
        body = self.body()
        order = ["## 🎯 Goal", "## 🙋 Needs you", "## 📈 Progress", "## 🔨 In progress",
                 "## 📋 Up next", "## ✅ Recently done", "## ⚠️ Stuck", "_Updated "]
        self.assertEqual(sorted(order, key=body.index), order)

    def test_empty_states(self):
        self.assertIn("Nothing. 🎉", self.body())


if __name__ == "__main__":
    unittest.main(verbosity=2)

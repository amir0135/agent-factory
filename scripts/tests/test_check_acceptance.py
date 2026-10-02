#!/usr/bin/env python3
"""Harness self-test: acceptance table parsing with optional Journey cells."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import check_acceptance  # noqa: E402


def table(header, row):
    return f"""<!-- AC-TABLE:START -->
| {header} |
|---|---|---|---|---|
| {row} |
<!-- AC-TABLE:END -->"""


class AcceptanceJourney(unittest.TestCase):
    def test_legacy_table_without_journey(self):
        rows = check_acceptance.parse(
            table(
                "ID | Feature | Criterion | Verify | Status",
                "AC-001 | booking | Member books a class | `pytest` | todo",
            )
        )
        self.assertEqual(rows[0]["journey"], "")
        self.assertEqual(rows[0]["verify"], "pytest")

    def test_journey_column_is_optional_and_position_independent(self):
        rows = check_acceptance.parse(
            table(
                "ID | Feature | Journey | Criterion | Status | Verify",
                'AC-001 | booking | open /classes > click "Book" | Member books a class | done | `pytest`',
            )
        )
        self.assertEqual(rows[0]["journey"], 'open /classes > click "Book"')
        self.assertEqual(rows[0]["verify"], "pytest")
        self.assertEqual(rows[0]["status"], "done")


if __name__ == "__main__":
    unittest.main(verbosity=2)

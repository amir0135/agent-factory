#!/usr/bin/env python3
"""Harness self-test: serve contract skip and startup-failure reporting."""
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVE = os.path.join(ROOT, "scripts", "serve.sh")


class ServeContract(unittest.TestCase):
    def run_serve(self, **overrides):
        env = os.environ.copy()
        env.update(overrides)
        return subprocess.run(
            ["bash", SERVE], cwd=ROOT, env=env, capture_output=True, text=True, timeout=10
        )

    def test_none_mode_skips_server(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_serve(SERVE_MODE="none", EVAL_DIR=tmp)
        self.assertEqual(result.returncode, 0)
        self.assertIn("serve: none", result.stdout)

    def test_failed_start_reports_log_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_serve(
                SERVE_MODE="app",
                SERVE_CMD="echo expected-startup-error >&2; exit 1",
                SERVE_URL="http://127.0.0.1:1",
                HEALTH_PATH="/",
                HEALTH_TIMEOUT_SECONDS="3",
                EVAL_DIR=tmp,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected-startup-error", result.stderr)
        self.assertIn("failed to become healthy", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

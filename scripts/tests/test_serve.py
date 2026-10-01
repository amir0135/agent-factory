#!/usr/bin/env python3
"""Harness self-test: serve contract skip and startup-failure reporting."""
import os
import signal
import socket
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

    def test_healthy_app_prints_base_url(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_serve(
                SERVE_MODE="app",
                SERVE_CMD=f"exec python3 -m http.server {port} --bind 127.0.0.1",
                SERVE_URL=f"http://127.0.0.1:{port}",
                HEALTH_PATH="/",
                HEALTH_TIMEOUT_SECONDS="5",
                EVAL_DIR=tmp,
            )
            try:
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"BASE_URL=http://127.0.0.1:{port}", result.stdout)
            finally:
                with open(os.path.join(tmp, "app.pid"), encoding="utf-8") as pid_file:
                    os.kill(int(pid_file.read()), signal.SIGTERM)

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

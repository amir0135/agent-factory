# App run contract

The planner fills this contract during onboarding for every UI or HTTP API app.
Libraries and CLIs without a local user-facing server set `SERVE_MODE=none`.

Set the app command, fixed loopback URL (including its port), and health-check
path below. `scripts/serve.sh` starts the command and waits for the health check.

```ini
SERVE_MODE=none
SERVE_CMD=
SERVE_URL=http://127.0.0.1:3000
HEALTH_PATH=/
```

Keep the server bound to `localhost` or `127.0.0.1`. The command runs in the
background and logs to `/tmp/eval/app.log`.

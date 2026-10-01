#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

RUN_CONFIG_FILE=${RUN_CONFIG_FILE:-product/RUN.md}
EVAL_DIR=${EVAL_DIR:-/tmp/eval}
mkdir -p "$EVAL_DIR"

config_value() {
  awk -F= -v key="$1" '
    $1 == key {
      sub(/^[^=]*=/, "")
      gsub(/^[[:space:]]+|[[:space:]]+$/, "")
      gsub(/^["'\'']|["'\'']$/, "")
      print
      exit
    }
  ' "$RUN_CONFIG_FILE"
}

SERVE_MODE=${SERVE_MODE:-$(config_value SERVE_MODE)}
SERVE_CMD=${SERVE_CMD:-$(config_value SERVE_CMD)}
SERVE_URL=${SERVE_URL:-$(config_value SERVE_URL)}
HEALTH_PATH=${HEALTH_PATH:-$(config_value HEALTH_PATH)}
HEALTH_TIMEOUT_SECONDS=${HEALTH_TIMEOUT_SECONDS:-60}

if [[ "$SERVE_MODE" == "none" || -z "$SERVE_MODE" ]]; then
  echo "serve: none"
  exit 0
fi
if [[ "$SERVE_MODE" != "app" || -z "$SERVE_CMD" || -z "$SERVE_URL" ]]; then
  echo "Invalid app run contract in $RUN_CONFIG_FILE (expected SERVE_MODE=app, SERVE_CMD, and SERVE_URL)." >&2
  exit 1
fi
if [[ ! "$SERVE_URL" =~ ^http://(localhost|127\.0\.0\.1):[0-9]+$ ]]; then
  echo "SERVE_URL must use a fixed port on localhost or 127.0.0.1: $SERVE_URL" >&2
  exit 1
fi

LOG_FILE="$EVAL_DIR/app.log"
PID_FILE="$EVAL_DIR/app.pid"
nohup bash -c "$SERVE_CMD" >"$LOG_FILE" 2>&1 </dev/null &
echo "$!" >"$PID_FILE"

if [[ "$HEALTH_PATH" != /* ]]; then HEALTH_PATH="/$HEALTH_PATH"; fi
HEALTH_URL="${SERVE_URL%/}${HEALTH_PATH}"
deadline=$((SECONDS + HEALTH_TIMEOUT_SECONDS))
while (( SECONDS < deadline )); do
  if curl --silent --show-error --fail --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
    echo "App is healthy: $SERVE_URL"
    echo "BASE_URL=$SERVE_URL"
    exit 0
  fi
  if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    break
  fi
  sleep 1
done

echo "App failed to become healthy at $HEALTH_URL. Startup log tail:" >&2
tail -60 "$LOG_FILE" >&2 2>/dev/null || true
exit 1

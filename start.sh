#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

npm run dev

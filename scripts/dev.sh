#!/usr/bin/env bash
# Start all three services: voice (8100), backend (8000) and UI (5173).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDS=()

cleanup() {
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt

# Optional neural voice. Skipped automatically if the environment is missing.
if [ -x .tts-venv/bin/uvicorn ]; then
  .tts-venv/bin/uvicorn voice_service.app:app --port 8100 &
  PIDS+=($!)
  echo "voice    -> http://127.0.0.1:8100"
else
  echo "voice    -> skipped (run 'make setup-voice' for the neural voice)"
fi

.venv/bin/uvicorn app.main:app --reload --port 8000 &
PIDS+=($!)
echo "backend  -> http://127.0.0.1:8000"

cd "$ROOT/frontend"
if [ ! -d node_modules ]; then
  npm install
fi
echo "frontend -> http://127.0.0.1:5173"
npm run dev

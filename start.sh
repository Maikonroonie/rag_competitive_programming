#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  [[ -n "${FRONTEND_PID}" ]] && kill "${FRONTEND_PID}" 2>/dev/null || true
  [[ -n "${BACKEND_PID}" ]] && kill "${BACKEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if [[ ! -x "${ROOT}/backend/.venv/bin/uvicorn" ]]; then
  echo "Run first: cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

if [[ ! -d "${ROOT}/frontend/node_modules" ]]; then
  echo "Run first: cd frontend && npm install"
  exit 1
fi

cd "${ROOT}/backend"
.venv/bin/uvicorn app.main:app --port 8000 &
BACKEND_PID=$!

cd "${ROOT}/frontend"
npm run dev &
FRONTEND_PID=$!

echo "Backend:  http://localhost:8000  (docs: /docs)"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop."

wait "${BACKEND_PID}" "${FRONTEND_PID}"

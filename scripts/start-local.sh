#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Starting MediVault local stack"

# Backend
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt
else
  . .venv/bin/activate
fi
[ -f .env ] || cp .env.example .env

# Seed demo users if DB empty
python scripts/seed_demo.py || true

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Frontend
cd "$ROOT/frontend"
[ -f .env.local ] || cp .env.local.example .env.local
npm run dev -- --port 3000 &
FRONTEND_PID=$!

echo ""
echo "MediVault running:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Demo accounts (password: password123)"
echo "  Patient: patient@demo.medivault"
echo "  Doctor:  doctor@demo.medivault"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

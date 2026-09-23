#!/usr/bin/env bash
set -e

echo "========================================"
echo "  CampusOS Local Development Startup   "
echo "========================================"

# Backend setup
if [ ! -d "apps/api/.venv" ]; then
    echo "Creating Python virtual environment in apps/api/.venv..."
    python3 -m venv apps/api/.venv
    apps/api/.venv/bin/pip install -r apps/api/requirements-dev.txt
fi

# Frontend setup
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

echo "Starting Backend API (:8000)..."
(cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8000) &
API_PID=$!

echo "Starting Frontend Web (:3000)..."
npm run dev --workspace=apps/web &
WEB_PID=$!

trap "kill $API_PID $WEB_PID" EXIT
wait

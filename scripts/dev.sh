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

echo "Starting CampusOS Unified Full-Stack (Backend :8000 + Frontend :3000)..."
node scripts/dev.mjs

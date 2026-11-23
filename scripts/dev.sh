#!/usr/bin/env bash
set -e

echo "========================================"
echo "  CampusOS Local Development Startup   "
echo "========================================"

# Backend setup
if [ ! -d "backend/.venv" ]; then
    echo "Creating Python virtual environment in backend/.venv..."
    python3 -m venv backend/.venv
    backend/.venv/bin/pip install -r backend/requirements-dev.txt
fi

# Frontend setup
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

echo "Starting CampusOS Unified Full-Stack (Backend :8000 + Frontend :3000)..."
node scripts/dev.mjs

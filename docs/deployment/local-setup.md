# CampusOS — Local Environment & Development Guide

This guide describes how to run and verify CampusOS locally on developer workstations (Windows, macOS, Linux).

---

## 1. Prerequisites

- **Node.js**: `v20.0.0` or higher (verified on Node `v26.x`)
- **npm**: `v10.0.0` or higher (verified on npm `11.x`)
- **Python**: `3.11.0` or higher (verified on Python `3.11.9`)
- **Git**

---

## 2. Directory & Environment Configuration

### Step A: Clone & Workspace Initialization

Ensure you are in the project root:

```bash
git status
```

### Step B: Backend Configuration

```bash
# In apps/api
cd apps/api
cp .env.example .env
```

Default local environment values:

```ini
ENVIRONMENT=development
PROJECT_NAME="CampusOS API"
API_V1_STR="/api/v1"
CORS_ORIGINS=["http://localhost:3000"]
DATABASE_URL=postgresql+asyncpg://campusos_user:campusos_password@localhost:5432/campusos_db
SECRET_KEY=campusos_insecure_local_dev_secret_key_change_in_production
```

### Step C: Frontend Configuration

```bash
# In apps/web
cd ../web
cp .env.example .env.local
```

Default local values:

```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 3. Running Locally

### Option 1: Native Local Processes (Recommended without Docker)

#### Terminal 1 — Backend API

```bash
cd apps/api
python -m venv .venv

# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API Health Check: `http://localhost:8000/api/v1/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

#### Terminal 2 — Frontend Application

```bash
# From workspace root
npm install
npm run dev --workspace=apps/web
```

- Frontend Web App: `http://localhost:3000`

---

## 4. Linting and Code Quality

### Frontend Lint & Format

```bash
npm run lint --workspace=apps/web
npm run format:check
```

### Backend Lint & Typecheck

```bash
cd apps/api
ruff check .
pytest
```

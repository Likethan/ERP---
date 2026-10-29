# CampusOS

> **One Campus. One System. One Source of Truth.**

CampusOS is an enterprise-grade College ERP / Campus Operating System designed to unify student lifecycle management, faculty operations, academic governance, attendance tracking, examination workflows, financial billing, placement drives, campus events, hostel/transport logistics, institutional documentation, and role-guarded campus intelligence.

Initially architected for a single high-scale institution, CampusOS is fundamentally structured to scale into a multi-tenant SaaS platform serving diverse colleges and universities with strict tenant data isolation.

---

## 🏛️ Core Design Principles

1. **Unified Core Entities**: A `Student` is a single source of truth across all modules (Attendance, Academics, Examination, Fees, Placement, Documents, Events), eliminating cross-module data duplication.
2. **Modular Monolith**: Clean, domain-driven boundaries in a unified repository, maximizing development velocity while maintaining strict decoupled architectural layers.
3. **Multi-Tenancy Readiness**: Row-Level Isolation backed by `tenant_id` context and database security policies, ensuring seamless migration to schema or database isolation without rewriting domain models.
4. **Zero Client-Side Trust**: Authentication and fine-grained authorization (RBAC + PBAC) are rigorously enforced at backend API route guards. Frontend role checks only govern presentation.
5. **Role-Driven Dashboards**: Dedicated operational views tailored for Super Admin, Principal / Management, HOD, Faculty, Accounts, Placement Officers, Students, and Parents.
6. **Ambient Intelligence Layer**: AI capabilities operate strictly through permission-guarded tools and domain services, never executing uncontrolled queries directly against storage.

---

## 📂 Repository Structure

```text
campusos/
├── apps/
│   ├── api/                      # Backend: Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic
│   └── web/                      # Frontend: Next.js 15 (App Router), TypeScript, Tailwind CSS
├── packages/
│   ├── config/                   # Shared linting, formatting, and TypeScript configs
│   └── types/                    # Shared TypeScript interfaces & API contracts
├── docs/                         # Architecture, security, database, and UX documentation
│   ├── product/                  # Vision, scope, and roadmap
│   ├── architecture/             # Monolith design & domain boundaries
│   ├── database/                 # Multi-tenancy isolation & entity relationships
│   ├── api/                      # REST standards & error formats
│   ├── security/                 # AuthN/AuthZ & RBAC/PBAC matrix
│   ├── ux/                       # Design system tokens & role-specific dashboards
│   ├── ai/                       # AI assistant tool boundaries & RAG design
│   ├── deployment/               # Local setup & production topology
│   └── decisions/                # Architecture Decision Records (ADRs)
├── infrastructure/               # Container definitions & deployment configs
├── scripts/                      # Developer automation scripts (cross-platform & PowerShell)
├── docker-compose.yml            # Local supporting services (PostgreSQL, Redis, MinIO)
├── package.json                  # Monorepo workspaces definition
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js**: `>= 20.0.0` (Tested on Node.js v22/v26)
- **npm**: `>= 10.0.0`
- **Python**: `>= 3.11.0` (Tested on Python 3.11 & 3.12)
- **PostgreSQL 16+** & **Redis 7+** (Optional for local testing; SQLite in-memory and local cache fallbacks are included)

---

### Quick Start (Local Development)

#### 1. Setup Environment Files

```bash
# Backend environment template
cp apps/api/.env.example apps/api/.env

# Frontend environment template
cp apps/web/.env.example apps/web/.env.local
```

#### 2. Install & Start Backend API (`apps/api`)

```bash
cd apps/api

# Create & activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
# source .venv/bin/activate

# Install runtime and development dependencies
pip install -r requirements-dev.txt

# Run forward schema migrations (against PostgreSQL when configured)
# alembic upgrade head

# Start FastAPI ASGI server
uvicorn app.main:app --reload --port 8000
```

- **Interactive API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Contract Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Liveness Probe:** [http://localhost:8000/api/v1/health/live](http://localhost:8000/api/v1/health/live)
- **Readiness Probe:** [http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready)

#### 3. Install & Start Frontend Web Application (`apps/web`)

```bash
# In the repository root:
npm install

# Start Next.js development server
npm run dev --workspace=apps/web
```

- **Web Application Portal:** [http://localhost:3000](http://localhost:3000)
- **Multi-Role Entry Portal:** [http://localhost:3000/login](http://localhost:3000/login)

#### 4. Background Workers & Distributed Scheduler

```bash
cd apps/api

# Run transactional outbox batch worker (processes pending domain events)
python -m app.worker

# Run distributed scheduler (sweeps maintenance schedules, overdue invoices, escalation SLAs)
python -m app.scheduler
```

---

## 🧪 Testing & Quality Assurance

CampusOS maintains strict, evidence-based test suites ensuring 100% test pass rates across both applications with zero mock workarounds:

### 1. Backend Automated Tests (747 Tests)
```bash
cd apps/api

# Run complete backend pytest suite (all 63 test files)
.venv\Scripts\python.exe -m pytest -q

# Run specific domain test suites:
.venv\Scripts\python.exe -m pytest tests/test_core_and_people.py -v
.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_saas_isolation.py -v
.venv\Scripts\python.exe -m pytest tests/test_security_hardening.py -v
.venv\Scripts\python.exe -m pytest tests/test_enterprise_database_migrations.py -v
.venv\Scripts\python.exe -m pytest tests/test_enterprise_asset_lifecycle.py -v
.venv\Scripts\python.exe -m pytest tests/test_enterprise_student_housing_step66.py -v
.venv\Scripts\python.exe -m pytest tests/test_enterprise_sustainability_step67.py -v
.venv\Scripts\python.exe -m pytest tests/test_enterprise_campus_security_step68.py -v
```

### 2. Frontend Test Suites (21 Suites)
```bash
cd apps/web

# Run all 21 frontend test suites:
node ../../scratch/run_all_frontend_tests.mjs

# Or run individual test suite using tsx:
npx tsx src/__tests__/auth-login-portal.test.ts
npx tsx src/__tests__/academics-module.test.ts
npx tsx src/__tests__/attendance-module.test.ts
npx tsx src/__tests__/campus-security-module.test.ts
npx tsx src/__tests__/housing-module.test.ts
npx tsx src/__tests__/sustainability-module.test.ts
```

### 3. Code Quality, Linting & Type Checking
```bash
# Backend lint check (Ruff 0.6+):
cd apps/api
.venv\Scripts\ruff.exe check app

# Frontend TypeScript strict type checking:
npx tsc --noEmit -p apps/web/tsconfig.json

# Frontend ESLint:
cd apps/web
npm run lint

# Production Next.js build (verifies static prerendering across all 251 routes):
cd apps/web
npm run build
```

---

## 🔐 Multi-Role Authentication & Demo Personas

The unified login experience at `/login` provides 5 dedicated entry experiences with built-in role scoping:

| Role Portal | Canonical Role | Demo Persona Email | Scope & Permissions |
| :--- | :--- | :--- | :--- |
| **Student Portal** | `STUDENT` | `aarav.patel@apextech.edu` | View personal attendance, grades, fee dues, timetable, housing requests. |
| **Faculty Portal** | `FACULTY` | `rajesh.sharma@apextech.edu` | Mark attendance rosters, enter marks, submit leave requests, view courses. |
| **HOD Portal** | `HOD` | `meenakshi.sundaram@apextech.edu` | Approve leaves, sign off mark corrections, review departmental health metrics. |
| **Vice Principal** | `PRINCIPAL` | `arvind.swaminathan@apextech.edu` | Institutional analytics, high-level accreditation snapshots, executive escalations. |
| **Administrator** | `SUPER_ADMIN` | `admin@apextech.edu` | Global campus management, security ops, billing, user role assignments. |

---

## 📦 Implemented Domain Modules (Steps 1–68)

CampusOS integrates 68 comprehensive enterprise domains:
1. **Core Organization:** Multi-campus hierarchy, departments, academic structures, degree programs.
2. **Academic Life:** Curricula (R-2024, R-2026), course offerings, timetable clash detection, student enrollments.
3. **Attendance Engine:** 75% threshold policy, session rosters, leave approvals, immutable audit logs.
4. **Examinations & Evaluation:** Internal/External rosters, lock/reopen flows, COE publication batches.
5. **Finance & Accounting:** Fee schedules, invoice ledgers, gateway reconciliation, printable vouchers with SHA-256 seals.
6. **Asset Lifecycle:** Commissioning, corrective work orders, depreciation schedules, inspection checklists.
7. **Transactional Outbox:** Guaranteed delivery, exponential backoff retries, dead-letter queue, sanitized payloads.
8. **Student Affairs & Support:** Confidential grievance intake, disciplinary hearings, appeals, IDP personal development plans.
9. **Global Mobility & Legal:** International partner universities, exchange applications, contract lifecycle risk matrix.
10. **Research & Sports:** Grant pipeline, milestone budget tracking, tournament brackets (Round Robin/Knockout), equipment checkouts.
11. **Student Housing (Step 66):** Off-campus landlords, bed telemetry, lease agreements, safety violation suspensions.
12. **Sustainability & Carbon (Step 67):** Scope 1/2/3 GHG accounting, IoT smart meters, TSDF hazardous waste tracking, CAPA permits.
13. **Campus Security (Step 68):** Visitor QR badges, NFC guard patrol checkpoint scans, hardware controller telemetry, emergency coordination.

---

## 📖 Architecture Documentation

Detailed architectural specifications and engineering standards are available in the [`docs/`](./docs) directory:

- [Product Overview](./docs/product/overview.md)
- [System Architecture](./docs/architecture/system-overview.md)
- [Domain Boundaries](./docs/architecture/domain-boundaries.md)
- [Database & Multi-Tenancy Strategy](./docs/database/multi-tenancy-strategy.md)
- [Security Architecture](./docs/security/architecture.md)
- [Production Deployment Runbook](./docs/deployment.md)
- [Production Security Checklist](./docs/production-security-checklist.md)
- [Disaster Recovery Plan](./docs/disaster-recovery.md)
- [Incident Response Plan](./docs/incident-response.md)
- [Database Backup & Restore](./docs/backup-restore.md)
- [Production Infrastructure Architecture](./docs/infrastructure.md)
- [Environment Configuration Strategy](./docs/environment-configuration.md)
- [Design System & UX Philosophy](./docs/ux/design-system.md)
- [AI Architecture & Guardrails](./docs/ai/architecture.md)
- [Architecture Decision Records (ADRs)](./docs/decisions/)

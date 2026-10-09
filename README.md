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

- **Node.js**: `>= 20.0.0`
- **npm**: `>= 10.0.0`
- **Python**: `>= 3.11.0`
- **PostgreSQL 16+** & **Redis 7+** (or Docker for containerized infrastructure)

### Quick Start (Local Development)

#### 1. Setup Environment Files

```bash
# Backend environment
cp apps/api/.env.example apps/api/.env

# Frontend environment
cp apps/web/.env.example apps/web/.env
```

#### 2. Start Backend API

```bash
cd apps/api
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API Documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)  
API Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

#### 3. Start Frontend Web Application

```bash
# In the root repository directory
npm install
npm run dev --workspace=apps/web
```

Web Application will be available at: [http://localhost:3000](http://localhost:3000)

#### 4. Supporting Infrastructure (Optional via Docker)

```bash
docker compose up -d
```

Spins up PostgreSQL (`:5432`), Redis (`:6379`), and MinIO (`:9000` / Console `:9001`).

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

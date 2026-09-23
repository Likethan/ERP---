# CampusOS — System Architecture Overview

## 1. High-Level Architectural Topology

CampusOS adopts a **Modular Monolith** architecture. All domains live in a single unified codebase with strictly isolated domain packages, clear internal interfaces, and decoupled layers.

```text
┌─────────────────────────────────────────────────────────────┐
│                       Client Layer                          │
│          Next.js 15 (React 19, TypeScript, Tailwind)        │
│          App Router • Role-Specific Views • SSR & CSR       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / REST (JSON)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / FastAPI                    │
│   Rate Limiting • CORS • Request ID • Tenant Context Extr. │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
┌──────────────────────────────┐ ┌───────────────────────────┐
│     Security & Auth Engine   │ │   Audit & Logging Engine  │
│  JWT / Session • RBAC / PBAC │ │  Structured JSON Logging  │
└──────────────┬───────────────┘ └─────────────┬─────────────┘
               │                               │
               ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Modules                         │
│  Core • People • Academics • Attendance • Exams • Finance   │
│  Placement • Campus • Infrastructure • Docs • Intelligence  │
│                                                             │
│  [ Routers ] ──► [ Services ] ──► [ Repositories/Queries ]  │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
┌──────────────────────┐ ┌───────────┐ ┌─────────────────────┐
│    PostgreSQL 16     │ │  Redis 7  │ │  Object Storage     │
│ Shared DB / RLS      │ │ Cache/Jobs│ │ MinIO / S3 Docs     │
└──────────────────────┘ └───────────┘ └─────────────────────┘
```

---

## 2. Technology Stack Justification

### Frontend: Next.js (TypeScript, App Router, Tailwind CSS)

- **Why App Router**: Native server-side rendering (SSR) for initial loads and metadata, layout nesting for role-based navigation shells, and fast client-side transitions.
- **Why TypeScript (Strict)**: Elimination of runtime type errors across complex ERP forms, nested academic data structures, and status envelopes.
- **Why Tailwind CSS & shadcn/ui**: Unmatched flexibility for high-density, accessible, clean enterprise UI without the visual debt or runtime bloat of legacy UI frameworks.

### Backend: Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic

- **Why FastAPI**: High-performance asynchronous execution, native OpenAPI documentation generation, and seamless integration with Pydantic v2 validation.
- **Why SQLAlchemy 2.0 (Async)**: Expressive, type-annotated query building with support for advanced PostgreSQL features (JSONB, Row-Level Security, window functions).
- **Why Alembic**: Robust, versioned, scriptable database migrations ensuring schema evolvability without data corruption.

### Storage & Cache

- **PostgreSQL 16**: Industry-standard relational data integrity, ACID guarantees, Row-Level Security (RLS) for tenant isolation, and JSONB capabilities for audit metadata.
- **Redis 7**: High-speed session caching, real-time rate limiting counters, and background worker queues (Celery/ARQ).
- **S3 / MinIO**: Standardized object storage for student certificates, institutional circulars, and document attachments.

---

## 3. Communication Patterns

- **Frontend-to-Backend**: Strictly typed RESTful HTTP API with standardized JSON envelopes.
- **Internal Cross-Domain Calls**: Direct Python service invocations or in-memory domain events; no internal HTTP roundtrips between modules.
- **Future Extraction Path**: If a high-throughput domain (e.g., Attendance Processing or Real-Time Biometric Ingestion) demands independent scaling, its clean domain interface allows seamless migration to an independent microservice.

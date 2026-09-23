# ADR-001: Modular Monolith vs Microservices

## Status

**Accepted**

## Context

Educational ERP systems encompass numerous interconnected domains: Students, Faculty, Courses, Attendance, Fees, Examinations, Placements, and Documents. A critical decision at the genesis of CampusOS is choosing between a **Distributed Microservices Architecture** and a **Modular Monolith**.

Microservices introduce significant network latency, distributed transaction complexities (Saga patterns / eventual consistency across student registrations and fee payments), duplicate entity models, high DevOps operational burden, and complex deployment pipelines.

Conversely, poorly structured monoliths ("Big Ball of Mud") lead to tight coupling, boundary erosion, and hard-to-maintain dependencies.

## Decision

CampusOS will be architected as a **Modular Monolith** using Python (FastAPI) and a Next.js frontend within a single monorepo.

- Code is organized strictly by business domains (`app/domains/{core, people, academics, ...}`).
- Cross-domain calls occur through explicit Python service interfaces. Direct cross-domain database table mutations are strictly prohibited.
- Shared infrastructure (PostgreSQL, Redis) supports all domains.

## Consequences

### Positive

- Direct atomic database transactions across interconnected operations (e.g., student admission + fee invoice creation).
- Simplified single-command local development setup.
- Zero network serialization overhead between internal modules.
- Single unified migration history via Alembic.

### Negative / Tradeoffs

- Requires discipline to prevent developers from bypassing domain boundaries (enforced through architectural code reviews and linting rules).
- Independent scaling of single domains is not initially possible without scaling the entire API process (mitigated by clean boundaries which allow future extraction of hot services like real-time attendance ingestion).

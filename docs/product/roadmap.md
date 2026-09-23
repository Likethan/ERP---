# CampusOS — Phased Product Roadmap

To guarantee stability, maintainability, and zero technical debt, CampusOS is implemented incrementally across carefully staged milestones.

---

## Phase Overview

```text
Step 1: Product Architecture & Project Foundation (Current)
   │
Step 2: Core Domain & Tenant Hierarchy (Institutions, Campuses, Departments, Programs)
   │
Step 3: Identity, Authentication & Granular RBAC/PBAC (Users, Roles, Permissions, JWT)
   │
Step 4: People Domain (Unified Student, Faculty, Staff, Parent Profiles)
   │
Step 5: Academic Operations (Curriculum, Courses, Semesters, Sections, Timetable)
   │
Step 6: Attendance Management (Sessions, Biometric/Web Logging, Leave Workflows)
   │
Step 7: Examination & Evaluation (Internal Assessments, Grade Scales, Result Processing)
   │
Step 8: Finance & Billing (Fee Structures, Invoicing, Payment Gateways, Receipts)
   │
Step 9: Career & Placements (Corporate Directory, Job Drives, Eligibility Filters, Offers)
   │
Step 10: Campus Life & Infrastructure (Hostel, Transport Routes, Clubs, Events)
   │
Step 11: Documents & Certification (Digital Repository, Certificate Generation, Verification)
   │
Step 12: Intelligence & Reporting (Institutional Analytics, Audit Trails, AI Assistant Layer)
   │
Step 13: Multi-Tenant SaaS Evolution (Self-service provisioning, custom subdomains, billing)
```

---

## Milestone Breakdown

### Phase 1: Foundation (Step 1 - Current)

- Monorepo setup with FastAPI backend, Next.js frontend, and shared types.
- Complete architectural blueprints, security frameworks, and domain boundaries.
- Local development workflow and health check verification.
- **Rule**: Zero fake modules or premature mock databases.

### Phase 2: Core Organization & Tenancy (Step 2)

- Multi-tenant data structures (`institutions`, `campuses`).
- Academic organizational tree: `departments`, `programs`, `academic_years`, `semesters`, `sections`.
- Database schema baseline with Alembic migrations.

### Phase 3: Identity & Access Governance (Step 3)

- Secure authentication engine (Argon2id password hashing, JWT in HttpOnly cookies).
- Fine-grained permission model (`domain:resource:action`).
- Session management, token refresh rotation, and rate limiting.

### Phase 4: People Registry (Step 4)

- Unified `users` table linked to polymorphic profile extensions: `students`, `faculty`, `staff`, `parents`.
- Roll number generation, admission tracking, and biographical data governance.

### Phase 5–11: Operational Domain Implementations

- Step-by-step rollout of academic, attendance, exam, finance, placement, infrastructure, and document modules.

### Phase 12–13: Intelligence & Scale

- Aggregated analytics dashboards for administrative leadership.
- Permission-guarded AI assistant with deterministic tool calling.
- Automated tenant onboarding and multi-institution isolation.

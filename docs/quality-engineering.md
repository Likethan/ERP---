# CampusOS Enterprise Quality Engineering Guide

## 1. Executive Summary & Quality Mandate

CampusOS is a mission-critical, multi-tenant enterprise college ERP platform serving higher education institutions ("One Campus. One System. One Source of Truth."). The platform governs sensitive institutional records, student academics, grading, financial ledger transactions, identity, campus operations, and SaaS platform administration.

**Quality Mandate:**
* **Correctness First:** Business logic in examinations, grades, fee allocation, and student lifecycles must be provably accurate and deterministic.
* **Strict Multi-Tenant Isolation:** Zero cross-tenant data leakage under any concurrent load, background execution, or administrative query.
* **Every Critical Workflow Testable:** Testing isolated endpoints is insufficient; end-to-end workflows connecting multiple domain modules must be continuously validated.
* **Evidence-Based Release Certification:** Releases cannot proceed based on assumptions; every release must be certified through verified test evidence, security audits, and contract checks.

---

## 2. Multi-Layer Quality Strategy

CampusOS employs a 12-layer quality pyramid ensuring defense-in-depth across the entire software delivery lifecycle:

```
                  ┌───────────────────────────────┐
                  │ 12. Release Certification     │  (Automated Certifier, Go/No-Go Gate)
                  ├───────────────────────────────┤
                  │ 11. Performance & Scalability │  (Load Test, Latency SLA, p95/p99)
                  ├───────────────────────────────┤
                  │ 10. Security & Hardening      │  (RBAC/PBAC, Threat Rules, Secret Scan)
                  ├───────────────────────────────┤
                  │  9. AI Quality & Safety       │  (Prompt Injection, RAG Context Bounds)
                  ├───────────────────────────────┤
                  │  8. Failure & Resilience      │  (Partial Writes, Rollback, Timeouts)
                  ├───────────────────────────────┤
                  │  7. Accessibility (a11y)      │  (WCAG 2.1 AA, Landmarks, Screen Reader)
                  ├───────────────────────────────┤
                  │  6. End-to-End User Journeys  │  (Playwright / Browser Flow Emulation)
                  ├───────────────────────────────┤
                  │  5. Cross-Module Workflows    │  (Multi-domain Lifecycle Integration)
                  ├───────────────────────────────┤
                  │  4. API Contracts & Schemas   │  (OpenAPI Spec, TypeScript Types Sync)
                  ├───────────────────────────────┤
                  │  3. Database & Migrations     │  (Alembic 001-020, Constraint Integrity)
                  ├───────────────────────────────┤
                  │  2. Service & Unit Tests      │  (Pytest, Async Fixtures, In-Memory DB)
                  ├───────────────────────────────┤
                  │  1. Static Analysis & Types   │  (Ruff, Prettier, TypeScript tsc, Mypy)
                  └───────────────────────────────┘
```

### Layer Breakdown

| Layer | Focus Area | Primary Tooling | Command | Pass Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **1. Static Analysis** | Formatting, style, dead code | Prettier, Ruff | `npm run format:check`<br>`ruff check apps/api` | 0 lint errors, 0 format diffs |
| **2. Type Checking** | Static type verification | TypeScript (`tsc`), Pydantic | `npm run typecheck --workspaces` | Zero compilation or type errors |
| **3. Unit & Service Tests**| Domain services, business rules | Pytest, AsyncSession | `pytest tests/` | 100% tests passing |
| **4. Database & Migrations**| Schema history, FKs, rollbacks | Alembic, SQLAlchemy | `alembic history`<br>`pytest tests/test_enterprise_database_migrations.py` | 0 broken migrations, FK constraints enforced |
| **5. API Contracts** | OpenAPI 3.1, TypeScript types | FastAPI OpenAPI, Pydantic | `pytest tests/test_enterprise_api_contracts.py` | OpenAPI valid, shared types in sync |
| **6. Multi-Tenant Isolation**| Cross-tenant boundary leaks | PBAC fixtures, Pytest | `pytest tests/test_saas_isolation.py` | Cross-tenant read/write blocked (403/404) |
| **7. Cross-Module Workflows**| End-to-end domain lifecycles | AsyncClient, Pytest | `pytest tests/test_enterprise_quality_workflows.py` | All 10 domain workflows pass |
| **8. Resilience & Failure** | DB drop, partial writes, timeouts | Custom adapters, Pytest | `pytest tests/test_enterprise_failure_injection.py` | Transactions atomic, fail-safe recovery |
| **9. AI Quality & Safety** | Prompt injection, unauthorized data | Governance Safety Module | `pytest tests/test_enterprise_ai_safety_eval.py` | Injections blocked, zero context leakage |
| **10. Security Operations** | Threat detection, containment | SOC engine, Scanner | `python scripts/security_scan.py`<br>`pytest tests/test_enterprise_security_operations.py` | 0 exposed secrets, all 9 rules active |
| **11. Accessibility** | WCAG 2.1 AA, ARIA landmarks | Custom auditor, Playwright | `python scripts/accessibility_audit.py` | 0 critical landmark or aria violations |
| **12. Release Certification**| Automated gate evaluation | Python certifier | `python scripts/release_certification.py` | Final verdict: PASS |

---

## 3. Critical Business Workflow Test Matrix

| ID | Business Workflow | Domain Modules Involved | Automated Verification Suite |
| :--- | :--- | :--- | :--- |
| **WF-01** | **Institution Onboarding & PBAC Security** | Core Institution, People, Roles, Permissions, Auth | `test_enterprise_quality_workflows.py::test_workflow_institution_onboarding_and_pbac` |
| **WF-02** | **Student & Faculty Administration** | People, Academics, Programs, Sections | `test_enterprise_quality_workflows.py::test_workflow_student_faculty_lifecycle` |
| **WF-03** | **Academic Lifecycle & Enrollment** | Academics, Programs, Courses, Offerings, Enrollments | `test_enterprise_quality_workflows.py::test_workflow_academic_lifecycle_and_enrollment` |
| **WF-04** | **Attendance Marking & Threshold Breaches** | Attendance, Notification, Academics | `test_enterprise_quality_workflows.py::test_workflow_attendance_sessions_and_threshold_alerts` |
| **WF-05** | **Examinations, Room Allocation & Marks** | Examinations, Assessments, Room Conflict, Debarment | `test_enterprise_quality_workflows.py::test_workflow_examinations_assessment_and_results` |
| **WF-06** | **Financial Ledgers & Payment Allocation** | Finance, Invoices, Payments, Receipts, Refunds | `test_enterprise_quality_workflows.py::test_workflow_finance_invoicing_and_payment_reconciliation` |
| **WF-07** | **Placement Drives & Job Applications** | Placement, Companies, Drives, Eligibility, Applications | `test_enterprise_quality_workflows.py::test_workflow_placement_drives_and_applications` |
| **WF-08** | **Campus Operations & Facility Bookings** | Campus, Events, Infrastructure, Facilities | `test_enterprise_quality_workflows.py::test_workflow_campus_facilities_and_events` |
| **WF-09** | **Document Management & Certificate Issuance**| Documents, Verification Desk, Certificates, Storage | `test_enterprise_quality_workflows.py::test_workflow_documents_verification_and_certificates` |
| **WF-10** | **AI Assistant & Permission-Bounded Retrieval** | Intelligence, AI Governance, Tool Invocation, Vectors | `test_enterprise_quality_workflows.py::test_workflow_ai_governance_and_tenant_bounds` |
| **WF-11** | **Tenant SaaS Operations & Quotas** | Platform Ops, Quotas, Lifecycle State Machine | `test_enterprise_quality_workflows.py::test_workflow_saas_tenant_lifecycle_and_quotas` |

---

## 4. Test Data & Environment Isolation Strategy

### 1. Synthetic Data Generation
* **Zero Production Data in Tests:** Synthetic UUIDs, deterministic names (e.g., `Apex Institute of Technology`, `Alan Turing`, `Student Alpha`), and synthetic email addresses (`user_<hex>@example.test`) are strictly enforced.
* **Deterministic Fixtures:** Centralized in [`apps/api/tests/conftest.py`](file:///c:/Users/Likethan%20KJ/Documents/project/VSB%20ERP/apps/api/tests/conftest.py).

### 2. Multi-Tenant Test Isolation
* Every isolation test provisions at least two active institutions (`tenant_a` and `tenant_b`) with distinct tenant IDs, distinct admin principals (`tenant_admin_a`, `tenant_admin_b`), and distinct user pools.
* Cross-tenant accesses are asserted for `404 Not Found` or `403 Forbidden` responses.

### 3. Database Isolation
* **Local Developer Environment:** Fast, isolated in-memory SQLite database via `sqlite+aiosqlite:///:memory:` with PostgreSQL JSONB and UUID compatibility compilers.
* **CI Environment:** Clean PostgreSQL 16 container service with isolated schemas.
* **Rollback & Drop:** Each test session creates tables, seeds system PBAC roles, and tears down cleanly.

---

## 5. Developer Guide: How to Run Tests Locally

### Quick Run
```bash
# Backend pytest suite (all 375+ tests)
cd apps/api
.venv\Scripts\pytest.exe -q

# Run specific domain test suite
.venv\Scripts\pytest.exe tests/test_academics.py -v

# Run with test coverage
.venv\Scripts\pytest.exe --cov=app --cov-report=term-missing

# Run Next.js type check
cd ../web
npm run typecheck

# Run Linting
npm run lint
```

### Full Quality & Release Certification Run
```bash
# Execute unified release certification
python scripts/release_certification.py
```

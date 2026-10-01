# Placement & Career Security Specification

The **Placement and Career Domain** within CampusOS manages corporate partnerships, compensation data, confidential interview scorecards, and student placement records. Security is enforced through multi-layered defense: multi-tenant database isolation, fine-grained RBAC/PBAC, zero client trust, deterministic server-side eligibility verification, and immutable audit trails.

---

## 1. Multi-Tenant Data Isolation

### 1.1 Tenant Scoping Model
All placement tables inherit from `TenantScopedModel`:
- `placement_companies`
- `placement_company_contacts`
- `placement_job_drives`
- `placement_job_positions`
- `placement_eligibility_rules`
- `placement_eligibility_snapshots`
- `placement_applications`
- `placement_application_histories`
- `placement_interview_rounds`
- `placement_interview_schedules`
- `placement_interview_evaluations`
- `placement_offers`
- `placement_outcomes`
- `placement_student_profiles`

### 1.2 Boundary Enforcement
- All ORM queries strictly filter by `tenant_id == current_tenant.id`.
- If an entity identifier belonging to another institution is supplied in a route parameter or foreign key payload, the domain service raises `TenantMismatchException` (HTTP 403 Forbidden).
- Cross-tenant data leakage is verified by automated integration tests (`test_cross_tenant_isolation_placement`).

---

## 2. Granular RBAC & PBAC Permissions

| Permission String | Purpose | Default Assigned Roles |
|---|---|---|
| `placement:companies:read` | View corporate partner directory | `SUPER_ADMIN`, `PLACEMENT_OFFICER`, `STUDENT`, `HOD` |
| `placement:companies:create` | Register new corporate recruiters | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:companies:update` | Update company information & tier | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:drives:read` | View drives and job positions | `SUPER_ADMIN`, `PLACEMENT_OFFICER`, `STUDENT`, `HOD` |
| `placement:drives:create` | Launch and configure recruitment drives | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:drives:update` | Edit recruitment drive dates and mode | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:drives:publish` | Transition drive to open application window | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:positions:manage` | Add or modify job roles and salary specs | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:eligibility:evaluate` | Evaluate student eligibility rules | `SUPER_ADMIN`, `PLACEMENT_OFFICER`, `STUDENT` |
| `placement:applications:read` | View candidate application pipelines | `SUPER_ADMIN`, `PLACEMENT_OFFICER`, `HOD`, `STUDENT` (own only) |
| `placement:applications:submit` | Submit application for open position | `STUDENT` |
| `placement:applications:update` | Shortlist or reject candidates | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:interviews:manage` | Schedule rounds, interviewers, and dates | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:interviews:evaluate` | Record interviewer ratings and feedback | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:offers:issue` | Issue official corporate offers | `SUPER_ADMIN`, `PLACEMENT_OFFICER` |
| `placement:offers:decide` | Accept or decline employment offer | `STUDENT` (own only) |
| `placement:profile:read` | View career preferences & resumes | `SUPER_ADMIN`, `PLACEMENT_OFFICER`, `STUDENT` (own only) |
| `placement:profile:write` | Update student skills and portfolio links | `STUDENT` |
| `placement:analytics:read` | Access placement CTC & tier analytics | `SUPER_ADMIN`, `PLACEMENT_OFFICER`, `HOD` |

---

## 3. Zero Client Trust & Server-Side Invariance

1. **Eligibility Invariance**: A student cannot bypass eligibility criteria by modifying client-side state. The server executes deterministic Python evaluations checking live transcripts (`SemesterExamResult`), attendance registers (`AttendanceSession`), and billing ledgers (`StudentInvoice`).
2. **Identity Invariance**: The candidate identifier is never read from client POST bodies in student-facing endpoints; it is resolved from the cryptographically verified JWT / Session identity (`current_user.id`).
3. **Double Application Prevention**: Unique composite database index `(tenant_id, job_position_id, student_id)` prevents race conditions or dual submission attempts.
4. **Offer Immutability**: Once an offer is accepted or declined, subsequent mutation attempts are rejected with `ValidationException`.

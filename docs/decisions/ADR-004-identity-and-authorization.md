# ADR-004: Identity and Authorization — Decoupling Authentication from Profile and Scoped PBAC

## Status

**Accepted**

## Context

Higher education institutions exhibit complex, multi-faceted human relationships:
- A user may join as an undergraduate student, graduate, become an alumnus, return as an adjunct faculty member, and subsequently become a permanent professor or Head of Department (HOD).
- A staff member or faculty member may also have a child studying at the institution, requiring parent portal access alongside their employee workflows.
- Administrative responsibilities are geographically and organizationally bounded: a faculty member may be appointed HOD of the Department of Computer Science & Engineering on the Main Campus, but should not possess administrative write authority over the Mechanical Engineering Department or a remote campus branch.

Coupling authentication credentials (email/password/sessions) directly into single-role tables (such as a legacy `students` or `teachers` table) causes immediate architectural failure when a human assumes multiple roles or transitions through institutional stages. Furthermore, naive role checks such as `if user.role == "HOD"` lack the necessary scope context (e.g. which department or campus).

## Decision

CampusOS decouples the physical authentication identity from operational institutional profiles and introduces scoped permission-based access control:

1. **Authentication Core (`people_users`)**:
   - Stores authentication credentials, password hashes (Argon2id), MFA status, global active flags, and primary contact information.
   - Represents the human login identity across the entire multi-tenant system.

2. **Distinct Institutional Profiles**:
   - Profiles are modeled as explicit child entities referencing `user_id`:
     - `StudentProfile` (`people_students`)
     - `FacultyProfile` (`people_faculty`)
     - `StaffProfile` (`people_staff`)
     - `GuardianProfile` (`people_guardians`)
   - A single `User` record can possess multiple profiles simultaneously without duplicating login credentials or audit identifiers.
   - Downstream operational domains (Attendance, Examination, Finance, Placement) link strictly to the specific profile identifier (e.g., `student_id: UUID`), preserving clean foreign key semantics.

3. **Fine-Grained Permissions (PBAC)**:
   - System permissions follow the atomic format `domain:resource:action` (e.g., `academics:courses:create`, `finance:invoices:approve`, `attendance:records:write`).

4. **Scoped Role Assignments (`people_user_roles`)**:
   - A role assignment maps a `user_id` to a `role_id` and is scoped by:
     - `tenant_id` (mandatory)
     - `campus_id` (optional; `NULL` implies all campuses within tenant)
     - `department_id` (optional; `NULL` implies all departments within campus)
   - Route authorization guards evaluate both the required atomic permission and the target entity's organizational scope.

## Consequences

### Positive
- A single login account smoothly supports alumni, faculty who are parents, and students who become teaching assistants.
- Granular administrative delegation: faculty can be granted HOD powers strictly for their department without granting institution-wide privileges.
- Standardized, auditable permission evaluations at every API gateway route.

### Negative / Tradeoffs
- Profile resolution requires querying profile tables or caching profile identifiers in the user session/JWT claims.
- Scope-aware authorization checks require evaluating request route parameters (e.g. validating that the target student belongs to the HOD's authorized department).

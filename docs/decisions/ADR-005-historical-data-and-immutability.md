# ADR-005: Historical Data Preservation and Immutability Architecture

## Status

**Accepted**

## Context

Educational institutions operate under stringent legal, statutory, and accreditation mandates (e.g., UGC, AICTE, NAAC, NBA, ABET). A common architectural flaw in legacy campus software is mutable in-place updates of operational fields:
- When a student is promoted from Semester 4 to Semester 5, or transferred from Section A to Section B, updating the foreign key directly on the `Student` record destroys past section and term history.
- When an instructor alters an assessment mark or an administrator corrects an attendance record, overwriting the record destroys the evidentiary audit trail.
- When a student moves from one hostel bed or transport route to another, overwriting the active allocation erases historical resource utilization and past fee entitlement proof.

## Decision

CampusOS establishes a strict **non-destructive historical preservation architecture**:

1. **Temporal Association / History Tables for Institutional Movements**:
   - **Student Term Enrollments (`people_student_semester_enrollments`)**: Every semester a student undertakes is recorded as a dedicated row capturing `academic_year_id`, `semester_id`, `section_id`, enrollment status, roll number, and date range. The `current_semester_id` and `current_section_id` on the `StudentProfile` act merely as operational pointers, never as the authoritative historical log.
   - **Resource Allocations (`HostelAllocation`, `TransportAllocation`)**: Physical resource assignments maintain `start_date`, `end_date`, and status flags (`ACTIVE`, `VACATED`, `TRANSFERRED`). Moving a student marks the previous allocation record as `VACATED` and inserts a new active row.

2. **Published Academic Records are Immutable**:
   - Semester exam results, marks cards, and official transcripts transition through a formal lifecycle: `DRAFT -> REVIEW -> APPROVED -> PUBLISHED`.
   - Once marked `PUBLISHED`, result records are strictly immutable. Any subsequent change (due to revaluation, dispute resolution, or administrative correction) must be issued via an audit-tracked `ResultCorrection` transaction with before/after snapshots, approved by the Controller of Examinations.

3. **Controlled Soft Deletion vs Status Transitions**:
   - Hard deletion (`DELETE FROM table`) is strictly prohibited on all operational, academic, financial, and regulatory entities.
   - Core entities use formal state machines (e.g., Student `APPLIED -> ADMITTED -> ACTIVE -> SUSPENDED -> GRADUATED -> ALUMNI`).
   - Soft deletion (`deleted_at TIMESTAMPTZ`) is reserved solely for non-financial, non-historical operational drafts (e.g. an unscheduled timetable draft or an unannounced club meeting).

4. **Dedicated System Audit Ledger (`intelligence_audit_logs`)**:
   - Captures actor identity, IP address, exact timestamp, target entity, old state JSON, new state JSON, and business justification for all modifications to core records.

## Consequences

### Positive
- Complete retrospective reporting: the institution can reconstruct the exact state of any student, class, section, room, or grade sheet at any historical point in time.
- Full compliance with international accreditation bodies and statutory government audits.
- Zero risk of accidental historical data loss during routine administrative promotions.

### Negative / Tradeoffs
- Increases database row volume; requires indexing on temporal fields (`start_date`, `end_date`, `is_active`) and composite tenant keys.
- Requires queries generating current student dashboards to join against active enrollment records or rely on cached current pointers.

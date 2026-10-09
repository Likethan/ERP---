# Enterprise Case Management (Step 25)

## Overview
A **Case** represents an operational matter that requires multi-step human coordination, document verification, stakeholder communication, or policy review.

```text
Case Lifecycle:
OPEN -> IN_PROGRESS -> [WAITING / ESCALATED] -> RESOLVED -> CLOSED
                                                    └── REOPENED ──┘
```

## Core Abstractions
1. **Case Types (`case_types`)**:
   Tenant-configurable classifications across academic and administrative modules:
   - `DOCUMENT_VERIFICATION`: Admissions credentials, identity proofs, certificates.
   - `FEE_REFUND`: Finance claims, withdrawal balances, adjustments.
   - `ATTENDANCE_CORRECTION`: Faculty or student attendance recalculations.
   - `EXAM_MARK_CORRECTION`: Revaluations, grade updates.
   - `HOSTEL_COMPLAINT`: Hostel facilities, plumbing, room allocation.
   - `FACILITY_ISSUE`: Infrastructure and laboratory equipment repairs.
   - `PLACEMENT_REVIEW`: Corporate interview disputes and offer verifications.
   - `STUDENT_SUPPORT`: General student counseling and grievance.

2. **Case Numbering**:
   Uses the Step 23 atomic sequence engine (`SequenceService.generate_next_sequence_number`), generating numbers like `CASE-2026-00001` under row-level database locking with yearly resets.

3. **Subject Entity References**:
   Cases do not duplicate domain records. They reference domain entities via `subject_entity_type` (e.g. `student`, `invoice`, `document`) and `subject_entity_id`.

4. **Case Relationships (`case_relationships`)**:
   Cases can be explicitly linked via directional relationship semantics:
   - `RELATED_TO`: General operational association.
   - `DUPLICATE_OF`: Redundant submission marked for closure.
   - `CHILD_OF`: Sub-case spawned from a parent issue.
   - `BLOCKED_BY`: Dependent on another case resolving first.
   - `DEPENDS_ON`: Upstream prerequisite case.
   - `ESCALATED_FROM`: Case spawned via escalation.

5. **Operational Timeline (`case_timeline_events`)**:
   A unified chronological event log capturing every lifecycle step:
   `CASE_CREATED`, `TASK_CREATED`, `TASK_ASSIGNED`, `TASK_CLAIMED`, `TASK_RELEASED`,
   `COMMENT_ADDED`, `DOCUMENT_ATTACHED`, `DECISION_MADE`, `ESCALATED`, `STATUS_CHANGED`,
   `CASE_RESOLVED`, `CASE_CLOSED`, `CASE_REOPENED`.

6. **Closure & Reopening Rules**:
   - A case cannot be resolved while uncompleted human tasks remain pending.
   - Resolving requires a mandatory `resolution_reason` and detailed `resolution_notes`.
   - Reopening requires an authoritative reason and increments `reopen_count`.

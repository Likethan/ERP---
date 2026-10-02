# CampusOS Result Finalization & Publication Architecture

This document outlines the governance, administrative controls, and visibility safeguards governing examination result finalization and deliberate publication to student portals.

---

## 1. Result Lifecycle & State Machine

```text
[Course Offering Marks Finalized]
                 │
                 ▼
     [Result Compilation / GPA Calculation]
                 │
                 ▼
        [RESULT: DRAFT] (Visible only to Admin / COE / HOD)
                 │
   (Moderation & Scrutiny Committee Review)
                 │
                 ▼
        [RESULT: FINALIZED]
                 │
 (Controller of Examinations Creates Publication Batch)
                 │
                 ▼
     [BATCH: READY FOR RELEASE]
                 │
      (Deliberate "Publish" Action)
                 │
                 ▼
       [BATCH: PUBLISHED]
                 │
    (Results Visible in Student 360 & Portals)
                 │
  (Emergency Revocation if Flagged for Anomaly)
                 │
                 ▼
        [BATCH: REVOKED]
```

---

## 2. Publication Batches Ledger

Located at `/app/examinations/publications`, this operational dashboard ensures that results are never leaked prematurely:

- **Batch Structure**: Groups candidates by `Examination Cycle`, `Academic Year`, `Semester`, and `Program` (e.g., `B.Tech Computer Science & Engineering - Semester 5 - Nov 2026`).
- **Batch States**:
  - `DRAFT`: Results being assembled and verified by departmental exam coordinators.
  - `READY`: Ratified by Academic Senate / COE; staged for release.
  - `PUBLISHED`: Deliberately released; public timestamps and ratifying officer logged.
  - `REVOKED`: Withdrawn from student view for moderation or grievance investigation.

---

## 3. Student Experience & Visibility Isolation

To maintain confidentiality and prevent premature grade exposure:

1. **Published Results Only**:
   - The student result interface query specifically filters:
     ```typescript
     results.filter((r) => r.studentId === studentId && r.isPublished);
     ```
   - Unfinalized, draft, or revoked results return `404 Not Found` or are excluded from student transcripts.

2. **Self-Only Scoping**:
   - Students can only view their own registered results; access to cohort-wide ledgers is strictly prohibited by role guards.

3. **Transcript View (`/app/examinations/results/[id]`)**:
   - For an authorized candidate, displays course credits, individual component breakdowns, weighted scores, letter grade, and grade point.
   - Administrative notes, moderation tags, and correction histories are hidden.

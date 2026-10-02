# CampusOS Marks Entry & Correction Workflows

This document describes the operational workflows, state machines, and UX patterns governing candidate scoring, validation, finalization locking, and supervised mark correction petitions.

---

## 1. Marks Lifecycle State Machine

```text
[NOT_ENTERED]
      │
      ├──────────────────┬─────────────────┐
      │ (Numeric Score)  │ (Absent Flag)   │ (Disciplinary)
      ▼                  ▼                 ▼
  [ENTERED]           [ABSENT]       [MALPRACTICE / WITHHELD]
      │                  │                 │
      └──────────────────┼─────────────────┘
                         ▼
             [Assessment Finalization]
                         ▼
               [LOCKED / FINALIZED]
                         │
        (Faculty Petition via Supervised Workflow)
                         ▼
             [Mark Correction Requested]
                         │
                 ┌───────┴───────┐
                 ▼               ▼
            [APPROVED]      [REJECTED]
                 │
                 ▼
         [Ledger Updated &
          Audit Trail Logged]
```

---

## 2. Marks Entry Matrix UX & Capabilities

Located at `/app/examinations/marks`, this interface is optimized for high-volume academic evaluations:

1. **Course & Assessment Selectors**:
   - Faculty selects assigned `Course Offering` and target `Assessment Scheme`.
   - The matrix automatically renders all enrolled students from Academic Management (`MOCK_STUDENTS`).

2. **Validation Safeguards**:
   - **Bounds Check**: Enforces `0 <= marksObtained <= maxMarks`. Negative numbers or scores exceeding component maximums display immediate red validation boundaries.
   - **Non-Numeric Cases**: Fast toggle buttons for `ABSENT`, `NOT_ATTEMPTED`, `WITHHELD`, and `MALPRACTICE`.
   - **Unsaved Changes Guard**: Prevents accidental tab closure or route switching when unsaved draft rows exist.
   - **Draft Auto-Save**: Allows faculty to save partial entries as drafts and return later.

---

## 3. Assessment Marks Finalization Lock

Finalization is an explicit administrative milestone:
- **Pre-requisite Validation**: All enrolled students must have their status accounted for (`ENTERED`, `ABSENT`, `WITHHELD`, or `MALPRACTICE`). An attempt to finalize with `NOT_ENTERED` students fails immediately with a validation dialog.
- **Lock Effect**: Once finalized, `isFinalized` is set to `true`. All numeric inputs are rendered as read-only. Casual editing is prohibited.

---

## 4. Supervised Mark Correction Workflow

After an assessment is locked, changes cannot occur silently:

1. **Petition Submission (Faculty)**:
   - Faculty initiates a **Request Mark Correction** dialog for a specific candidate.
   - Requires `Requested Mark`, `Requested Status`, and an explicit academic justification (e.g., *"Re-totalling error discovered in Question 3b (+5 marks)"*).
   - Status transitions to `PENDING`.

2. **Authoritative Review (HOD / Academic Council)**:
   - Head of Department reviews the petition with full context (original score, requested change, applicant notes).
   - Action: `APPROVE` or `REJECT` with reviewer notes.

3. **Automatic Ledger Synchronization**:
   - Upon HOD approval, `examinationsService` automatically updates the candidate's active `Mark` record in memory.
   - An immutable audit trail entry (`timeline`) records the date, time, approving authority, and rationale.

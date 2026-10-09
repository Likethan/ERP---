# Human-in-the-Loop (HITL) Operations & AI Integration (Step 25)

## Overview
CampusOS enforces strict separation between automated heuristics/AI assistance and authoritative institutional decisions.

```text
Automated Processing / AI Assistance
                 ↓
      Decision Boundary (HITL)
                 ↓
   Human Operator Judgment (Authoritative)
                 ↓
       State Progression & Audit
```

## Core HITL Principles
1. **Human Authority**:
   - Automated workflows pause whenever policy demands review, verification, or approval.
   - An AI model may suggest classification, summarize a case, or propose a resolution, but **never** completes a task or commits an institutional decision.
2. **Explicit Decision Entities**:
   - Human choices are recorded in `task_decisions` with immutable audit trails including actor ID, decision type, timestamp, and mandatory justification reason.
3. **Audit Immutability**:
   - Every human action (claim, release, reassign, delegate, decide, resolve, reopen) creates an append-only `case_timeline_events` entry and an immutable `audit_logs` record.
4. **Visibility & Privacy Scoping**:
   - Administrative case notes and internal deliberations use `INTERNAL` or `RESTRICTED` comment visibility, ensuring student or external submitters only see appropriate customer-facing notifications (`CASE_PARTICIPANT`).
5. **Delegated Authority Protection**:
   - Temporary delegation does not permanently transfer role ownership or allow bypassing PBAC boundaries. Delegations are time-bounded and audited.

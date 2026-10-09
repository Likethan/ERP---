# Enterprise Workflow Architecture (Step 25)

## Overview
CampusOS provides an enterprise-grade automated workflow and human-in-the-loop operations layer that separates automated event-driven/scheduled execution from long-running human operational case management.

```text
Workflow Definition (Immutable Versions)
         ↓
Workflow Execution Instance
         ↓
Automated Steps (Action, Condition, Notification, Wait)
         ↓
Human Tasks / Operational Cases (HITL Bridge)
         ↓
Authoritative Human Decisions
         ↓
Transitions & Terminal Completion
```

## Architectural Principles
1. **Reusability over Duplication**: Rather than creating duplicate workflow machinery, Step 25 builds upon the Step 17 `workflow_definitions` and `workflow_executions` foundation, adding first-class operational cases, work queues, and human tasks.
2. **Immutable Versioning**: Once activated, a workflow version's definition JSON is completely immutable. Edits generate a new version number (V1 -> V2). In-flight executions continue on their pinned version.
3. **Deterministic Idempotency**: Workflow dispatch enforces strict tenant-scoped idempotency keys (`uq_execution_tenant_idempotency`), preventing duplicate run dispatch.
4. **Human-in-the-Loop Bridge**: Any step requiring human institutional judgment yields an associated `HumanTask` and `Case`, pausing automated progression until an explicit human decision (`APPROVE`, `REJECT`, `RETURN`, `ESCALATE`) is recorded.

## Endpoints
- `GET /api/v1/workflows`: List workflow definitions.
- `POST /api/v1/workflows`: Create workflow definition in `DRAFT`.
- `GET /api/v1/workflows/{id}`: Retrieve workflow and active step graph.
- `POST /api/v1/workflows/{id}/activate`: Validate DAG graph and transition to `ACTIVE`.
- `POST /api/v1/workflows/{id}/execute`: Dispatch manual execution run.
- `POST /api/v1/workflow-instances/{id}/transition`: Bridge human decision to trigger state transition.

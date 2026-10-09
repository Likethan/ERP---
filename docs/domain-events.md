# CampusOS Domain Events System

## 1. Overview

CampusOS employs an asynchronous domain event model to notify workflow engines and background workers of meaningful business events without coupling domain services directly to workflow execution.

---

## 2. Central Event Registry

Events must belong to the central allowlist defined in `app/core/events.py`. User input may never specify unregistered event names.

| Event Type | Aggregate Type | Description |
|---|---|---|
| `STUDENT_CREATED` | Student | New student registered |
| `STUDENT_ENROLLED` | Enrollment | Student enrolled in course/section |
| `ATTENDANCE_THRESHOLD_REACHED` | AttendanceSummary | Student attendance fell below threshold |
| `ATTENDANCE_MARKED` | AttendanceSession | Session attendance marked by faculty |
| `EXAM_RESULT_PUBLISHED` | Assessment | Results approved and published |
| `INVOICE_GENERATED` | Invoice | Fee invoice issued to student |
| `INVOICE_OVERDUE` | Invoice | Invoice unpaid past due date |
| `PAYMENT_RECEIVED` | Payment | Fee payment confirmed |
| `DOCUMENT_EXPIRY_APPROACHING` | Document | Document nearing expiry date |
| `DOCUMENT_EXPIRED` | Document | Document validity expired |
| `PLACEMENT_DRIVE_OPENED` | PlacementDrive | Recruitment drive opened |
| `PLACEMENT_OFFER_ACCEPTED` | PlacementOffer | Student accepted employment offer |
| `EVENT_REGISTERED` | CampusEventRegistration | Member registered for campus event |
| `HOSTEL_ALLOCATION_CREATED` | HostelAllocation | Hostel room/bed assigned |

---

## 3. Payload Security & Minimization

In compliance with enterprise security requirements:
- Event payloads contain **identifiers and minimal metadata only** (`student_id`, `invoice_id`, `threshold`, `due_date`).
- Sensitive data (passwords, bank credentials, PII) is strictly stripped by `sanitize_event_payload`.
- Downstream workflow steps query authorized domain services using standard repositories to retrieve authorized data.

---

## 4. Event Dispatching to Workflows

When an event is processed:
1. `WorkflowService.dispatch_domain_event` finds all `ACTIVE` workflows belonging to the tenant configured with `trigger_type = EVENT` and matching `event_type`.
2. Each matching workflow is dispatched through `WorkflowService.execute_workflow` with the event payload supplied as execution context.
3. Step conditions and actions evaluate safely within the tenant context.

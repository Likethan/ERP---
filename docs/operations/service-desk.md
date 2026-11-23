# Enterprise Customer Support, Service Desk & SLA Management (Step 36)

## 1. Executive Summary & Core Principle

CampusOS is a multi-tenant university ERP platform serving institutional leadership, registrars, bursars, faculty, staff, students, and platform SRE operators. The Enterprise Service Desk manages inquiries, technical incidents, access requests, and configuration adjustments without compromising multi-tenant data isolation or disclosing internal investigation commentary.

**Core Principle:** *Every support request has an owner, every commitment is measurable, every escalation is traceable, and every resolution is verifiable.*

---

## 2. Architecture & Data Model

### 2.1 Database Entities (`app/models/support.py`)

1. **`SupportTeam` (`support_teams`)**:
   - Represents specialized resolution queues (e.g. `TIER_1_OPS`, `BURSAR_FINANCE`, `ACAD_OPERATIONS`, `SECURITY_IDENTITY`, `PLATFORM_SRE`).
   - Supports tenant-scoped teams or platform-wide queues (`is_platform_team=True`, `tenant_id=None`).
   - Tracks supervisor assignment and specialized ERP module tags.
2. **`SupportTeamMember` (`support_team_members`)**:
   - Agent membership within a team, tracking `is_team_lead`, real-time `is_available` flag, and `active_ticket_count`.
3. **`SupportSlaPolicy` (`support_sla_policies`)**:
   - Configurable SLA policies defining `response_target_minutes`, `resolution_target_minutes`, `business_hours_only`, and `escalation_threshold_pct`.
   - Supports fallback platform policies and tenant-specific override policies.
4. **`SupportTicket` (`support_tickets`)**:
   - Authoritative record with deterministic identifier (`TICK-YYYY-XXXXXX`).
   - Requester profile (`requester_id`, `requester_email`, `requester_name`, `requester_type`).
   - Taxonomy (`category`, `subcategory`, `request_type`, `priority`, `severity`, `status`).
   - Assignment (`assigned_team_id`, `assigned_agent_id`).
   - ERP correlation (`related_erp_module`, `related_resource_type`, `related_resource_id`, `related_incident_id`, `related_security_incident_id`).
   - SLA tracking (`sla_policy_id`, `response_due_at`, `resolution_due_at`, `sla_paused_at`, `sla_total_paused_minutes`, `sla_response_status`, `sla_resolution_status`).
   - Resolution & CSAT (`resolution_summary`, `closure_reason`, `reopen_reason`, `csat_rating`, `csat_feedback`).
5. **`SupportTicketMessage` (`support_ticket_messages`)**:
   - Time-stamped communication records strictly partitioned by `message_type`:
     - **`PUBLIC_REPLY`**: Customer-visible dialogue between requester and support agent.
     - **`INTERNAL_NOTE`**: Confidential diagnostics and supervisor collaboration, strictly filtered from tenant-facing APIs and notifications.
6. **`SupportTicketTimeline` (`support_ticket_timeline`)**:
   - Immutable audit log tracking state transitions, SLA pause/resume cycles, assignments, escalations, and incident links.
7. **`SupportTicketArticleLink` (`support_ticket_article_links`)**:
   - Knowledge base solution attachments with relevance scores and helpfulness feedback.

---

## 3. Support Request Lifecycle State Machine

```
                      +-------------------+
                      |        NEW        |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |      TRIAGED      |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |     ASSIGNED      |
                      +---------+---------+
                                |
                                v
                      +-------------------+
            +-------->|    IN_PROGRESS    |<--------+
            |         +----+---------+----+         |
            |              |         |              |
            |              v         v              |
            |   +--------------+ +-----------+      |
            |   | WAITING_FOR_ | |  ON_HOLD  |      |
            |   |  REQUESTER   | +-----+-----+      |
            |   +-------+------+       |            |
            |           |              |            |
            +-----------+--------------+            |
            |                                       |
            |         +-------------------+         |
            +-------->|     ESCALATED     |---------+
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |     RESOLVED      |
                      +----+---------+----+
                           |         |
                           v         v
                     +----------+ +--------+
                     | REOPENED | | CLOSED |
                     +----+-----+ +--------+
                          |
                          +---> (Loops back to IN_PROGRESS / TRIAGED)
```

### Transition Validation Rules

| Current Status | Permitted Target Statuses | Guard Conditions & Side Effects |
| :--- | :--- | :--- |
| **`NEW`** | `TRIAGED`, `ASSIGNED`, `CANCELLED` | Requires initial classification or direct queue routing. |
| **`TRIAGED`** | `ASSIGNED`, `IN_PROGRESS`, `CANCELLED` | Team or agent assigned; SLA assignment clock stamped. |
| **`ASSIGNED`** | `IN_PROGRESS`, `ON_HOLD`, `CANCELLED` | Agent accepts investigation work. |
| **`IN_PROGRESS`** | `WAITING_FOR_REQUESTER`, `WAITING_FOR_ENGINEERING`, `ON_HOLD`, `ESCALATED`, `RESOLVED`, `CANCELLED` | Clock pauses if transitioning to `WAITING_FOR_REQUESTER` or `ON_HOLD`. |
| **`WAITING_FOR_REQUESTER`**| `IN_PROGRESS`, `RESOLVED`, `CLOSED`, `CANCELLED` | SLA clock resumes; elapsed pause time is added to response and resolution deadlines. Requester reply automatically resumes ticket to `IN_PROGRESS`. |
| **`WAITING_FOR_ENGINEERING`**| `IN_PROGRESS`, `ESCALATED`, `RESOLVED` | Engineering investigation active; clock continues unless contractual pause is active. |
| **`ON_HOLD`** | `IN_PROGRESS`, `CANCELLED` | Clock pauses; resumes upon status change. |
| **`ESCALATED`** | `IN_PROGRESS`, `WAITING_FOR_ENGINEERING`, `RESOLVED` | Supervisor or Tier-3 queue assigned; escalation level incremented. |
| **`RESOLVED`** | `CLOSED`, `REOPENED` | Resolution summary mandatory; resolution SLA evaluated against deadline. |
| **`CLOSED`** | `REOPENED` | Formal closure; requester confirmation recorded. |
| **`REOPENED`** | `IN_PROGRESS`, `TRIAGED`, `ASSIGNED` | Reopen reason required; reopen count incremented. |
| **`CANCELLED`** | *(Terminal)* | Cancellation reason required. Clocks stopped. |

---

## 4. Categories & Automated Team Routing

CampusOS preconfigures 16 distinct support categories routed deterministically across 5 specialized support queues:

| Category | Typical Intake Inquiries | Default Assigned Queue |
| :--- | :--- | :--- |
| `ACCOUNT_ACCESS` | MFA resets, SSO synchronization, password lockouts | `SECURITY_IDENTITY` |
| `STUDENT_ADMIN` | Enrollment roster errors, demographic updates | `TIER_1_OPS` |
| `ACADEMIC_CONFIG` | Curriculum prerequisite rules, syllabus mapping | `ACAD_OPERATIONS` |
| `ATTENDANCE` | Biometric sync errors, leave calculation rules | `ACAD_OPERATIONS` |
| `EXAMINATIONS` | Grade lockouts, hall ticket generation, transcripts | `ACAD_OPERATIONS` |
| `FINANCE_FEES` | Payment gateway reconciliation, receipt generation | `BURSAR_FINANCE` |
| `PLACEMENTS` | Resume builder, drive registration, offer letters | `TIER_1_OPS` |
| `CAMPUS_OPERATIONS`| Hostel room allocation, library fine waiver | `TIER_1_OPS` |
| `DOCUMENTS_RECORDS`| Digital transcript signatures, certificate verification | `TIER_1_OPS` |
| `REPORTS_ANALYTICS`| Accreditation report generation, data exports | `PLATFORM_SRE` |
| `INTEGRATIONS_APIS`| Webhook delivery failures, LMS sync failures | `PLATFORM_SRE` |
| `AI_FEATURES` | Advisory engine hallucinations, embedding failures | `PLATFORM_SRE` |
| `PERFORMANCE_AVAIL`| Latency spikes, 504 Gateway Timeouts | `PLATFORM_SRE` |
| `DATA_MIGRATION` | Historical student record bulk import errors | `PLATFORM_SRE` |
| `FEATURE_REQUESTS` | Enhancement suggestions, new workflow requests | `TIER_1_OPS` |
| `GENERAL_ASSISTANCE`| Navigation guidance, portal orientation | `TIER_1_OPS` |

---

## 5. SLA Policy Engine & Clock Calculation

### 5.1 Targets by Priority

| Priority | Response Target (Default) | Resolution Target (Default) | Escalation Warning Threshold |
| :--- | :--- | :--- | :--- |
| **`URGENT`** | 30 minutes | 4 hours (240 mins) | 75% elapsed (180 mins) |
| **`HIGH`** | 60 minutes | 8 hours (480 mins) | 75% elapsed (360 mins) |
| **`MEDIUM`** | 240 minutes (4h) | 24 hours (1440 mins) | 75% elapsed (1080 mins) |
| **`LOW`** | 480 minutes (8h) | 48 hours (2880 mins) | 75% elapsed (2160 mins) |

### 5.2 Clock Calculation Rules

1. **Start Condition**: Response clock and resolution clock start immediately upon ticket creation (`created_at`).
2. **First Response Met Condition**: Triggered when an authorized support agent posts a `PUBLIC_REPLY`. Internal notes do not count toward response SLAs.
3. **Pause Condition**: When ticket moves to `WAITING_FOR_REQUESTER` or `ON_HOLD`:
   - `sla_paused_at = now()`
   - Clocks marked as `PAUSED`.
4. **Resume Condition**: When moving back to active status:
   - Paused duration in minutes: `paused_mins = (now() - sla_paused_at)`.
   - `sla_total_paused_minutes += paused_mins`.
   - `response_due_at += timedelta(minutes=paused_mins)`.
   - `resolution_due_at += timedelta(minutes=paused_mins)`.
   - Clocks revert to `ON_TRACK`.
5. **Breach Condition**: If `now() > response_due_at` before first response or `now() > resolution_due_at` before ticket resolution.

---

## 6. Multi-Tenant Isolation & Zero-Trust Security

1. **Tenant Context**:
   - Institution users (Student, Faculty, Staff) access only their own tickets (`ticket.requester_id == user.id`).
   - Institution Admins manage tickets within their primary institution (`ticket.tenant_id == user.primary_tenant_id`).
   - Platform Operators (`SUPER_ADMIN`, `PLATFORM_OPERATOR`) can inspect cross-tenant queues with audited justification.
2. **Internal Note Segregation**:
   - `SupportTicketMessage.message_type == INTERNAL_NOTE` is restricted to authorized support roles.
   - Requesters querying tickets receive messages strictly filtered to `PUBLIC_REPLY`.
   - Internal notes are never exposed via public API schemas or notifications.
3. **Incident Correlation Isolation**:
   - Support tickets may reference operational outages or security incidents (`related_incident_id`, `related_security_incident_id`).
   - Linking a security incident does not grant the requester access to restricted security evidence.

---

## 7. Ten Operational Support Runbooks

### Runbook 1: A New Support Request
1. **Intake & Triage**: System automatically validates mandatory fields, generates ticket number (`TICK-YYYY-XXXXXX`), and routes to target queue based on category.
2. **Verification**: Triage agent confirms category, priority, and tenant identity.
3. **Assignment**: Assigns ticket to an active specialist in the queue.
4. **Initial Response**: Specialist posts a public reply within the response SLA target.

### Runbook 2: Critical Service-Impacting Ticket
1. **Identification**: Category `PERFORMANCE_AVAIL` or `FINANCE_FEES` with priority `URGENT`.
2. **Incident Declaration**: Correlate ticket with active system incident (`INC-YYYY-XXXX`).
3. **Escalation**: Transition to `ESCALATED` and notify Platform SRE supervisor.
4. **Public Communication**: Post public reply acknowledging issue and providing incident tracking link.
5. **Internal Collaboration**: Use internal notes to coordinate backend mitigation steps.

### Runbook 3: An Approaching SLA Deadline
1. **Detection**: Automated SLA sweep detects resolution time remaining `< 25%` of threshold.
2. **Notification**: Priority alert dispatched to assigned agent and team lead.
3. **Action**:
   - If blocked on requester: transition to `WAITING_FOR_REQUESTER` to pause clock.
   - If blocked internally: reassign to senior engineer or escalate to Tier-3.

### Runbook 4: An SLA Breach
1. **Detection**: Scheduled SLA watcher marks `sla_response_status` or `sla_resolution_status` as `BREACHED`.
2. **Timeline Logging**: System records `SLA_BREACHED` audit timeline event.
3. **Supervisor Notification**: Automatic dispatch to operational desk manager.
4. **Remediation**: Manager performs root-cause review, reassigns resources, and logs justification note.

### Runbook 5: Incorrect Ticket Assignment
1. **Identification**: Assigned agent identifies issue belongs to another domain (e.g. fee reconciliation assigned to academics).
2. **Reassignment**: Agent navigates to Assignment panel, selects target team (`BURSAR_FINANCE`), and provides explanation notes.
3. **Audit**: System logs `ASSIGNED` timeline event with old team, new team, and rationale.

### Runbook 6: Requester Reopening a Resolved Ticket
1. **Trigger**: Requester tests resolution and finds recurrence; calls `/reopen` endpoint with reason.
2. **Validation**: Status transitions from `RESOLVED`/`CLOSED` to `REOPENED`.
3. **Clock Re-evaluation**: Reopen count incremented; ticket placed in high-priority triage queue.
4. **Investigation**: Previous agent reviews original resolution notes and investigates root cause.

### Runbook 7: Notification Provider Outage
1. **Symptom**: Webhook / email delivery failure logs detected in outbox processor.
2. **Procedure**:
   - Verify support ticket updates persist to database regardless of delivery outcome.
   - Outbox worker retries notification delivery with exponential backoff.
   - Agents utilize in-portal public replies directly so requesters see updates in portal upon login.

### Runbook 8: Recurring Integration Issue
1. **Pattern Detection**: Multiple tickets logged under `INTEGRATIONS_APIS` for a common institution.
2. **Incident Correlation**: Correlate all related tickets to a primary parent ticket or incident ID.
3. **Knowledge Base Linking**: Link approved troubleshooting article (e.g. `ART-101`) across all correlated tickets.
4. **Broadcast Resolution**: Once root cause resolved in ERP adapter, resolve parent incident and update child tickets.

### Runbook 9: Ticket Related to a Restricted Security Incident
1. **Intake**: Requester reports suspected account takeover or credential leak.
2. **Security Escalation**: Support agent links `related_security_incident_id` in backend.
3. **Strict Separation**: Security investigation evidence stored strictly in `security_incidents` table.
4. **Customer Communication**: Public replies provide safe guidance (e.g. "Session invalidated, please reset password") without disclosing vulnerability details or forensic logs.

### Runbook 10: Backlog Requiring Bulk Escalation
1. **Criteria**: Multiple tickets in queue exceeding age threshold due to regional outage.
2. **Procedure**:
   - Query tickets by `tenant_id` and `category`.
   - Reassign queue to designated incident recovery team.
   - Post mass status update explaining ongoing investigation.
   - Perform post-incident resolution sweep.

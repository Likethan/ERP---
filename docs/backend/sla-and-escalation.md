# Service Level Agreement (SLA) & Escalation Management (Step 25)

## Overview
CampusOS provides configurable Service Level Agreements (SLAs) with operational clocks, early warning triggers, breach detection, and automated escalation routing.

## SLA Policy Model (`sla_policies`)
Configurable duration targets based on priority and operational module:
- `URGENT`: 4 hours (240 minutes)
- `HIGH`: 8 hours (480 minutes)
- `NORMAL`: 48 hours (2880 minutes)
- `LOW`: 72 hours (4320 minutes)

Attributes:
- `warning_threshold_percentage`: Default 75% elapsed duration triggers `AT_RISK` status.
- `business_hours_only`: Enables calculation restricted to institutional working hours (default 09:00 - 18:00).
- `escalation_queue_id`: Target work queue for automated escalation on breach.
- `escalation_role`: Target authority role for notification.

## SLA Instance Clock (`sla_instances`)
Tracks real-time performance against commitments:
- `started_at`: Clock activation timestamp.
- `due_at`: Deadline threshold.
- `warning_at`: Early warning milestone (e.g. at 75%).
- `completed_at`: Resolution or decision recording timestamp.
- `elapsed_minutes`: Total elapsed operational time.
- `status`: `ON_TRACK`, `AT_RISK`, `BREACHED`, `PAUSED`, `MET`.
- `breached`: Boolean flag indicating deadline violation.
- `escalated`: Boolean flag indicating automated or manual escalation.

## Background Sweep & Automated Escalation
The scheduler runs periodic evaluations via `check_sla_deadlines_and_escalate`:
1. Identifies active instances where `now >= due_at`.
2. Marks `breached = True`, `status = BREACHED`.
3. Flips associated case/task status to `ESCALATED`.
4. Reroutes to `escalation_queue_id` if configured on the policy.
5. Emits `SLA_BREACHED` audit record and timeline entry.

# CampusOS — Intelligence Insights & Alert Center

## Overview

The **Intelligence Insights & Alert Center** (`/app/intelligence/insights` and `/app/intelligence/alerts`) acts as the proactive monitoring and recommendation engine for CampusOS. Rather than requiring users to manually search for bottlenecks, the system surfaces anomalies, compliance thresholds, and operational opportunities automatically.

---

## 1. Insights Architecture

### Insight Types & Classification

Insights are categorized across 9 institutional domains:
- `ATTENDANCE`: Chronic shortage, pattern anomalies, unexcused absence clusters.
- `ACADEMIC`: GPA dips, prerequisite failures, course drop surges.
- `FINANCE`: Fee collection lag, overdue fee ageing, unapplied scholarship waivers.
- `PLACEMENT`: Placement drive conversion drop, interview schedule conflicts, shortlist anomalies.
- `INFRASTRUCTURE`: Hostel occupancy imbalances, unresolved facilities maintenance SLA breaches.
- `DOCUMENT`: Verification backlog surge, missing mandatory admissions documents.
- `CAMPUS`: Low event participation, inactive student club governance.
- `EXAMINATION`: Grade anomalies, exam hall scheduling bottlenecks.
- `STUDENT`: Multi-domain holistic risk signals.

### Priority Levels

| Priority | Visual Treatment | Trigger Criteria |
|---|---|---|
| `CRITICAL` | Rose Badge + Pulse | Immediate statutory, financial, or academic risk (e.g. attendance < 60%) |
| `HIGH` | Amber Badge | Major operational bottleneck requiring review within 24 hours |
| `MEDIUM` | Indigo Badge | Trend anomaly requiring departmental coordination |
| `LOW` | Sky Badge | Informational opportunity or mild deviation |
| `INFO` | Slate Badge | Positive milestone or periodic summary |

### Status Lifecycle

```text
[NEW] ─── (Review Action) ───> [REVIEWED] ─── (Resolve Action) ───> [ACTIONED]
  │
  └────── (Dismiss Action) ───> [DISMISSED]
```

1. `NEW`: Newly generated insight awaiting staff attention.
2. `REVIEWED`: Acknowledged by faculty/officer; investigation underway.
3. `ACTIONED`: Remedial action executed in underlying module (e.g. notices issued).
4. `DISMISSED`: Rejected as non-actionable or false positive with audit reason.

---

## 2. Alert Center Architecture

### Alert Severities & Categories

Alerts represent urgent operational events requiring immediate operational triage.
Categories:
- `ATTENDANCE`: Sub-threshold attendance clusters before hall ticket generation.
- `ACADEMIC`: Failed prerequisites preventing semester registration.
- `FINANCE`: High-value invoice past 60 days overdue.
- `PLACEMENT`: Crucial drive registration deadline approaching with low signups.
- `INFRASTRUCTURE`: Water supply disruption or electrical failure in hostel blocks.
- `DOCUMENT`: Expiring affiliation licenses or statutory compliance certificates.
- `SYSTEM`: Data sync failure or simulated threshold anomaly.

Severities:
- `CRITICAL` (Red)
- `HIGH` (Amber)
- `WARNING` (Yellow)
- `INFO` (Blue)

### Alert Resolution Workflow

Each alert provides immediate human-in-the-loop action buttons:
- **Acknowledge**: Changes state to `ACKNOWLEDGED`, assigning current user as handler.
- **Resolve**: Marks as `RESOLVED`, archiving from the critical queue.
- **Dismiss**: Moves to `DISMISSED` with required comment.
- **Deep-Link**: Directly opens the affected student 360, course roster, or facility work order.

---

## 3. UI Surfaces

### Insight Cards (`src/components/intelligence/insight-card.tsx`)
- Displays title, domain badge, priority badge, relative timestamp.
- Concise summary with affected entity count (e.g. "18 students affected").
- Recommended operational remediation action.
- Action buttons: View 360 Details, Mark Reviewed, Save/Bookmark, Dismiss.

### Alert Cards (`src/components/intelligence/alert-card.tsx`)
- High-contrast alert header with severity badge and time elapsed.
- Affected record references and source domain indicator.
- Root cause statement and suggested mitigation steps.
- Quick resolution triggers directly on card or via modal workspace.

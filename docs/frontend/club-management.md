# CampusOS — Student Clubs & Organizations Governance

## 1. Overview

The **Clubs & Organizations** sub-module provides student societies, cultural teams, technical hack clubs, and entrepreneurship cells with institutional governance, membership approval pipelines, leadership hierarchies, and activity coordination.

---

## 2. Club Organization Entity

Every recognized student organization maintains:
- **Code & Name**: e.g., `ACE` (Association of Computer Engineers), `ROBOTICS` (Robotics & Mechatronics Society)
- **Category**: `TECHNICAL`, `CULTURAL`, `SPORTS`, `LITERARY`, `SOCIAL_SERVICE`, `ENTREPRENEURSHIP`, `SPECIAL_INTEREST`
- **Governance**:
  - `facultyCoordinator`: Faculty Advisor responsible for institutional compliance and approval workflows
  - `studentLead`: Student President / Convener responsible for daily club operations
- **Status**: `DRAFT`, `ACTIVE`, `INACTIVE`, `SUSPENDED`

---

## 3. Leadership Roles & Permission Hierarchy

Club membership operates across a defined role hierarchy:

| Role | Operational Scope | Administrative Rights |
| :--- | :--- | :--- |
| `FACULTY_COORDINATOR` | Faculty Oversight | Charter approval, final budget sign-off, disciplinary suspension |
| `CLUB_PRESIDENT` | Chief Executive Student Lead | Event creation, membership approval, executive appointments |
| `VICE_PRESIDENT` | Operational Deputy | Event logistics, attendee approvals, meeting coordination |
| `SECRETARY` | Records & Communications | Notice publishing, minutes of meeting, roster maintenance |
| `TREASURER` | Financial Records | Expenditure requests, co-curricular invoice matching |
| `EVENT_COORDINATOR` | Event Execution | Event attendance marking, pass verification |
| `MEMBER` | Standard Participant | Event access, meeting attendance, vote in internal elections |

---

## 4. Student Membership Lifecycle

```text
Discover Club in Directory
          ↓
Click "Join Club"
          ↓
Application Form (Motivation, Skills, Interests)
          ↓
Membership Status: PENDING
          ↓
Coordinator Review Desk:
    ├── APPROVE ──→ Status: ACTIVE (Role: MEMBER)
    └── REJECT  ──→ Status: REJECTED (With Reason)
          ↓
Promotion / Role Elevation (e.g. Promoted to SECRETARY)
          ↓
Voluntary Resignation ──→ Status: LEFT
```

### Self-Approval Prohibition
Students are strictly prevented from approving their own membership applications or elevating their own roles. All membership transitions are guarded by role checks and recorded in the club audit history.

---

## 5. Club Referenced Events

Clubs organize departmental workshops, hackathons, and cultural fests. In CampusOS:
- Events maintain a direct foreign reference to their host club (`clubId`, `organizerType: "CLUB"`).
- Events are never duplicated as separate club entities.
- Club details tab dynamically aggregates all referenced events scheduled or completed by the club.

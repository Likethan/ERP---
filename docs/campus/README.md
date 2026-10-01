# CampusOS — Campus Events, Clubs, Communication & Notification Engine

## Overview

The **Campus Events, Clubs, Communication & Notification Engine** (CampusOS Step 10) provides an institutional engagement, communication, and notification infrastructure. It serves as a campus-wide layer unifying physical activity scheduling, student organizations, targeted official circulars, and multi-channel notifications.

```
Campus
   ↓
Event / Club / Announcement
   ↓
Target Audience Resolution
   ↓
Registration / Membership Request
   ↓
Participation & Supervised Attendance Check-In
   ↓
Notification Dispatch Engine (In-App Center + Delivery State)
   ↓
Audit Trail & History Logging
```

---

## Subsystem Architecture

### 1. Event Management Engine
- **Taxonomy & Categorization**: Configurable `EventCategory` records (Hackathons, Workshops, Symposiums, Guest Lectures, Sports, Cultural).
- **Physical Venue Conflict Detection**: Prevents scheduling collisions across shared campus venues through deterministic interval checks `(start_a < end_b) AND (end_a > start_b)` and capacity validation.
- **Controlled Event Lifecycle**:
  `DRAFT` → `PUBLISHED` → `REGISTRATION_OPEN` → `REGISTRATION_CLOSED` → `ONGOING` → `COMPLETED` / `CANCELLED` / `ARCHIVED`.
- **Student Registration & Quota Enforcement**: Atomic registration codes, waitlist mechanisms, duplicate prevention, and departmental/program eligibility filtering.
- **Participation Attendance & Check-In**: Independent of daily academic attendance registers. Supports manual code verification, roll call, supervised undo, and time-bounded HMAC-SHA256 dynamic QR check-in tokens.

### 2. Clubs & Student Societies
- **Charter Governance & Lifecycle**:
  `DRAFT` → `PENDING_APPROVAL` → `ACTIVE` → `SUSPENDED` → `ARCHIVED`. Requires authorized faculty/administrative approval to activate student-proposed charters.
- **Elected Leadership & Mentorship**: Structured roles (`MEMBER`, `PRESIDENT`, `VICE_PRESIDENT`, `SECRETARY`, `TREASURER`, `EVENT_COORDINATOR`) under faculty advisor oversight.
- **Membership Workflow**: Structured student application → leadership approval/rejection → active affiliation or voluntary departure.
- **Club-Organized Events**: Transparent event association with host clubs via canonical foreign key references.

### 3. Institutional Announcements & Circulars
- **Official Broadcasts**: Priority stratification (`LOW`, `NORMAL`, `HIGH`, `URGENT`) with sticky pin support.
- **Audience Targeting Architecture**: Composable targeting criteria across `ALL_USERS`, `ALL_STUDENTS`, `ALL_FACULTY`, `ALL_STAFF`, `CAMPUS`, `DEPARTMENT`, `PROGRAM`, `ACADEMIC_YEAR`, `SEMESTER`, `SECTION`, `CLUB`, and `INDIVIDUAL_USERS`.
- **Pre-Publish Audience Preview**: Real-time server-side recipient calculation estimating total reach broken down by student, faculty, and administrative staff roles.

### 4. Unified Notification Engine
- **Single Source of Truth**: Reusable institutional messaging service consumed across Academics, Attendance, Examination, Finance, Placement, Events, and Clubs.
- **Delivery Decoupling**: Separation between `Notification` intent and `NotificationDelivery` channels (`IN_APP`, `EMAIL`, `PUSH`, `SMS`).
- **Deduplication Strategy**: Deterministic hash keys preventing repeat alerts for identical business events.
- **User Privacy & Preferences**: Granular opt-in/opt-out matrix across channels and categories, strictly protecting mandatory security and urgent institutional alerts.
- **Scalable Bulk Batch Fanout**: Background batch chunking (1,000 recipients/batch) preventing synchronous API latency during campus-wide circular broadcasts.

---

## Directory Navigation

- [Events Architecture](events.md)
- [Clubs & Governance](clubs.md)
- [Announcements & Bulletin](announcements.md)
- [Notification Engine](notifications.md)
- [Audience Targeting Strategy](audience-targeting.md)

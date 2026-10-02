# CampusOS — Campus Events, Clubs, Communication & Notifications Frontend Architecture

## 1. Executive Overview

The **Campus Events, Clubs, Communication & Notifications** module is the central institutional engagement, student life, and operational communication layer of **CampusOS**.

Following the core CampusOS operational sequence:
```text
People → Academics → Attendance → Examinations → Finance → Placement → Campus
```

The Campus module serves as the primary gateway where academic operations meet student co-curricular activities, institutional broadcasts, club governance, and multi-channel notification dispatches.

---

## 2. Core Campus Lifecycle

```text
Event / Club / Announcement
        ↓
Audience Targeting & Reach Estimation
        ↓
Registration / Membership Application
        ↓
Coordinator Approval / Waitlist Management
        ↓
Participation & Event Attendance
        ↓
Multi-Channel Communication & Notifications
        ↓
Unread Inbox & Deep-Link Resolution
        ↓
Audited Activity History & Attendance Metrics
```

---

## 3. Absolute Frontend-Only Guarantee

- **Zero Backend Business Logic**: No backend database models, migrations, schemas, repositories, or router endpoints in `apps/api` were modified or created.
- **Service Isolation**: All UI pages consume typed service interfaces via `campusService`.
- **Pure Calculators**: Centralized calculation functions in `campus-calculator.ts` eliminate formula duplication.
- **Relational Mock Adapter**: Fully synchronized in-memory database linking events, venues, clubs, memberships, registrations, attendance rosters, announcements, notification inboxes, and preference channels.

---

## 4. Route Architecture

| Route | View Description | Primary Persona | Key Capabilities |
| :--- | :--- | :--- | :--- |
| `/app/campus` | Operations & Engagement Dashboard | All Roles | KPI metric banners, upcoming timeline, today's schedule, club roster, engagement rates |
| `/app/campus/events` | Enterprise Event DataGrid | All Roles | 8-status filtering, category pills, registration state, capacity progress bars, cancel modal |
| `/app/campus/events/create` | 7-Step Guided Creation Wizard | Coordinators, Admin | Multi-step wizard: Basic info, Schedule, Venue conflict simulation, Audience matrix, Registration, Attendance, Review |
| `/app/campus/events/[id]` | Event Command Center | All Roles | 7 tabs: Overview, Schedule, Audience, Registrations, Attendance, Announcements, Timeline |
| `/app/campus/registrations` | Registration Management & Pass Console | Students, Coordinators | Enterprise DataGrid of registrations, ticket code badges, student "My Registrations" view, cancellation modal |
| `/app/campus/attendance` | Event Attendance Marking Console | Coordinators, Faculty | Event selector, participant search, 1-click status toggles (PRESENT, ABSENT, EXCUSED), bulk mark, rate KPI |
| `/app/campus/clubs` | Student Organizations Directory | All Roles | Club cards, category badges, faculty coordinator & student lead profiles, membership request flow |
| `/app/campus/clubs/create` | Club Charter Creation Wizard | Faculty, Admin | Formal charter registration: name, mission, faculty advisor, student president, membership rules |
| `/app/campus/clubs/[id]` | Club Operational Center | All Roles | 6 tabs: Overview, Members (approve/reject/promote), Events, Announcements, Leadership, History |
| `/app/campus/announcements` | Institutional Notice Board | All Roles | Priority indicators (URGENT, HIGH, NORMAL, LOW), audience tags, publisher roles, draft/publish modal |
| `/app/campus/announcements/[id]` | Notice Detail & Audit Trail | All Roles | Full announcement body, target audience breakdown, publishing history, priority alerts, archive action |
| `/app/campus/notifications` | Unified Notification Inbox | All Roles | Category filters, unread badge counter, 1-click mark read, mark all read, archive, entity deep links |
| `/app/campus/notifications/[id]` | Notification Detail View | All Roles | Notification message, source category, timestamp, read state, direct CTA to source entity |
| `/app/campus/preferences` | Channel Preferences & Delivery Telemetry | All Roles | In-app/Email/SMS/Push toggle matrix, simulated delivery metrics, communication audit log |

---

## 5. Component Catalog

- `AudienceBuilder`: Reusable targeting matrix supporting combinations of department, program, semester, section, club, or institutional scope with live estimated recipient counts.
- `CampusCalendar`: Unified scheduling calendar supporting Month, Week, Day, and Agenda views with category color coding and direct entity deep links.
- `NotificationDrawer`: Slide-over topbar drawer displaying real-time unread counts, categorical icons, and one-click navigation to referenced invoices, interviews, events, and notices.
- `DataGrid`: Enterprise-grade tabular interface featuring search, column visibility, sorting, and pagination across events, registrations, and notices.

---

## 6. Centralized Pure Calculators

Exported from `apps/web/src/services/campus-calculator.ts`:

1. `calculateEventAttendanceRate(attended, registered)`: Formats exact integer percentage with zero-guarding.
2. `calculateEventCapacityUsage(registered, capacity)`: Returns percentage of venue capacity occupied.
3. `calculateRegistrationRate(registered, targetSize)`: Quantifies audience uptake.
4. `calculateClubMembershipCount(members)`: Computes active, pending, suspended, and total counts.
5. `calculateUnreadNotificationCount(notifications)`: Tallies unread inbox alerts.
6. `calculateAudienceSize(target)`: Computes estimated audience reach for targeting combinations.
7. `calculateDeliveryRate(delivered, total)`: Provides mock delivery transmission health percentages.

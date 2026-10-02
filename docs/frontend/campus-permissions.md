# CampusOS — Campus Role Permissions & Access Control Matrix

## 1. Overview

Access to Campus features is strictly regulated by role-based permissions (`campus.*`) defined in the central authorization store.

---

## 2. Permission Definitions

| Permission Key | Description |
| :--- | :--- |
| `campus.view` | View campus dashboard, public events, active clubs, calendar, and notices |
| `campus.manage_events` | Create and edit draft campus events |
| `campus.publish_events` | Approve and publish events to public campus calendar and open registrations |
| `campus.cancel_events` | Abort scheduled events with mandatory broadcast reason |
| `campus.manage_event_registrations` | View all attendee registrations, export rosters, process cancellations |
| `campus.register_events` | Self-register for open campus events and view owned event passes |
| `campus.manage_event_attendance` | Mark present/absent/excused and execute bulk attendance reconciliation |
| `campus.manage_clubs` | Charter new student organizations and edit club parameters |
| `campus.manage_memberships` | Review, approve, or reject student club membership applications and assign executive roles |
| `campus.manage_own_memberships` | Apply to join clubs and voluntarily resign membership |
| `campus.create_announcements` | Draft institutional circulars and targeted broadcasts |
| `campus.publish_announcements` | Publish institutional announcements and dispatch multi-channel alerts |
| `campus.archive_announcements` | Expire or archive campus announcements |
| `campus.view_notifications` | Access personal notification inbox |
| `campus.manage_notifications` | Mark read, unread, or archive notifications |
| `campus.manage_notification_preferences` | Configure In-App, Email, SMS, and Push channel subscriptions |
| `campus.view_reports` | Access attendance analytics, engagement metrics, and transmission telemetry |

---

## 3. Role Access Matrix

| Role | `view` | `create_events` | `publish_events` | `mark_attendance` | `approve_club` | `publish_notice` | `register_event` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Super Admin** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| **Admin** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| **HOD** | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✖ |
| **Faculty / Advisor** | ✔ | ✔ | ✖ | ✔ | ✔ | ✖ | ✖ |
| **Event / Club Coordinator**| ✔ | ✔ | ✖ | ✔ | ✔ | ✖ | ✖ |
| **Student** | ✔ | ✖ | ✖ | ✖ | ✖ | ✖ | ✔ |

---

## 4. Persona Experience Focus

### Student Persona
- **Primary Views**: `/app/campus`, `/app/campus/registrations`, `/app/campus/clubs`, `/app/campus/notifications`
- **Key Actions**: Discover workshops, 1-click event pass registration, apply to join technical clubs, view attendance records, manage notification delivery channels.
- **Strict Guards**: Prohibited from publishing events, approving club members, marking attendance, or drafting institutional circulars.

### Faculty / Advisor Persona
- **Primary Views**: `/app/campus/events`, `/app/campus/attendance`, `/app/campus/clubs/[id]`
- **Key Actions**: Mark session attendance, review club membership applications, supervise co-curricular activity rosters.

### HOD Persona
- **Primary Views**: `/app/campus`, `/app/campus/events`, `/app/campus/announcements`
- **Key Actions**: Departmental event approval and publication, targeted departmental circular broadcasting, review student engagement metrics.

### Coordinator Persona
- **Primary Views**: `/app/campus/events/[id]`, `/app/campus/attendance`, `/app/campus/clubs/[id]`
- **Key Actions**: Event creation wizard, ticket check-in desk, bulk attendance marking, club member executive role assignments.

### Administrator Persona
- **Primary Views**: Complete `/app/campus/*` suite
- **Key Actions**: Institutional notice broadcasting, multi-channel simulated delivery telemetry, venue schedule conflict resolution, campus calendar management.

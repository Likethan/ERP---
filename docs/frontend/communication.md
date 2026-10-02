# CampusOS — Institutional Communication & Broadcast Center

## 1. Overview

The **Communication Center** governs institutional broadcast notices, circulars, urgent administrative advisories, and targeted messages across the university campus.

---

## 2. Institutional Announcements

### Route: `/app/campus/announcements`

Announcements are categorized by topic:
- `ACADEMIC`: Semester schedules, syllabus updates, timetable revisions
- `EXAMINATION`: Hall ticket releases, seating arrangements, result declarations
- `HOSTEL`: Mess timings, maintenance circulars, curfew updates
- `GENERAL`: Institutional holidays, guest lectures, campus visitors
- `URGENT`: Emergency weather advisories, immediate campus closures

### Priority Classes
- `URGENT`: Highlighted with high-contrast alert styling; overrides notification channel suppressions.
- `HIGH`: Prioritized on top of notification lists and campus dashboards.
- `NORMAL`: Standard broadcast feed notice.
- `LOW`: Informational bulletin.

### Status Machine
- `DRAFT`: Notice composed but not yet visible to stakeholders.
- `SCHEDULED`: Notice configured with future publish timestamp.
- `PUBLISHED`: Actively broadcast across web app notice boards and notifications.
- `EXPIRED`: Past expiration date; moved to archival read-only feed.
- `ARCHIVED`: Manually archived by communications administrator.

---

## 3. Targeted Audience Builder

The `AudienceBuilder` component (`src/components/campus/audience-builder.tsx`) provides granular targeting criteria:

```text
Scope Combination:
  Target Type: SPECIFIC_DEPARTMENT
  Department: Department of Computer Science & Engineering
  Semester: 5
  Role: STUDENT
        ↓
Live Audience Estimation: 142 recipients
```

### Supported Audience Types:
1. `ALL_USERS`: All registered students, faculty, and administrative staff (~4,750 users).
2. `ALL_STUDENTS`: All enrolled undergraduate and postgraduate students (~4,200 users).
3. `SPECIFIC_DEPARTMENT`: Filtered to singular department faculty and students (~525 users).
4. `SPECIFIC_PROGRAM`: Filtered to single degree program (e.g. B.Tech Artificial Intelligence).
5. `SPECIFIC_SEMESTER`: Filtered to specific academic semester cohort across programs.
6. `SPECIFIC_SECTION`: Granular class section targeting.
7. `FACULTY`: Academic teaching faculty only (~320 users).
8. `STAFF`: Administrative, laboratory, and non-teaching personnel (~180 users).
9. `CLUB_MEMBERS`: Targeted to enrolled members of a recognized student organization.
10. `CUSTOM`: Multi-criteria composite filters.

---

## 4. Multi-Channel Simulated Telemetry

For administrative auditing, CampusOS displays transmission success metrics across 4 delivery channels:

| Channel | Protocol Simulation | Audit State Displayed |
| :--- | :--- | :--- |
| **In-App** | CampusOS Web Notification System | 100% delivered to notification inboxes |
| **Email** | Institutional SMTP Relay Mock | e.g. 718 Delivered, 24 Bounced / Failed |
| **SMS** | Campus Telecom SMS Gateway Mock | Sent to registered student phone numbers |
| **Push** | Mobile Campus App FCM Simulation | Sent to active enrolled devices |

All delivery counts are clearly labeled with simulated telemetry tags to distinguish frontend mock telemetry from future live gateways.

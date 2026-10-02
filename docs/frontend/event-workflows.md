# CampusOS — Campus Event Lifecycle & Workflows

## 1. Overview

Campus events represent the structured extra- and co-curricular lifecycle of CampusOS, spanning technical hackathons, national symposiums, cultural fests, academic workshops, guest lectures, and placement orientation drives.

---

## 2. Event Status State Machine

Events transition through an explicit 8-status lifecycle:

```text
       [ CREATE EVENT ]
              ↓
           DRAFT ──────────────┐
              ↓                │
      PENDING_APPROVAL         │
              ↓                │
          PUBLISHED            │
              ↓                │
      REGISTRATION_OPEN ───────┤
              ↓                │ (Cancel Event)
      REGISTRATION_CLOSED      │
              ↓                │
           ONGOING             │
              ↓                │
          COMPLETED            │
              ▲                ↓
              └─────────── CANCELLED
```

### Status Descriptions
- `DRAFT`: Initial saved state created by event coordinator or faculty organizer. Never publicly displayed or open for registration.
- `PENDING_APPROVAL`: Submitted by club coordinators or student bodies awaiting HOD or Administrator sign-off.
- `PUBLISHED`: Approved and publicly visible on campus calendars and discovery feeds.
- `REGISTRATION_OPEN`: Actively accepting student registration passes up to configured venue capacity.
- `REGISTRATION_CLOSED`: Deadline reached or capacity full without waitlist.
- `ONGOING`: Event is currently in progress.
- `COMPLETED`: Event concluded; final attendance rates locked and archived into student co-curricular transcripts.
- `CANCELLED`: Explicitly aborted with mandatory cancellation reason broadcast to all registered participants.

---

## 3. Guided 7-Step Event Creation Wizard

Located at `/app/campus/events/create`:

1. **Step 1 — Basic Information**:
   - Event Title & Slug
   - Category (`Academic`, `Technical`, `Cultural`, `Sports`, `Workshop`, `Seminar`, `Hackathon`, `Symposium`, `Club Activity`, `Placement`, `Orientation`, `Institutional`)
   - Description & Objectives
   - Organizer Entity (Department vs Student Club)
2. **Step 2 — Schedule**:
   - Start Date, End Date, Start Time, End Time
   - Schedule validation (End must be after Start)
3. **Step 3 — Venue & Capacity**:
   - Campus Block selection
   - Venue / Auditorium / Lab selection
   - Seating Capacity limit
   - Real-time venue overlap and capacity clash warning indicators
4. **Step 4 — Target Audience**:
   - Powered by `AudienceBuilder` component
   - Scope: `All Students`, `Specific Department`, `Specific Program`, `Specific Semester`, `Faculty`, `Staff`, `Club Members`, `Custom`
   - Real-time audience size estimate calculation
5. **Step 5 — Registration Configuration**:
   - Registration Required toggle
   - Registration Window (Open Date, Close Date)
   - Maximum Participant Cap
   - Waitlist enablement
6. **Step 6 — Attendance Configuration**:
   - Mandatory attendance tracking toggle
   - Minimum participation criteria
7. **Step 7 — Review & Save**:
   - Comprehensive summary verification
   - **Crucial Rule**: Events are strictly saved as `DRAFT` upon submission. Never auto-published.

---

## 4. Student Registration Workflow

```text
1. Discover Event on Discovery Feed or Campus Calendar
2. View Details & Eligibility Requirements
3. Click "Register Now"
4. System validates:
   - Event is in REGISTRATION_OPEN status
   - Registration deadline has not passed
   - Student has not already registered (duplicate guard)
   - Capacity has not been exceeded
5. Ticket Code generated (e.g. TKT-CS23B001-9214)
6. Registration status set to CONFIRMED
7. Event registeredCount incremented
8. In-app confirmation notification dispatched with deep link to pass
```

---

## 5. Event Attendance Roster & Marking Console

Located at `/app/campus/attendance`:

### Coordinator Capabilities:
- Event Selector dropdown filtering active and ongoing events
- Real-time attendance rate calculation using `calculateEventAttendanceRate()`:
  $$\text{Attendance Rate} = \frac{\text{Present Participants}}{\text{Total Registered}} \times 100$$
- Search by student name, roll number, or ticket code
- 1-Click Status Marking:
  - `PRESENT` (Green badge)
  - `ABSENT` (Rose badge)
  - `EXCUSED` (Amber badge)
- Bulk Actions:
  - Mark All Unmarked as Present
  - Mark All Unmarked as Absent
- Automatic relational update back to registration records and event attendance counts.

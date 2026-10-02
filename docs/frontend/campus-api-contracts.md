# CampusOS — Campus Management REST API Contracts

This specification defines the future REST API endpoints for the Campus module, matching the service interface implemented in `apps/web/src/services/campus.service.ts`.

## Base Path
```text
/api/v1/campus
```

---

## 1. Campus Dashboard

### `GET /api/v1/campus/summary`
Retrieves institutional campus engagement statistics and today's operational schedule.

**Response `200 OK`**:
```json
{
  "success": true,
  "data": {
    "activeEventsCount": 18,
    "upcomingEventsCount": 12,
    "openRegistrationsCount": 8,
    "activeClubsCount": 14,
    "registeredParticipantsCount": 2420,
    "attendanceTodayCount": 380,
    "unreadAnnouncementsCount": 3,
    "unreadNotificationsCount": 4,
    "averageAttendanceRate": 84,
    "activeClubMembershipsCount": 1150
  }
}
```

---

## 2. Event Management

### `GET /api/v1/campus/events`
Query events with filtering, search, and pagination.

**Query Parameters**:
- `status`: Filter by `EventStatus` (`DRAFT`, `PUBLISHED`, `REGISTRATION_OPEN`, etc.)
- `category`: Filter by `EventCategory` (`Academic`, `Technical`, `Cultural`, `Sports`, etc.)
- `search`: Keyword string matching title, organizer, or venue
- `startDate` / `endDate`: ISO-8601 date range

**Response `200 OK`**:
```json
{
  "success": true,
  "data": [
    {
      "id": "evt-01",
      "title": "HackCampus 2026: 36-Hour National Hackathon",
      "slug": "hackcampus-2026",
      "category": "Hackathon",
      "description": "Annual flagship inter-collegiate hackathon.",
      "organizer": "Department of Computer Science & Engineering",
      "organizerType": "DEPARTMENT",
      "startDate": "2026-10-15",
      "endDate": "2026-10-17",
      "startTime": "09:00 AM",
      "endTime": "09:00 PM",
      "venue": "Dr. APJ Abdul Kalam Auditorium",
      "capacity": 200,
      "registeredCount": 180,
      "attendedCount": 0,
      "requiresRegistration": true,
      "allowWaitlist": true,
      "requiresAttendance": true,
      "status": "REGISTRATION_OPEN"
    }
  ]
}
```

### `POST /api/v1/campus/events`
Create a new campus event. Automatically creates the event in `DRAFT` status.

**Request Body**:
```json
{
  "title": "Quantum Computing & Quantum Algorithms Workshop",
  "category": "Workshop",
  "description": "Foundations of Qubits and Qiskit hands-on programming.",
  "organizer": "Department of Physics & Computing",
  "organizerType": "DEPARTMENT",
  "startDate": "2026-11-05",
  "endDate": "2026-11-06",
  "startTime": "10:00 AM",
  "endTime": "04:00 PM",
  "campus": "Main Campus",
  "building": "Science & Research Block",
  "venue": "Quantum Lab 301",
  "capacity": 60,
  "requiresRegistration": true,
  "registrationOpenDate": "2026-10-20",
  "registrationCloseDate": "2026-11-03",
  "allowWaitlist": true,
  "requiresAttendance": true,
  "targetAudience": {
    "type": "SPECIFIC_DEPARTMENT",
    "departmentName": "CSE & Physics",
    "estimatedCount": 350
  }
}
```

### `GET /api/v1/campus/events/{id}`
Retrieve complete event details including timeline, venue specs, and registration metadata.

### `PATCH /api/v1/campus/events/{id}`
Update event metadata. Prohibited if event is `COMPLETED` or `CANCELLED`.

### `POST /api/v1/campus/events/{id}/publish`
Promote event from `DRAFT` or `PENDING_APPROVAL` to `PUBLISHED` / `REGISTRATION_OPEN`.

### `POST /api/v1/campus/events/{id}/cancel`
Cancel an event with mandatory cancellation reason and automatic notification broadcast.

---

## 3. Registrations & Attendance

### `GET /api/v1/campus/events/{id}/registrations`
Fetch registered participants for an event with attendance and ticket statuses.

### `POST /api/v1/campus/events/{id}/registrations`
Register current authenticated student for an event. Enforces capacity and duplicate prevention.

**Request Body**:
```json
{
  "studentId": "stu-canonical-01",
  "studentName": "Aditya Verma",
  "rollNumber": "CS23B001",
  "department": "CSE",
  "program": "B.Tech CSE",
  "semester": 5
}
```

**Response `201 Created`**:
```json
{
  "success": true,
  "data": {
    "id": "reg-evt-01-stu-01",
    "eventId": "evt-01",
    "eventTitle": "HackCampus 2026: 36-Hour National Hackathon",
    "ticketCode": "TKT-CS23B001-9214",
    "status": "CONFIRMED",
    "registrationDate": "2026-10-02"
  }
}
```

### `DELETE /api/v1/campus/events/{id}/registrations/{registrationId}`
Cancel a registration with audit reason.

### `GET /api/v1/campus/events/{id}/attendance`
Fetch attendance roster with aggregate summary metrics.

### `POST /api/v1/campus/events/{id}/attendance`
Record attendance for one or more participants.

**Request Body**:
```json
{
  "records": [
    {
      "registrationId": "reg-01",
      "status": "PRESENT",
      "remarks": "On-time arrival"
    },
    {
      "registrationId": "reg-02",
      "status": "ABSENT",
      "remarks": "Unexcused"
    }
  ]
}
```

---

## 4. Club Management

### `GET /api/v1/campus/clubs`
Fetch active student clubs and societies.

### `POST /api/v1/campus/clubs`
Charter a new student organization.

### `GET /api/v1/campus/clubs/{id}`
Retrieve club overview, executive leadership, active members, and associated events.

### `POST /api/v1/campus/clubs/{id}/memberships`
Student requests to join club (`PENDING` state).

### `PATCH /api/v1/campus/clubs/{id}/memberships/{membershipId}`
Approve (`ACTIVE`), reject, or modify role (`VICE_PRESIDENT`, `SECRETARY`, `MEMBER`).

---

## 5. Institutional Announcements

### `GET /api/v1/campus/announcements`
Fetch announcements filtered by priority, status, and target audience.

### `POST /api/v1/campus/announcements`
Draft a new announcement with targeted audience configuration.

### `POST /api/v1/campus/announcements/{id}/publish`
Publish announcement and trigger simulated delivery dispatches.

---

## 6. Notifications & Preferences

### `GET /api/v1/campus/notifications`
Retrieve current user's notification inbox.

### `PATCH /api/v1/campus/notifications/{id}/read`
Mark single notification as read.

### `POST /api/v1/campus/notifications/read-all`
Mark all unread notifications as read.

### `PATCH /api/v1/campus/notifications/{id}/archive`
Move notification to archive state.

### `GET /api/v1/campus/preferences`
Get multi-channel delivery preferences (In-App, Email, SMS, Push).

### `PATCH /api/v1/campus/preferences`
Update notification channel subscription preferences.

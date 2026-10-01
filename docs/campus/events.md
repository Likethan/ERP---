# CampusOS — Events Architecture & Lifecycle Specification

## 1. Domain Entities & Relational Design

The event management subsystem is modeled using distinct canonical entities in PostgreSQL:

| Entity | Table Name | Purpose | Key Attributes |
|---|---|---|---|
| `EventCategory` | `campus_event_categories` | Configurable event taxonomy | `code`, `name`, `is_active` |
| `EventVenue` | `campus_event_venues` | Reusable physical campus spaces | `campus_id`, `name`, `building`, `floor`, `capacity`, `status` |
| `CampusEvent` | `campus_events` | Core event scheduling record | `campus_id`, `venue_id`, `category_id`, `title`, `slug`, `organizer_type`, `organizer_id`, `start_at`, `end_at`, `capacity`, `status`, `visibility` |
| `EventRegistration` | `campus_event_registrations` | Student registration record | `event_id`, `student_id`, `registration_code`, `status`, `attended` |
| `EventAttendance` | `campus_event_attendances` | Physical check-in participation | `event_id`, `student_id`, `checked_in_at`, `attendance_status`, `verification_method` |

---

## 2. Event Lifecycle State Machine

```
      [DRAFT]
         │ (events:publish)
         ▼
    [PUBLISHED]
         │ (Open registration window reached or admin override)
         ▼
[REGISTRATION_OPEN] ──(Quota reached / window closed)──► [REGISTRATION_CLOSED]
         │                                                      │
         └───────────────────────┬──────────────────────────────┘
                                 │ (Start time reached)
                                 ▼
                             [ONGOING]
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
                [COMPLETED]             [CANCELLED]
                     │
                     ▼
                 [ARCHIVED]
```

Lifecycle mutations are guarded by strict transitions in `CampusService.transition_event_status()`. Unauthorized or illogical transitions (e.g. `COMPLETED` → `DRAFT`) are rejected with `422 Unprocessable Content`.

---

## 3. Venue Conflict & Overlap Detection

When an event is scheduled or rescheduled at a physical `EventVenue`, the engine evaluates existing reservations using an interval overlap predicate:

$$\text{Overlap} = (\text{Existing.start} < \text{New.end}) \land (\text{Existing.end} > \text{New.start})$$

```python
conditions = [
    CampusEvent.tenant_id == tenant_id,
    CampusEvent.venue_id == venue_id,
    CampusEvent.status.notin_(["CANCELLED", "ARCHIVED"]),
    CampusEvent.start_at < end_at,
    CampusEvent.end_at > start_at,
]
```

If any overlapping record exists, the reservation is rejected with a descriptive message indicating the conflicting event title and reserved time window.

---

## 4. Student Registration Rules & Eligibility

1. **Registration Window**: Evaluated server-side against `registration_open_at` and `registration_close_at`.
2. **Quota Bounds**: Checked atomically against `event.capacity`. If capacity is reached, new registrants are placed into `WAITLISTED` status.
3. **Duplicate Prevention**: Enforced via DB unique constraint `uq_event_registrations_event_student` on `(tenant_id, event_id, student_id)`.
4. **Target Criteria Filter**: If `event.target_filter_json` is specified, student department and program IDs are verified before accepting registration.
5. **Registration Code**: A cryptographically random unique alphanumeric code (e.g., `REG-A1B2C3`) is generated for every registration, enabling high-speed barcode and manual check-ins.

---

## 5. Participation Check-In & Attendance

Event attendance is completely distinct from statutory academic attendance. Marking an event check-in records extracurricular engagement:

- **Manual Verification**: Authorized staff enter the student's registration code or roll number.
- **Dynamic QR Check-In**:
  - The staff console generates a temporary token:
    $$\text{Token} = \text{tenant\_id} + \text{event\_id} + \text{expiry} + \text{HMAC-SHA256}(\text{data}, \text{SECRET})$$
  - Tokens expire after 5 minutes (configurable up to 30 minutes).
  - The student scans the projected token in the hall; authenticated endpoint `POST /api/v1/events/{id}/qr-check-in` validates the signature, prevents replay attacks, marks attendance as `PRESENT`, and sets `verification_method = "QR"`.
- **Undo Capability**: Supervised reversal of mistaken check-ins with an audit trail entry.

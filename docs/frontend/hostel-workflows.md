# CampusOS — Hostel Residential Lifecycle & Operations Workflows

## 1. Overview

The Hostel Operations workflow governs residential life across male, female, and postgraduate hostel blocks. Key operational pillars include:

```text
Room & Bed Inventory Matrix
            ↓
Student Bed Allocation / Vacation
            ↓
Outing & Leave Gate Pass Approval Cycle
            ↓
Student Grievance Logging & Technician Dispatch
            ↓
Resolution Verification & Residential Safety Audit
```

---

## 2. Room & Bed Inventory Matrix

Each hostel block maintains a dynamic inventory categorized by floors:
- **Room Types**: Single, Double, Triple, Quadruple, Dormitory.
- **Bed Statuses**:
  - `AVAILABLE`: Bed is vacant and ready for student assignment.
  - `OCCUPIED`: Bed is assigned to an enrolled student.
  - `RESERVED`: Temporarily held for incoming exchange or special admission.
  - `UNDER_MAINTENANCE`: Bed or surrounding fixtures require physical repairs before occupancy.

### Bed Allocation Rules:
1. Only `AVAILABLE` beds can be selected for allocation.
2. Allocation automatically links student `id`, `name`, and `rollNumber`.
3. Bed status shifts to `OCCUPIED` and triggers an update to the hostel's aggregate occupancy telemetry.
4. Vacating a bed returns it to `AVAILABLE` status.

---

## 3. Hostel Leaves & Outing Passes

Students residing in campus hostels must request authorization before departing campus:

```text
Student Submits Request (Dates, Reason, Emergency Contact)
                    ↓
Warden Review Desk (Verification with Guardian if needed)
                    ↓
Warden Decision
    ├── APPROVED → Generates Timestamped Security Gate Pass Code
    └── REJECTED → Logs Justification & Informs Student
                    ↓
Student Returns & Security Marks Gate Pass Completed
```

### Security Safeguards:
- Emergency parent phone numbers are required.
- Gate pass generation is cryptographic and time-bound.
- Overdue returns are highlighted with alerts in the Warden console.

---

## 4. Residential Complaints & Grievance Tracking

Hostel complaints support 6 core facility categories:
- `ELECTRICAL`: Power loss, ceiling fan failure, faulty sockets.
- `PLUMBING`: Leaking taps, geyser malfunction, drainage blockage.
- `CLEANING`: Deep cleaning requirements, waste disposal.
- `FURNITURE`: Bed frame repair, study table / chair replacement.
- `ROOM`: Door locks, window panes, seepage.
- `WIFI`: Access point downtime, bandwidth degradation.

### Complaint Resolution Lifecycle:
1. **OPEN**: Ticket logged by student resident.
2. **ASSIGNED**: Warden or Facility Officer assigns designated maintenance technician.
3. **IN_PROGRESS**: Technician initiates on-site repair.
4. **RESOLVED**: Technician documents resolution notes and marks fix complete.
5. **CLOSED**: Student confirms resolution satisfaction or auto-closes after 48h.

# CampusOS — Attendance Management Workflows & Operational Guides

## 1. Classroom Attendance Recording Workflow

### 1.1 Step-by-Step Flow
```text
Faculty Selects Timetable Period / Course Offering
                  │
                  ▼
System Loads Canonical Enrolled Cohort Roster
                  │
                  ▼
Interactive Matrix Opened (/app/attendance/sessions/[id])
                  │
   ┌──────────────┴──────────────┐
   ▼                             ▼
Individual Student Quick-Toggle  Bulk Action ("Mark All Present" / "Mark All Absent")
   │                             │
   └──────────────┬──────────────┘
                  ▼
Dirty State Triggered: Unsaved Changes Protection Banner Displayed
                  │
                  ▼
Faculty Clicks "Save Attendance"
                  │
                  ▼
attendanceService.saveSessionAttendance(...)
                  │
                  ├── Session status updated from OPEN to COMPLETED
                  ├── Student records persisted into ledger
                  ├── Recalculates student & course aggregate statistics
                  └── Chronological audit timeline logs "Attendance Submitted"
```

### 1.2 Unsaved Changes Protection
- **Dirty State Detection**: Any modification to a student's status marks the form as `isDirty`.
- **Warning Banner**: A prominent high-visibility warning banner informs faculty: *"You have unsaved changes. Any modifications to attendance will be lost if you leave this page without saving."*
- **Action Safeguards**: "Discard" triggers a complete reset back to original loaded marks, while "Save Changes" commits all modifications to the reactive service.

### 1.3 Fast Keyboard & Mobile Roster Navigation
- **Keyboard Optimization**: Tab-index ordering and rapid single-character key shortcuts (`P` for Present, `A` for Absent, `L` for Late, `E` for Excused).
- **Responsive Layout**: On desktop, a high-density 4-button pill matrix is displayed. On mobile screens, items render as compact student cards with direct tap actions.

---

## 2. Supervised Attendance Correction Workflow

### 2.1 Audit & Governance Principle
To prevent grade tampering, fraudulent adjustments, or accidental alterations, attendance records **CANNOT be silently overwritten**. Any change following formal submission must proceed through supervised administrative review.

```text
Faculty discovers error (e.g. biometric scanner timeout or mistaken mark)
                      │
                      ▼
Faculty clicks "Request Correction" on student row
                      │
                      ▼
Correction Form submitted:
  - Original Status: ABSENT
  - Requested Status: PRESENT
  - Justification: "Student was verified present in lecture hall; scanner failure."
                      │
                      ▼
Status: PENDING ➔ Routed to Department HOD / Admin
                      │
                      ▼
HOD opens /app/attendance/corrections
                      │
                      ▼
Review Modal with Full Context & Audit Timeline
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
     HOD Approves          HOD Rejects
           │                     │
           ▼                     ▼
- Underlying Record patched    - Record remains unchanged
- Status set to APPROVED       - Status set to REJECTED
- Appends to Audit Trail       - Appends rejection notes
```

### 2.2 Chronological Audit Trail Format
Each correction preserves a strictly ordered, immutable audit log:
1. `[10:15 AM]` Session Scheduled by Faculty Dr. Ramesh Sundaram
2. `[11:05 AM]` Session Opened for Manual Roll Call
3. `[11:12 AM]` Attendance Submitted (38 Present, 2 Absent, 2 Late)
4. `[02:30 PM]` Correction Requested by Dr. Ramesh Sundaram for Student Aarav Patel (ABSENT ➔ PRESENT)
5. `[03:45 PM]` HOD Review Approved by Dr. Anita Roy (Notes: "Verified via lab logbook")
6. `[03:45 PM]` Attendance Record Updated & Synchronized

---

## 3. Student Leave & Condonation Workflow

### 3.1 Leave Request Flow
```text
Student / Faculty Advisor Submits Leave (/app/attendance/leaves)
  - Leave Type: MEDICAL | SPORTS_CULTURAL | OFFICIAL_DUTY | CASUAL
  - Start Date & End Date
  - Reason & Medical/OD Document Attachment
                      │
                      ▼
Request Logged as PENDING
                      │
                      ▼
HOD Reviews Document & Academic Standing
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
     HOD Approves          HOD Rejects
           │                     │
           ▼                     ▼
Affected sessions marked        Leave rejected; days
as EXCUSED for student          count as ABSENT
```

### 3.2 Impact on University Eligibility
- Sessions designated as `EXCUSED` are factored according to institutional policy.
- In standard mode, excused sessions are either deducted from the total session denominator or credited as present attendance for university condonation committees.

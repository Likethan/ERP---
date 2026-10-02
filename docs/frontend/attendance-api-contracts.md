# CampusOS — Attendance Management API Contracts & Backend Migration Guide

## 1. Architectural Strategy

The Attendance Management module follows the standard CampusOS layered architecture:

```text
Page Component (e.g. /app/attendance/sessions/[id])
       │
       ▼
Domain Hook / UI Component
       │
       ▼
attendanceService (apps/web/src/services/attendance.service.ts)
       │
       ▼
Current: In-Memory Reactive Mock Adapter
Future:  FastAPI Endpoints (/api/v1/attendance/...)
```

When backend FastAPI endpoints and SQLAlchemy models are implemented in a future phase, only the adapter implementation inside `attendance.service.ts` will need to switch from local mock manipulation to `fetchClient` calls. All domain contracts, TypeScript interfaces, and UI pages will remain completely unchanged.

---

## 2. API Contract Endpoints

### 2.1 Operations & Dashboard

#### `GET /api/v1/attendance/summary`
- **Method**: `attendanceService.getDashboardSummary()`
- **Query Params**: None
- **Response**: `ApiResponse<AttendanceSummary>`
```json
{
  "success": true,
  "data": {
    "overallAttendancePercentage": 84.6,
    "studentsBelowThreshold": 18,
    "todaySessionsCount": 48,
    "pendingSessionsCount": 6,
    "pendingCorrectionsCount": 4,
    "pendingLeavesCount": 7,
    "departmentBreakdown": [
      { "departmentId": "dept-cse", "departmentName": "Computer Science & Engineering", "attendancePercentage": 86.2, "studentCount": 420 },
      { "departmentId": "dept-ece", "departmentName": "Electronics & Communication", "attendancePercentage": 83.8, "studentCount": 380 }
    ],
    "semesterBreakdown": [
      { "semester": 1, "attendancePercentage": 88.5, "studentCount": 350 },
      { "semester": 5, "attendancePercentage": 84.1, "studentCount": 390 }
    ]
  }
}
```

---

### 2.2 Attendance Policies

#### `GET /api/v1/attendance/policies`
- **Method**: `attendanceService.getPolicies()`
- **Response**: `ApiResponse<AttendancePolicy[]>`

#### `POST /api/v1/attendance/policies`
- **Method**: `attendanceService.createPolicy(data: Omit<AttendancePolicy, "id" | "createdAt">)`
- **Request Body**:
```json
{
  "name": "B.Tech Engineering Policy 2026",
  "description": "Standard university threshold with condonation band",
  "minimumPercentage": 75,
  "warningThreshold": 80,
  "criticalThreshold": 65,
  "lateThresholdMinutes": 10,
  "lateWeightPercentage": 50,
  "includeLeavesInCalculations": true,
  "requireApprovalForCorrections": true,
  "applicablePrograms": ["B.Tech Computer Science & Engineering"],
  "academicYear": "2026-2027",
  "isDefault": true
}
```
- **Response**: `ApiResponse<AttendancePolicy>`

---

### 2.3 Attendance Sessions

#### `GET /api/v1/attendance/sessions`
- **Method**: `attendanceService.getSessions(filters?: SessionFilters)`
- **Query Params**: `date`, `department`, `program`, `semester`, `section`, `facultyId`, `subjectId`, `status`
- **Response**: `ApiResponse<AttendanceSession[]>`

#### `GET /api/v1/attendance/sessions/{sessionId}`
- **Method**: `attendanceService.getSessionById(sessionId: string)`
- **Response**: `ApiResponse<AttendanceSession>`

#### `POST /api/v1/attendance/sessions`
- **Method**: `attendanceService.createSession(payload)`
- **Request Body**:
```json
{
  "courseOfferingId": "co-cs301-a",
  "subjectCode": "CS301",
  "subjectName": "Data Structures & Algorithms",
  "section": "A",
  "department": "Computer Science & Engineering",
  "facultyId": "fac-001",
  "facultyName": "Dr. Ramesh Sundaram",
  "date": "2026-10-02",
  "startTime": "09:00",
  "endTime": "09:50",
  "room": "CS-LH-201",
  "sessionType": "LECTURE",
  "topicsCovered": "Binary Search Trees and AVL Rotations"
}
```
- **Response**: `ApiResponse<AttendanceSession>`

#### `GET /api/v1/attendance/sessions/{sessionId}/roster`
- **Method**: `attendanceService.getSessionRoster(sessionId: string)`
- **Response**: `ApiResponse<AttendanceRecord[]>`

#### `POST /api/v1/attendance/sessions/{sessionId}/roster`
- **Method**: `attendanceService.saveSessionAttendance(sessionId, records, topicsCovered?)`
- **Request Body**:
```json
{
  "records": [
    { "studentId": "std-001", "status": "PRESENT", "remarks": "" },
    { "studentId": "std-002", "status": "LATE", "remarks": "Delayed by 8 mins" },
    { "studentId": "std-003", "status": "ABSENT", "remarks": "Unexcused" }
  ],
  "topicsCovered": "AVL Tree rebalancing and rotation demonstrations"
}
```
- **Response**: `ApiResponse<{ session: AttendanceSession; records: AttendanceRecord[] }>`

---

### 2.4 Attendance Records Ledger

#### `GET /api/v1/attendance/records`
- **Method**: `attendanceService.getRecords(filters?: RecordFilters)`
- **Query Params**: `studentId`, `courseOfferingId`, `status`, `dateFrom`, `dateTo`, `search`
- **Response**: `ApiResponse<AttendanceRecord[]>`

---

### 2.5 Student & Course Summaries

#### `GET /api/v1/attendance/students`
- **Method**: `attendanceService.getStudentSummaries(filters?)`
- **Response**: `ApiResponse<AttendanceStudentSummary[]>`

#### `GET /api/v1/attendance/students/{studentId}`
- **Method**: `attendanceService.getStudentAttendance(studentId: string)`
- **Response**: `ApiResponse<{ summary: AttendanceStudentSummary; courseBreakdown: AttendanceCourseBreakdown[]; weeklyTrend: WeeklyAttendanceTrend[] }>`

#### `GET /api/v1/attendance/courses`
- **Method**: `attendanceService.getCourseSummaries(filters?)`
- **Response**: `ApiResponse<AttendanceCourseSummary[]>`

#### `GET /api/v1/attendance/courses/{courseOfferingId}`
- **Method**: `attendanceService.getCourseAttendance(courseOfferingId: string)`
- **Response**: `ApiResponse<{ summary: AttendanceCourseSummary; studentRoster: AttendanceStudentSummary[] }>`

---

### 2.6 Leave Requests

#### `GET /api/v1/attendance/leaves`
- **Method**: `attendanceService.getLeaves(filters?: { status?: string; studentId?: string })`
- **Response**: `ApiResponse<AttendanceLeave[]>`

#### `POST /api/v1/attendance/leaves`
- **Method**: `attendanceService.createLeave(data)`
- **Request Body**:
```json
{
  "studentId": "std-001",
  "studentName": "Aarav Patel",
  "rollNumber": "24CSE0101",
  "department": "Computer Science & Engineering",
  "leaveType": "MEDICAL",
  "startDate": "2026-10-05",
  "endDate": "2026-10-07",
  "reason": "Viral fever recovery with medical certificate",
  "documentUrl": "/documents/med-cert-24cse0101.pdf"
}
```
- **Response**: `ApiResponse<AttendanceLeave>`

#### `PATCH /api/v1/attendance/leaves/{leaveId}`
- **Method**: `attendanceService.reviewLeave(leaveId, action, reviewerNotes)`
- **Request Body**:
```json
{
  "status": "APPROVED",
  "reviewedBy": "Dr. Ramesh Sundaram",
  "reviewerNotes": "Approved based on submitted hospital prescription."
}
```
- **Response**: `ApiResponse<AttendanceLeave>`

---

### 2.7 Supervised Corrections Workflow

#### `GET /api/v1/attendance/corrections`
- **Method**: `attendanceService.getCorrections(filters?: { status?: string })`
- **Response**: `ApiResponse<AttendanceCorrection[]>`

#### `POST /api/v1/attendance/corrections`
- **Method**: `attendanceService.requestCorrection(data)`
- **Request Body**:
```json
{
  "sessionId": "att-sess-001",
  "recordId": "rec-sess-001-std-001",
  "studentId": "std-001",
  "studentName": "Aarav Patel",
  "rollNumber": "24CSE0101",
  "courseCode": "CS301",
  "courseTitle": "Data Structures & Algorithms",
  "sessionDate": "2026-10-01",
  "originalStatus": "ABSENT",
  "requestedStatus": "PRESENT",
  "reason": "Biometric terminal network timeout during classroom entry; student was verified present."
}
```
- **Response**: `ApiResponse<AttendanceCorrection>`

#### `PATCH /api/v1/attendance/corrections/{correctionId}`
- **Method**: `attendanceService.reviewCorrection(correctionId, action, notes)`
- **Request Body**:
```json
{
  "status": "APPROVED",
  "reviewerNotes": "Verified with lab entry register. Correction sanctioned."
}
```
- **Response**: `ApiResponse<AttendanceCorrection>`

---

### 2.8 Reports

#### `POST /api/v1/attendance/reports/generate`
- **Method**: `attendanceService.generateReport(filters: AttendanceReportFilter)`
- **Request Body**:
```json
{
  "reportType": "LOW_ATTENDANCE",
  "department": "Computer Science & Engineering",
  "semester": 5,
  "startDate": "2026-08-01",
  "endDate": "2026-10-02"
}
```
- **Response**: `ApiResponse<AttendanceReportResult>`

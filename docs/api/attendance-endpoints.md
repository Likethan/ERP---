# Attendance Management Engine API Reference

All endpoints require authentication and are tenant-isolated. Path prefix: `/api/v1/attendance`.

## 1. Attendance Policy Endpoints

### List Policies
- **Endpoint**: `GET /api/v1/attendance/policies`
- **Permission**: `attendance_policy:read`
- **Query Params**: `course_offering_id`, `program_id`, `is_active`
- **Response**: `ApiResponse<List[AttendancePolicyResponse]>`

### Create / Update Policy
- **Endpoint**: `POST /api/v1/attendance/policies`
- **Permission**: `attendance_policy:create`
- **Payload**: `AttendancePolicyCreateRequest`
- **Response**: `ApiResponse<AttendancePolicyResponse>`

---

## 2. Attendance Session Endpoints

### List Sessions
- **Endpoint**: `GET /api/v1/attendance/sessions`
- **Permission**: `attendance:read`
- **Query Params**: `course_offering_id`, `section_id`, `faculty_id`, `date`, `status`, `page`, `page_size`
- **Response**: `PaginatedResponse<AttendanceSessionResponse>`

### Get Session Detail & Roster
- **Endpoint**: `GET /api/v1/attendance/sessions/{id}`
- **Permission**: `attendance:read`
- **Response**: `ApiResponse<AttendanceSessionDetailResponse>`

### Create Manual Session
- **Endpoint**: `POST /api/v1/attendance/sessions`
- **Permission**: `attendance:mark`
- **Payload**: `AttendanceSessionCreateRequest`
- **Response**: `ApiResponse<AttendanceSessionResponse>`

### Instantiate Sessions from Timetable
- **Endpoint**: `POST /api/v1/attendance/sessions/from-timetable`
- **Permission**: `attendance:mark`
- **Payload**: `AttendanceSessionFromTimetableRequest` (`target_date`, `section_id`, `academic_year_id`, `semester_id`)
- **Response**: `ApiResponse<List[AttendanceSessionResponse]>`

### Open Session Register
- **Endpoint**: `POST /api/v1/attendance/sessions/{id}/open`
- **Permission**: `attendance:mark`
- **Response**: `ApiResponse<AttendanceSessionResponse>`

### Lock Session Register
- **Endpoint**: `POST /api/v1/attendance/sessions/{id}/lock`
- **Permission**: `attendance:lock`
- **Response**: `ApiResponse<AttendanceSessionResponse>`

---

## 3. Attendance Record Endpoints

### Bulk Submit Attendance Records
- **Endpoint**: `POST /api/v1/attendance/sessions/{id}/records/bulk`
- **Permission**: `attendance:mark`
- **Payload**: `AttendanceBulkSubmitRequest` (`records: [{ student_id, status, remarks }]`)
- **Response**: `ApiResponse<List[AttendanceRecordResponse]>`

### Update Single Record
- **Endpoint**: `PATCH /api/v1/attendance/records/{id}`
- **Permission**: `attendance:update`
- **Payload**: `AttendanceRecordUpdateRequest`
- **Response**: `ApiResponse<AttendanceRecordResponse>`

---

## 4. Student & Course Attendance Summary Endpoints

### Student Overall & Subject Summary
- **Endpoint**: `GET /api/v1/attendance/students/{student_id}/summary`
- **Permission**: `attendance:read`
- **Response**: `ApiResponse<StudentOverallAttendanceSummary>`

### Course Offering Attendance Summary
- **Endpoint**: `GET /api/v1/attendance/course-offerings/{id}/summary`
- **Permission**: `attendance:read`
- **Response**: `ApiResponse<CourseOfferingAttendanceSummary>`

### Low Attendance Risk Telemetry
- **Endpoint**: `GET /api/v1/attendance/low-attendance`
- **Permission**: `attendance:read`
- **Query Params**: `threshold`, `course_offering_id`
- **Response**: `ApiResponse<List[LowAttendanceStudentItem]>`

### Attendance Dashboard Telemetry
- **Endpoint**: `GET /api/v1/attendance/dashboard`
- **Permission**: `attendance:read`
- **Response**: `ApiResponse<AttendanceDashboardResponse>`

---

## 5. Student Leave Management Endpoints

### List Leaves
- **Endpoint**: `GET /api/v1/attendance/leaves`
- **Permission**: `leave:read`
- **Query Params**: `student_id`, `status`
- **Response**: `ApiResponse<List[StudentLeaveResponse]>`

### Submit Leave Request
- **Endpoint**: `POST /api/v1/attendance/leaves`
- **Permission**: `leave:create`
- **Payload**: `StudentLeaveCreateRequest`
- **Response**: `ApiResponse<StudentLeaveResponse>`

### Approve Leave Request
- **Endpoint**: `POST /api/v1/attendance/leaves/{id}/approve`
- **Permission**: `leave:approve`
- **Payload**: `StudentLeaveReviewRequest`
- **Response**: `ApiResponse<StudentLeaveResponse>`

### Reject Leave Request
- **Endpoint**: `POST /api/v1/attendance/leaves/{id}/reject`
- **Permission**: `leave:reject`
- **Payload**: `StudentLeaveReviewRequest`
- **Response**: `ApiResponse<StudentLeaveResponse>`

---

## 6. Supervised Attendance Correction Endpoints

### List Corrections
- **Endpoint**: `GET /api/v1/attendance/corrections`
- **Permission**: `attendance:read`
- **Query Params**: `student_id`, `course_offering_id`, `status`
- **Response**: `ApiResponse<List[AttendanceCorrectionResponse]>`

### Request Correction on Locked Session
- **Endpoint**: `POST /api/v1/attendance/corrections`
- **Permission**: `attendance:correct`
- **Payload**: `AttendanceCorrectionCreateRequest`
- **Response**: `ApiResponse<AttendanceCorrectionResponse>`

### Approve Correction
- **Endpoint**: `POST /api/v1/attendance/corrections/{id}/approve`
- **Permission**: `attendance:approve_correction`
- **Payload**: `AttendanceCorrectionReviewRequest`
- **Response**: `ApiResponse<AttendanceCorrectionResponse>`

### Reject Correction
- **Endpoint**: `POST /api/v1/attendance/corrections/{id}/reject`
- **Permission**: `attendance:approve_correction`
- **Payload**: `AttendanceCorrectionReviewRequest`
- **Response**: `ApiResponse<AttendanceCorrectionResponse>`

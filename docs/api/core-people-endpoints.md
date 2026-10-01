# CampusOS — Core Institution & People API Specification

All endpoints in this specification require:
1. **Authentication**: Bearer JWT in `Authorization` header.
2. **Tenant Resolution**: Handled automatically from authenticated User context. Cross-tenant access attempts return `404 Not Found`.
3. **Authorization**: Enforced via PBAC (`require_permission`). Unauthorized roles receive `403 Forbidden`.

---

## 1. Institution Management

### `GET /api/v1/institutions`
- **Permission**: `core:institutions:read`
- **Description**: Returns root institution details for the caller's tenant.
- **Response**: `ApiResponse[InstitutionResponse]`

### `PATCH /api/v1/institutions`
- **Permission**: `core:institutions:manage`
- **Description**: Updates institution metadata (legal name, contact info, website, timezone).
- **Request**: `InstitutionUpdateRequest`
- **Response**: `ApiResponse[InstitutionResponse]`

---

## 2. Campus Management

### `GET /api/v1/campuses`
- **Permission**: `core:campuses:read`
- **Description**: Lists physical campuses/branches for the tenant.
- **Response**: `ApiResponse[list[CampusResponse]]`

### `POST /api/v1/campuses`
- **Permission**: `core:campuses:manage`
- **Description**: Creates a new campus branch.
- **Request**: `CampusCreateRequest` (`code`, `name`, `city`, `address`)
- **Status**: `201 Created`
- **Errors**: `409 Conflict` if campus code already exists in tenant.

---

## 3. Academic Departments

### `GET /api/v1/departments`
- **Permission**: `core:departments:read`
- **Query Params**: `campus_id` (optional UUID)
- **Response**: `ApiResponse[list[DepartmentResponse]]`

### `POST /api/v1/departments`
- **Permission**: `core:departments:manage`
- **Description**: Registers a department with optional HOD appointment.
- **Request**: `DepartmentCreateRequest` (`campus_id`, `code`, `name`, `head_of_department_id`)
- **Status**: `201 Created`
- **Errors**: `409 Conflict` on duplicate department code.

### `PATCH /api/v1/departments/{id}`
- **Permission**: `core:departments:manage`
- **Description**: Updates department name, status, or reassigns HOD.
- **Request**: `DepartmentUpdateRequest`

---

## 4. Degree Programs

### `GET /api/v1/programs`
- **Permission**: `core:programs:read`
- **Query Params**: `department_id` (optional UUID), `search` (optional string)
- **Response**: `ApiResponse[list[ProgramResponse]]`

### `POST /api/v1/programs`
- **Permission**: `core:programs:manage`
- **Request**: `ProgramCreateRequest` (`department_id`, `code`, `name`, `degree_level`, `duration_years`, `total_semesters`, `required_credits`)
- **Status**: `201 Created`
- **Errors**: `409 Conflict` on duplicate program code.

---

## 5. Academic Structure

### `GET /api/v1/academic-structure/academic-years`
- **Permission**: `core:academic_years:read`
- **Response**: `ApiResponse[list[AcademicYearResponse]]`

### `POST /api/v1/academic-structure/academic-years`
- **Permission**: `core:academic_years:manage`
- **Request**: `AcademicYearCreateRequest` (`name`, `start_date`, `end_date`, `is_current`)
- **Status**: `201 Created`

### `GET /api/v1/academic-structure/semesters`
- **Permission**: `core:academic_years:read`
- **Query Params**: `academic_year_id` (optional UUID)
- **Response**: `ApiResponse[list[SemesterResponse]]`

### `POST /api/v1/academic-structure/semesters`
- **Permission**: `core:academic_years:manage`
- **Request**: `SemesterCreateRequest` (`academic_year_id`, `name`, `semester_number`, `term_type`, `start_date`, `end_date`)
- **Status**: `201 Created`

### `GET /api/v1/academic-structure/regulations`
- **Permission**: `core:programs:read`
- **Response**: `ApiResponse[list[RegulationResponse]]`

### `POST /api/v1/academic-structure/regulations`
- **Permission**: `core:regulations:manage`
- **Request**: `RegulationCreateRequest` (`code`, `title`, `effective_year`, `description`)
- **Status**: `201 Created`

### `GET /api/v1/academic-structure/batches`
- **Permission**: `core:programs:read`
- **Query Params**: `program_id` (optional UUID)
- **Response**: `ApiResponse[list[BatchResponse]]`

### `POST /api/v1/academic-structure/batches`
- **Permission**: `core:programs:manage`
- **Request**: `BatchCreateRequest` (`program_id`, `regulation_id`, `name`, `admission_year`, `graduation_year`)
- **Status**: `201 Created`

### `GET /api/v1/academic-structure/sections`
- **Permission**: `core:sections:read`
- **Query Params**: `program_id`, `batch_id`, `semester_id`
- **Response**: `ApiResponse[list[SectionResponse]]`

### `POST /api/v1/academic-structure/sections`
- **Permission**: `core:sections:manage`
- **Request**: `SectionCreateRequest` (`program_id`, `batch_id`, `semester_id`, `name`, `capacity`)
- **Status**: `201 Created`
- **Errors**: `409 Conflict` on duplicate section name within the same semester and batch.

---

## 6. Student Management

### `GET /api/v1/students`
- **Permission**: `people:students:read`
- **Query Params**:
  - `page` (int, default: 1)
  - `page_size` (int, default: 25, max: 100)
  - `search` (string: matches student name, roll number, admission number, registration number, or user email)
  - `program_id` (UUID)
  - `batch_id` (UUID)
  - `status` (string enum: `ADMITTED`, `ACTIVE`, `APPLIED`, `SUSPENDED`, `ON_LEAVE`, `GRADUATED`, `WITHDRAWN`, `ALUMNI`)
  - `section_id` (UUID)
- **Response**: `PaginatedResponse[StudentSummaryResponse]`

### `POST /api/v1/students`
- **Permission**: `people:students:create`
- **Description**: Atomic transaction that creates:
  1. `User` authentication identity (with Argon2id password hash).
  2. Role mapping (`STUDENT`).
  3. `StudentProfile` with institutional identifiers and demographics.
  4. Initial `StudentEnrollmentHistory` record.
  5. Initial `StudentStatusHistory` ledger entry (`ADMITTED`).
  6. Audit log entry (`STUDENT_ADMITTED`).
- **Request**: `StudentCreateRequest`
- **Status**: `201 Created`
- **Errors**: `409 Conflict` on duplicate email, admission number, or roll number.

### `GET /api/v1/students/{student_id}`
- **Permission**: `people:students:read`
- **Description**: Fetches 360° profile including historical enrollment ledger and status history.
- **Response**: `ApiResponse[StudentDetailResponse]`

### `PATCH /api/v1/students/{student_id}`
- **Permission**: `people:students:update`
- **Description**: Updates mutable student metadata (roll number, registration number, emergency contacts, current section).
- **Request**: `StudentUpdateRequest`
- **Response**: `ApiResponse[StudentDetailResponse]`

### `POST /api/v1/students/{student_id}/transition-status`
- **Permission**: `people:students:update`
- **Description**: Transitions student lifecycle state subject to transition state machine rules.
- **Request**: `StudentStatusTransitionRequest` (`to_status`, `reason`, `effective_date`)
- **Errors**: `400 Bad Request` on invalid transition (e.g. `WITHDRAWN` to `ACTIVE`).

---

## 7. Faculty & Staff Management

### `GET /api/v1/faculty`
- **Permission**: `people:faculty:read`
- **Query Params**: `department_id`, `search`
- **Response**: `ApiResponse[list[FacultyResponse]]`

### `POST /api/v1/faculty`
- **Permission**: `people:faculty:manage`
- **Description**: Creates `User` account + `FacultyProfile` + assigns `FACULTY` role + optional HOD appointment.
- **Request**: `FacultyCreateRequest`
- **Status**: `201 Created`
- **Errors**: `409 Conflict` on duplicate employee code or email.

### `GET /api/v1/staff`
- **Permission**: `people:staff:read`
- **Query Params**: `department_id`, `search`
- **Response**: `ApiResponse[list[StaffResponse]]`

### `POST /api/v1/staff`
- **Permission**: `people:staff:manage`
- **Description**: Creates `User` account + `StaffProfile` + assigns `STAFF` role.
- **Request**: `StaffCreateRequest`
- **Status**: `201 Created`
- **Errors**: `409 Conflict` on duplicate employee code or email.

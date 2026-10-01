# Attendance Engine Database Schema & Indexing Strategy

## Table Catalog

### 1. `attendance_policies`
Defines institutional and course-level attendance governance rules.
- `id`: UUID (PK)
- `tenant_id`: UUID (FK -> `core_tenants.id`, Index)
- `name`: VARCHAR(128)
- `department_id`, `program_id`, `academic_year_id`, `semester_id`, `course_offering_id`: Nullable UUID FKs
- `minimum_percentage`: NUMERIC(5, 2), default 75.00
- `warning_threshold_percentage`: NUMERIC(5, 2), default 80.00
- `critical_threshold_percentage`: NUMERIC(5, 2), default 65.00
- `condonation_percentage`: NUMERIC(5, 2), default 65.00
- `late_grace_minutes`: INTEGER, default 10
- `late_weight`: NUMERIC(3, 2), default 0.50
- `excused_counts_as_present`: BOOLEAN, default True
- `on_leave_counts_as_present`: BOOLEAN, default True
- `exclude_excused_from_total`: BOOLEAN, default False
- `effective_from`, `effective_to`: DATE
- `status`: VARCHAR(32), default 'ACTIVE'
- `is_active`: BOOLEAN, default True
- **Indexes**: `(tenant_id, is_active)`, `(tenant_id, course_offering_id)`, `(tenant_id, program_id)`

### 2. `attendance_sessions`
Canonical instructional teaching sessions.
- `id`: UUID (PK)
- `tenant_id`: UUID (FK -> `core_tenants.id`, Index)
- `course_offering_id`: UUID (FK -> `academic_course_offerings.id`, Index)
- `section_id`: UUID (FK -> `core_sections.id`, Index)
- `faculty_id`: UUID (FK -> `people_faculty.id`, Index)
- `academic_year_id`: UUID (FK -> `core_academic_years.id`)
- `semester_id`: UUID (FK -> `core_semesters.id`)
- `session_date`: DATE (Index)
- `period_number`: INTEGER
- `session_type`: VARCHAR(32), default 'LECTURE'
- `status`: VARCHAR(32), default 'SCHEDULED' (Index)
- `topic`: VARCHAR(256), nullable
- `start_time`, `end_time`: VARCHAR(16), nullable
- `room_id`: UUID (FK -> `academic_classrooms.id`, nullable)
- `timetable_slot_id`: UUID (FK -> `academic_timetable_entries.id`, nullable)
- `total_enrolled`, `total_present`, `total_absent`, `total_late`, `total_excused`, `total_on_leave`: INTEGER counters
- `submitted_at`, `locked_at`: TIMESTAMPTZ, nullable
- `locked_by_user_id`: UUID (FK -> `people_users.id`, nullable)
- **Indexes**:
  - `ix_att_sess_tenant_course_date`: `(tenant_id, course_offering_id, session_date)`
  - `ix_att_sess_tenant_status`: `(tenant_id, status)`
  - `ix_att_sess_tenant_faculty_date`: `(tenant_id, faculty_id, session_date)`
  - `ix_att_sess_tenant_section`: `(tenant_id, section_id)`

### 3. `attendance_records`
Individual student presence records per session.
- `id`: UUID (PK)
- `tenant_id`: UUID (FK -> `core_tenants.id`, Index)
- `session_id`: UUID (FK -> `attendance_sessions.id`, Index)
- `student_id`: UUID (FK -> `people_students.id`, Index)
- `status`: VARCHAR(32), default 'PRESENT' (Index)
- `remarks`: VARCHAR(256), nullable
- `recorded_by_user_id`: UUID (FK -> `people_users.id`)
- `has_approved_leave`: BOOLEAN, default False
- **Constraints**:
  - `uq_att_record_session_student`: `UniqueConstraint("tenant_id", "session_id", "student_id")`
- **Indexes**:
  - `ix_att_rec_tenant_student_status`: `(tenant_id, student_id, status)`
  - `ix_att_rec_tenant_session`: `(tenant_id, session_id)`

### 4. `attendance_student_leaves`
Student leave requests and approval lifecycle.
- `id`: UUID (PK)
- `tenant_id`: UUID (FK -> `core_tenants.id`, Index)
- `student_id`: UUID (FK -> `people_students.id`, Index)
- `leave_type`: VARCHAR(32) ('SICK', 'CASUAL', 'DUTY', 'MEDICAL', 'BEREAVEMENT')
- `start_date`, `end_date`: DATE (Index)
- `reason`: TEXT
- `proof_storage_key`: VARCHAR(512), nullable
- `status`: VARCHAR(32), default 'PENDING' (Index)
- `reviewed_by_user_id`: UUID (FK -> `people_users.id`, nullable)
- `reviewed_at`: TIMESTAMPTZ, nullable
- `review_notes`: TEXT, nullable
- **Indexes**:
  - `ix_att_leave_tenant_student_dates`: `(tenant_id, student_id, start_date, end_date)`
  - `ix_att_leave_tenant_status`: `(tenant_id, status)`

### 5. `attendance_corrections`
Supervised rectification requests on locked registers.
- `id`: UUID (PK)
- `tenant_id`: UUID (FK -> `core_tenants.id`, Index)
- `attendance_record_id`: UUID (FK -> `attendance_records.id`, Index)
- `session_id`: UUID (FK -> `attendance_sessions.id`)
- `student_id`: UUID (FK -> `people_students.id`, Index)
- `previous_status`: VARCHAR(32)
- `requested_status`: VARCHAR(32)
- `reason`: TEXT
- `requested_by_user_id`: UUID (FK -> `people_users.id`)
- `approved_by_user_id`: UUID (FK -> `people_users.id`, nullable)
- `approval_status`: VARCHAR(32), default 'PENDING' (Index)
- `approval_notes`: TEXT, nullable
- `reviewed_at`: TIMESTAMPTZ, nullable
- **Indexes**:
  - `ix_att_corr_tenant_status`: `(tenant_id, approval_status)`
  - `ix_att_corr_tenant_student`: `(tenant_id, student_id)`

### 6. `attendance_alerts`
Automated threshold alerts and notification events.
- `id`: UUID (PK)
- `tenant_id`: UUID (FK -> `core_tenants.id`, Index)
- `student_id`: UUID (FK -> `people_students.id`, Index)
- `course_offering_id`: UUID (FK -> `academic_course_offerings.id`, nullable)
- `alert_type`: VARCHAR(64) ('LOW_ATTENDANCE_WARNING', 'LOW_ATTENDANCE_CRITICAL', 'CONSECUTIVE_ABSENCE')
- `severity`: VARCHAR(16) ('INFO', 'WARNING', 'CRITICAL')
- `attendance_percentage`, `threshold_percentage`: NUMERIC(5, 2), nullable
- `message`: VARCHAR(512)
- `is_resolved`: BOOLEAN, default False (Index)
- `resolved_at`: TIMESTAMPTZ, nullable
- **Indexes**:
  - `ix_att_alert_tenant_student`: `(tenant_id, student_id)`
  - `ix_att_alert_tenant_unresolved`: `(tenant_id, is_resolved)`

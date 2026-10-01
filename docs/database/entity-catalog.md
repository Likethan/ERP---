# CampusOS — Comprehensive Entity Catalog & Schema Specification

This document provides the definitive architectural schema catalog for all tables across the 11 domains of CampusOS.

---

## 1. Core Domain Tables (`core_*`)

### 1.1 `core_institutions`
- **Purpose**: Top-level tenant anchor representing the university or college system.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant Root (defines `tenant_id` for all downstream tables).
- **Columns**:
  - `code VARCHAR(32) NOT NULL` (e.g., "VSB-ENG")
  - `legal_name VARCHAR(255) NOT NULL`
  - `short_name VARCHAR(64) NOT NULL`
  - `website VARCHAR(255)`
  - `contact_email VARCHAR(255) NOT NULL`
  - `contact_phone VARCHAR(32) NOT NULL`
  - `address_line1 VARCHAR(255) NOT NULL`
  - `city VARCHAR(100) NOT NULL`
  - `state VARCHAR(100) NOT NULL`
  - `postal_code VARCHAR(32) NOT NULL`
  - `country VARCHAR(100) NOT NULL DEFAULT 'India'`
  - `default_timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Kolkata'`
  - `currency_code VARCHAR(8) NOT NULL DEFAULT 'INR'`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Unique Constraints**: `UNIQUE(code)`
- **Indexes**: `CREATE INDEX idx_core_institutions_code ON core_institutions(code);`
- **Delete Strategy**: Never deleted.

### 1.2 `core_campuses`
- **Purpose**: Physical campus locations belonging to an institution.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped (`tenant_id` -> `core_institutions.id`).
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `code VARCHAR(32) NOT NULL` (e.g., "MAIN", "NORTH")
  - `name VARCHAR(255) NOT NULL`
  - `address TEXT NOT NULL`
  - `city VARCHAR(100) NOT NULL`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, code)`
- **Indexes**: `CREATE INDEX idx_campuses_tenant ON core_campuses(tenant_id);`
- **Delete Strategy**: Soft delete via `is_active = FALSE`.

### 1.3 `core_departments`
- **Purpose**: Academic and administrative divisions.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `campus_id UUID REFERENCES core_campuses(id) ON DELETE SET NULL`
  - `code VARCHAR(32) NOT NULL` (e.g., "CSE", "ECE", "MECH")
  - `name VARCHAR(255) NOT NULL`
  - `department_type VARCHAR(32) NOT NULL DEFAULT 'ACADEMIC'` (ACADEMIC, ADMINISTRATIVE)
  - `hod_user_id UUID REFERENCES people_users(id) ON DELETE SET NULL`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, code)`
- **Indexes**: `CREATE INDEX idx_departments_tenant ON core_departments(tenant_id);`

### 1.4 `core_programs`
- **Purpose**: Degree / certification programs offered by academic departments.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `department_id UUID NOT NULL REFERENCES core_departments(id) ON DELETE RESTRICT`
  - `code VARCHAR(32) NOT NULL` (e.g., "BTECH-CSE", "MBA")
  - `name VARCHAR(255) NOT NULL`
  - `degree_level VARCHAR(32) NOT NULL` (UNDERGRADUATE, POSTGRADUATE, DOCTORAL, DIPLOMA)
  - `duration_years NUMERIC(3,1) NOT NULL DEFAULT 4.0`
  - `total_semesters INT NOT NULL DEFAULT 8`
  - `required_credits INT NOT NULL DEFAULT 160`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, code)`
- **Indexes**: `CREATE INDEX idx_programs_tenant_dept ON core_programs(tenant_id, department_id);`

### 1.5 `core_regulations`
- **Purpose**: Academic statutory curriculum schemes (e.g., Autonomous 2021, Autonomous 2025).
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `code VARCHAR(32) NOT NULL` (e.g., "R2021", "R2025")
  - `title VARCHAR(255) NOT NULL`
  - `effective_year INT NOT NULL`
  - `description TEXT`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, code)`

### 1.6 `core_batches`
- **Purpose**: Admitted cohorts of students for a program bound to an academic regulation.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `program_id UUID NOT NULL REFERENCES core_programs(id) ON DELETE RESTRICT`
  - `regulation_id UUID NOT NULL REFERENCES core_regulations(id) ON DELETE RESTRICT`
  - `name VARCHAR(64) NOT NULL` (e.g., "CSE 2024-2028")
  - `admission_year INT NOT NULL`
  - `graduation_year INT NOT NULL`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, program_id, name)`

### 1.7 `core_academic_years`
- **Purpose**: Calendar operational years.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `name VARCHAR(32) NOT NULL` (e.g., "2024-2025")
  - `start_date DATE NOT NULL`
  - `end_date DATE NOT NULL`
  - `is_current BOOLEAN NOT NULL DEFAULT FALSE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, name)`

### 1.8 `core_semesters`
- **Purpose**: Discrete teaching terms within an academic year.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `academic_year_id UUID NOT NULL REFERENCES core_academic_years(id) ON DELETE RESTRICT`
  - `name VARCHAR(64) NOT NULL` (e.g., "Odd Semester 2024-25")
  - `semester_number INT NOT NULL` (1 through 10)
  - `term_type VARCHAR(16) NOT NULL` (ODD, EVEN, SUMMER)
  - `start_date DATE NOT NULL`
  - `end_date DATE NOT NULL`
  - `is_active BOOLEAN NOT NULL DEFAULT FALSE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, academic_year_id, name)`

### 1.9 `core_sections`
- **Purpose**: Student division within a semester cohort.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `program_id UUID NOT NULL REFERENCES core_programs(id) ON DELETE RESTRICT`
  - `batch_id UUID NOT NULL REFERENCES core_batches(id) ON DELETE RESTRICT`
  - `semester_id UUID NOT NULL REFERENCES core_semesters(id) ON DELETE RESTRICT`
  - `name VARCHAR(32) NOT NULL` (e.g., "A", "B")
  - `capacity INT NOT NULL DEFAULT 60`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, program_id, batch_id, semester_id, name)`

---

## 2. People & Identity Tables (`people_*`)

### 2.1 `people_users`
- **Purpose**: Universal authentication account.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Global / Tenant Anchor (Each user is authenticated; in multi-tenant mode, users have a primary tenant or belong to platform).
- **Columns**:
  - `primary_tenant_id UUID REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `email VARCHAR(255) NOT NULL`
  - `phone_number VARCHAR(32)`
  - `password_hash VARCHAR(255) NOT NULL`
  - `first_name VARCHAR(100) NOT NULL`
  - `last_name VARCHAR(100) NOT NULL`
  - `avatar_storage_key VARCHAR(255)`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `is_verified BOOLEAN NOT NULL DEFAULT FALSE`
  - `last_login_at TIMESTAMPTZ`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(email)`
- **Indexes**: `CREATE INDEX idx_users_email ON people_users(email);`

### 2.2 `people_roles`
- **Purpose**: Named collections of permissions.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Scoped or System (`tenant_id = NULL` for global system roles).
- **Columns**:
  - `tenant_id UUID REFERENCES core_institutions(id) ON DELETE CASCADE`
  - `name VARCHAR(64) NOT NULL` (e.g., "SUPER_ADMIN", "HOD", "FACULTY", "STUDENT")
  - `display_name VARCHAR(128) NOT NULL`
  - `description TEXT`
  - `is_system BOOLEAN NOT NULL DEFAULT FALSE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, name)`

### 2.3 `people_permissions`
- **Purpose**: Atomic action identifiers (`domain:resource:action`).
- **Primary Key**: `id UUID`
- **Tenant Scope**: Global System Table (`tenant_id = NULL`).
- **Columns**:
  - `code VARCHAR(128) NOT NULL` (e.g., "attendance:records:write")
  - `domain VARCHAR(64) NOT NULL`
  - `description TEXT NOT NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Unique Constraints**: `UNIQUE(code)`

### 2.4 `people_role_permissions`
- **Purpose**: M:M binding roles to atomic permissions.
- **Primary Key**: `(role_id, permission_id)`
- **Columns**:
  - `role_id UUID NOT NULL REFERENCES people_roles(id) ON DELETE CASCADE`
  - `permission_id UUID NOT NULL REFERENCES people_permissions(id) ON DELETE CASCADE`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

### 2.5 `people_user_roles`
- **Purpose**: M:M binding users to roles with optional organizational scope.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE CASCADE`
  - `user_id UUID NOT NULL REFERENCES people_users(id) ON DELETE CASCADE`
  - `role_id UUID NOT NULL REFERENCES people_roles(id) ON DELETE CASCADE`
  - `campus_id UUID REFERENCES core_campuses(id) ON DELETE CASCADE` (optional scope)
  - `department_id UUID REFERENCES core_departments(id) ON DELETE CASCADE` (optional scope)
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Unique Constraints**: `UNIQUE(tenant_id, user_id, role_id, campus_id, department_id)`

### 2.6 `people_students`
- **Purpose**: Canonical institutional profile for a student.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `user_id UUID NOT NULL REFERENCES people_users(id) ON DELETE RESTRICT`
  - `admission_number VARCHAR(64) NOT NULL`
  - `registration_number VARCHAR(64)`
  - `roll_number VARCHAR(64)`
  - `date_of_birth DATE NOT NULL`
  - `gender VARCHAR(16) NOT NULL` (MALE, FEMALE, OTHER)
  - `blood_group VARCHAR(8)`
  - `status VARCHAR(32) NOT NULL DEFAULT 'ADMITTED'` (APPLIED, ADMITTED, ACTIVE, SUSPENDED, ON_LEAVE, GRADUATED, WITHDRAWN, ALUMNI)
  - `admission_date DATE NOT NULL`
  - `expected_graduation_date DATE NOT NULL`
  - `actual_graduation_date DATE`
  - `program_id UUID NOT NULL REFERENCES core_programs(id) ON DELETE RESTRICT`
  - `batch_id UUID NOT NULL REFERENCES core_batches(id) ON DELETE RESTRICT`
  - `current_semester_id UUID REFERENCES core_semesters(id) ON DELETE RESTRICT`
  - `current_section_id UUID REFERENCES core_sections(id) ON DELETE RESTRICT`
  - `emergency_contact_name VARCHAR(128)`
  - `emergency_contact_phone VARCHAR(32)`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, admission_number)`, `UNIQUE(tenant_id, registration_number)`
- **Indexes**: `CREATE INDEX idx_students_tenant_prog_batch ON people_students(tenant_id, program_id, batch_id);`
- **Delete Strategy**: Never hard-deleted; transitions through status lifecycle.

### 2.7 `people_faculty`
- **Purpose**: Canonical instructional profile for academic faculty.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `user_id UUID NOT NULL REFERENCES people_users(id) ON DELETE RESTRICT`
  - `employee_code VARCHAR(64) NOT NULL`
  - `department_id UUID NOT NULL REFERENCES core_departments(id) ON DELETE RESTRICT`
  - `designation VARCHAR(128) NOT NULL` (PROFESSOR, ASSOCIATE_PROFESSOR, ASSISTANT_PROFESSOR, LECTURER)
  - `highest_qualification VARCHAR(128) NOT NULL`
  - `specialization TEXT`
  - `joining_date DATE NOT NULL`
  - `is_hod BOOLEAN NOT NULL DEFAULT FALSE`
  - `employment_status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE'` (ACTIVE, ON_LEAVE, RESIGNED, RETIRED)
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, employee_code)`

### 2.8 `people_staff`
- **Purpose**: Canonical profile for administrative and logistical staff.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `user_id UUID NOT NULL REFERENCES people_users(id) ON DELETE RESTRICT`
  - `employee_code VARCHAR(64) NOT NULL`
  - `department_id UUID REFERENCES core_departments(id) ON DELETE RESTRICT`
  - `designation VARCHAR(128) NOT NULL`
  - `employment_type VARCHAR(32) NOT NULL DEFAULT 'FULL_TIME'`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, employee_code)`

### 2.9 `people_guardians`
- **Purpose**: Parent / legal guardian profile.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `user_id UUID REFERENCES people_users(id) ON DELETE SET NULL`
  - `first_name VARCHAR(100) NOT NULL`
  - `last_name VARCHAR(100) NOT NULL`
  - `email VARCHAR(255)`
  - `phone_number VARCHAR(32) NOT NULL`
  - `occupation VARCHAR(128)`
  - `annual_income NUMERIC(14,2)`
  - `address TEXT`
  - `created_at / updated_at TIMESTAMPTZ`

### 2.10 `people_student_guardians`
- **Purpose**: M:M relationship between students and guardians.
- **Primary Key**: `(student_id, guardian_id)`
- **Columns**:
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE CASCADE`
  - `guardian_id UUID NOT NULL REFERENCES people_guardians(id) ON DELETE CASCADE`
  - `relationship_type VARCHAR(32) NOT NULL` (FATHER, MOTHER, LEGAL_GUARDIAN, SPONSOR)
  - `is_primary BOOLEAN NOT NULL DEFAULT FALSE`
  - `can_pickup BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

### 2.11 `people_student_semester_enrollments`
- **Purpose**: Non-destructive historical ledger of student terms and section placements.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `academic_year_id UUID NOT NULL REFERENCES core_academic_years(id) ON DELETE RESTRICT`
  - `semester_id UUID NOT NULL REFERENCES core_semesters(id) ON DELETE RESTRICT`
  - `section_id UUID NOT NULL REFERENCES core_sections(id) ON DELETE RESTRICT`
  - `roll_number_snapshot VARCHAR(64)`
  - `status VARCHAR(32) NOT NULL DEFAULT 'ENROLLED'` (ENROLLED, PROMOTED, DETAINED, COMPLETED, WITHDRAWN)
  - `start_date DATE NOT NULL`
  - `end_date DATE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, student_id, semester_id)`
- **Indexes**: `CREATE INDEX idx_student_enrollment_history ON people_student_semester_enrollments(student_id, semester_id);`

### 2.12 `people_student_status_history`
- **Purpose**: Audit trail of student lifecycle transitions.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `from_status VARCHAR(32) NOT NULL`
  - `to_status VARCHAR(32) NOT NULL`
  - `reason TEXT NOT NULL`
  - `authorized_by_user_id UUID NOT NULL REFERENCES people_users(id)`
  - `effective_date DATE NOT NULL`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

---

## 3. Academics Domain Tables (`academics_*`)

### 3.1 `academics_subjects`
- **Purpose**: Canonical intellectual catalog of courses/subjects.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `department_id UUID NOT NULL REFERENCES core_departments(id) ON DELETE RESTRICT`
  - `code VARCHAR(32) NOT NULL` (e.g., "CS301")
  - `title VARCHAR(255) NOT NULL` (e.g., "Data Structures and Algorithms")
  - `credits NUMERIC(3,1) NOT NULL DEFAULT 3.0`
  - `lecture_hours INT NOT NULL DEFAULT 3`
  - `tutorial_hours INT NOT NULL DEFAULT 0`
  - `practical_hours INT NOT NULL DEFAULT 0`
  - `subject_type VARCHAR(32) NOT NULL DEFAULT 'THEORY'` (THEORY, PRACTICAL, INTEGRATED, ELECTIVE, AUDIT)
  - `syllabus_summary TEXT`
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, code)`

### 3.2 `academics_curriculums`
- **Purpose**: Program curriculum scheme bound to a regulation.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `program_id UUID NOT NULL REFERENCES core_programs(id) ON DELETE RESTRICT`
  - `regulation_id UUID NOT NULL REFERENCES core_regulations(id) ON DELETE RESTRICT`
  - `title VARCHAR(255) NOT NULL`
  - `is_locked BOOLEAN NOT NULL DEFAULT FALSE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, program_id, regulation_id)`

### 3.3 `academics_curriculum_subjects`
- **Purpose**: Subjects included in a curriculum scheme for a specific semester.
- **Primary Key**: `id UUID`
- **Columns**:
  - `curriculum_id UUID NOT NULL REFERENCES academics_curriculums(id) ON DELETE CASCADE`
  - `subject_id UUID NOT NULL REFERENCES academics_subjects(id) ON DELETE RESTRICT`
  - `semester_number INT NOT NULL`
  - `is_mandatory BOOLEAN NOT NULL DEFAULT TRUE`
  - `elective_group VARCHAR(64)` (e.g., "Professional Elective I")
  - `credits_override NUMERIC(3,1)`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Unique Constraints**: `UNIQUE(curriculum_id, subject_id, semester_number)`

### 3.4 `academics_course_offerings`
- **Purpose**: Classroom delivery of a subject in a specific term, department, and section.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `subject_id UUID NOT NULL REFERENCES academics_subjects(id) ON DELETE RESTRICT`
  - `academic_year_id UUID NOT NULL REFERENCES core_academic_years(id) ON DELETE RESTRICT`
  - `semester_id UUID NOT NULL REFERENCES core_semesters(id) ON DELETE RESTRICT`
  - `section_id UUID NOT NULL REFERENCES core_sections(id) ON DELETE RESTRICT`
  - `status VARCHAR(32) NOT NULL DEFAULT 'DRAFT'` (DRAFT, ACTIVE, COMPLETED, CANCELLED)
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, subject_id, academic_year_id, semester_id, section_id)`

### 3.5 `academics_course_faculty`
- **Purpose**: Faculty assignment to course offerings.
- **Primary Key**: `(course_offering_id, faculty_id)`
- **Columns**:
  - `course_offering_id UUID NOT NULL REFERENCES academics_course_offerings(id) ON DELETE CASCADE`
  - `faculty_id UUID NOT NULL REFERENCES people_faculty(id) ON DELETE RESTRICT`
  - `role VARCHAR(32) NOT NULL DEFAULT 'PRIMARY_INSTRUCTOR'` (PRIMARY_INSTRUCTOR, CO_INSTRUCTOR, LAB_ASSISTANT)
  - `assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

### 3.6 `academics_course_enrollments`
- **Purpose**: Student enrollment in a course offering.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `course_offering_id UUID NOT NULL REFERENCES academics_course_offerings(id) ON DELETE RESTRICT`
  - `enrollment_type VARCHAR(32) NOT NULL DEFAULT 'REGULAR'` (REGULAR, REPEAT, ARREAR, AUDIT)
  - `status VARCHAR(32) NOT NULL DEFAULT 'ENROLLED'` (ENROLLED, DROPPED, COMPLETED, WITHDRAWN)
  - `enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Unique Constraints**: `UNIQUE(tenant_id, student_id, course_offering_id)`

### 3.7 `academics_timetable_slots`
- **Purpose**: Weekly instructional timetable slot.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `course_offering_id UUID NOT NULL REFERENCES academics_course_offerings(id) ON DELETE CASCADE`
  - `faculty_id UUID REFERENCES people_faculty(id) ON DELETE RESTRICT`
  - `day_of_week INT NOT NULL` (1 = Monday through 7 = Sunday)
  - `period_number INT NOT NULL`
  - `start_time TIME NOT NULL`
  - `end_time TIME NOT NULL`
  - `room_identifier VARCHAR(64) NOT NULL` (e.g., "Hall 302")
  - `is_active BOOLEAN NOT NULL DEFAULT TRUE`
  - `created_at / updated_at TIMESTAMPTZ`

---

## 4. Attendance Domain Tables (`attendance_*`)

### 4.1 `attendance_policies`
- **Purpose**: Attendance thresholds and statutory minimum percentage requirements.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `department_id UUID REFERENCES core_departments(id) ON DELETE RESTRICT`
  - `minimum_percentage NUMERIC(5,2) NOT NULL DEFAULT 75.00`
  - `condonation_percentage NUMERIC(5,2) NOT NULL DEFAULT 65.00`
  - `late_grace_minutes INT NOT NULL DEFAULT 10`
  - `created_at / updated_at TIMESTAMPTZ`

### 4.2 `attendance_sessions`
- **Purpose**: Scheduled lecture or lab attendance capture event.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `course_offering_id UUID NOT NULL REFERENCES academics_course_offerings(id) ON DELETE RESTRICT`
  - `section_id UUID NOT NULL REFERENCES core_sections(id) ON DELETE RESTRICT`
  - `faculty_id UUID NOT NULL REFERENCES people_faculty(id) ON DELETE RESTRICT`
  - `timetable_slot_id UUID REFERENCES academics_timetable_slots(id) ON DELETE SET NULL`
  - `session_date DATE NOT NULL`
  - `period_number INT NOT NULL`
  - `session_type VARCHAR(32) NOT NULL DEFAULT 'LECTURE'` (LECTURE, LAB, TUTORIAL, REMEDIAL)
  - `status VARCHAR(32) NOT NULL DEFAULT 'OPEN'` (OPEN, SUBMITTED, LOCKED)
  - `submitted_at TIMESTAMPTZ`
  - `locked_at TIMESTAMPTZ`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, course_offering_id, session_date, period_number)`

### 4.3 `attendance_records`
- **Purpose**: Atomic attendance presence status per student per session.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `session_id UUID NOT NULL REFERENCES attendance_sessions(id) ON DELETE CASCADE`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `status VARCHAR(32) NOT NULL DEFAULT 'PRESENT'` (PRESENT, ABSENT, LATE, EXCUSED, ON_DUTY)
  - `remarks VARCHAR(255)`
  - `recorded_by_user_id UUID NOT NULL REFERENCES people_users(id)`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(session_id, student_id)`
- **Indexes**: `CREATE INDEX idx_attendance_records_student ON attendance_records(student_id, status);`

### 4.4 `attendance_corrections`
- **Purpose**: Supervised correction workflow for locked attendance records.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `attendance_record_id UUID NOT NULL REFERENCES attendance_records(id) ON DELETE RESTRICT`
  - `previous_status VARCHAR(32) NOT NULL`
  - `requested_status VARCHAR(32) NOT NULL`
  - `reason TEXT NOT NULL`
  - `requested_by_user_id UUID NOT NULL REFERENCES people_users(id)`
  - `approved_by_user_id UUID REFERENCES people_users(id)`
  - `approval_status VARCHAR(32) NOT NULL DEFAULT 'PENDING'` (PENDING, APPROVED, REJECTED)
  - `approval_notes TEXT`
  - `created_at / updated_at TIMESTAMPTZ`

### 4.5 `attendance_leave_requests`
- **Purpose**: Student formal leave applications.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `leave_type VARCHAR(32) NOT NULL` (MEDICAL, CASUAL, ON_DUTY, SPORTS)
  - `start_date DATE NOT NULL`
  - `end_date DATE NOT NULL`
  - `reason TEXT NOT NULL`
  - `proof_storage_key VARCHAR(255)`
  - `status VARCHAR(32) NOT NULL DEFAULT 'PENDING'` (PENDING, APPROVED, REJECTED)
  - `reviewed_by_user_id UUID REFERENCES people_users(id)`
  - `created_at / updated_at TIMESTAMPTZ`

---

## 5. Examination Domain Tables (`examination_*`)

### 5.1 `examination_grade_scales` & `examination_grade_items`
- **Purpose**: Grading framework (e.g., 10-point scale: O, A+, A, B+, B, C, F).
- **Scale Primary Key**: `id UUID`
- **Items Primary Key**: `id UUID`
- **Columns (Items)**:
  - `grade_scale_id UUID NOT NULL REFERENCES examination_grade_scales(id) ON DELETE CASCADE`
  - `grade_letter VARCHAR(8) NOT NULL` (O, A+, A, B, etc.)
  - `grade_point NUMERIC(3,1) NOT NULL` (10.0, 9.0, etc.)
  - `min_mark_percent NUMERIC(5,2) NOT NULL`
  - `max_mark_percent NUMERIC(5,2) NOT NULL`
  - `is_passing BOOLEAN NOT NULL DEFAULT TRUE`

### 5.2 `examination_terms`
- **Purpose**: Formal examination cycles.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `academic_year_id UUID NOT NULL REFERENCES core_academic_years(id) ON DELETE RESTRICT`
  - `semester_id UUID NOT NULL REFERENCES core_semesters(id) ON DELETE RESTRICT`
  - `name VARCHAR(128) NOT NULL` (e.g., "Nov/Dec 2024 University Examinations")
  - `exam_type VARCHAR(32) NOT NULL` (INTERNAL_ASSESSMENT, END_SEMESTER, SUPPLEMENTARY)
  - `start_date DATE NOT NULL`
  - `end_date DATE NOT NULL`
  - `status VARCHAR(32) NOT NULL DEFAULT 'DRAFT'` (DRAFT, SCHEDULED, IN_PROGRESS, EVALUATION, COMPLETED, PUBLISHED)
  - `created_at / updated_at TIMESTAMPTZ`

### 5.3 `examination_assessments`
- **Purpose**: Evaluation components (CIA 1, Model Exam, End Semester Theory).
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `course_offering_id UUID NOT NULL REFERENCES academics_course_offerings(id) ON DELETE RESTRICT`
  - `exam_term_id UUID REFERENCES examination_terms(id) ON DELETE RESTRICT`
  - `title VARCHAR(128) NOT NULL`
  - `assessment_type VARCHAR(32) NOT NULL` (CIA_1, CIA_2, ASSIGNMENT, PRACTICAL, SEMESTER_EXAM)
  - `max_marks NUMERIC(5,2) NOT NULL DEFAULT 100.00`
  - `weightage_percent NUMERIC(5,2) NOT NULL`
  - `created_at / updated_at TIMESTAMPTZ`

### 5.4 `examination_student_marks`
- **Purpose**: Raw scored marks.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `assessment_id UUID NOT NULL REFERENCES examination_assessments(id) ON DELETE CASCADE`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `marks_obtained NUMERIC(5,2)`
  - `is_absent BOOLEAN NOT NULL DEFAULT FALSE`
  - `evaluated_by_faculty_id UUID REFERENCES people_faculty(id)`
  - `moderated_marks NUMERIC(5,2)`
  - `remarks TEXT`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(assessment_id, student_id)`

### 5.5 `examination_results`
- **Purpose**: Official, finalized semester transcript grade per course.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `course_offering_id UUID NOT NULL REFERENCES academics_course_offerings(id) ON DELETE RESTRICT`
  - `exam_term_id UUID NOT NULL REFERENCES examination_terms(id) ON DELETE RESTRICT`
  - `internal_marks NUMERIC(5,2) NOT NULL DEFAULT 0.00`
  - `external_marks NUMERIC(5,2) NOT NULL DEFAULT 0.00`
  - `total_marks NUMERIC(5,2) NOT NULL DEFAULT 0.00`
  - `grade_letter VARCHAR(8) NOT NULL`
  - `grade_point NUMERIC(3,1) NOT NULL`
  - `credits_earned NUMERIC(3,1) NOT NULL`
  - `result_status VARCHAR(32) NOT NULL DEFAULT 'PASS'` (PASS, FAIL, ABSENT, WITHHELD, MALPRACTICE)
  - `publication_status VARCHAR(32) NOT NULL DEFAULT 'DRAFT'` (DRAFT, REVIEW, APPROVED, PUBLISHED)
  - `published_at TIMESTAMPTZ`
  - `published_by_user_id UUID REFERENCES people_users(id)`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, student_id, course_offering_id, exam_term_id)`
- **Immutability**: When `publication_status == 'PUBLISHED'`, updates are locked.

---

## 6. Finance & Billing Domain Tables (`finance_*`)

### 6.1 `finance_fee_categories`
- **Purpose**: Fee categorization heads (Tuition, Hostel, Transport, Exam).
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `code VARCHAR(32) NOT NULL` (e.g., "TUITION", "HOSTEL", "BUS")
  - `name VARCHAR(128) NOT NULL`
  - `is_refundable BOOLEAN NOT NULL DEFAULT FALSE`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, code)`

### 6.2 `finance_fee_structures`
- **Purpose**: Structured fee catalog for a program, batch, and term.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `program_id UUID NOT NULL REFERENCES core_programs(id) ON DELETE RESTRICT`
  - `academic_year_id UUID NOT NULL REFERENCES core_academic_years(id) ON DELETE RESTRICT`
  - `batch_id UUID REFERENCES core_batches(id) ON DELETE RESTRICT`
  - `quota_type VARCHAR(32) NOT NULL DEFAULT 'GENERAL'` (GENERAL, MANAGEMENT, GOVERNMENT, NRI)
  - `name VARCHAR(128) NOT NULL`
  - `created_at / updated_at TIMESTAMPTZ`

### 6.3 `finance_fee_items`
- **Purpose**: Specific fee line items in a structure.
- **Primary Key**: `id UUID`
- **Columns**:
  - `fee_structure_id UUID NOT NULL REFERENCES finance_fee_structures(id) ON DELETE CASCADE`
  - `category_id UUID NOT NULL REFERENCES finance_fee_categories(id) ON DELETE RESTRICT`
  - `name VARCHAR(128) NOT NULL`
  - `amount NUMERIC(12,2) NOT NULL`
  - `is_optional BOOLEAN NOT NULL DEFAULT FALSE`

### 6.4 `finance_concessions`
- **Purpose**: Scholarships and concessions applied to a student.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `category_id UUID NOT NULL REFERENCES finance_fee_categories(id) ON DELETE RESTRICT`
  - `academic_year_id UUID NOT NULL REFERENCES core_academic_years(id) ON DELETE RESTRICT`
  - `concession_type VARCHAR(32) NOT NULL` (SCHOLARSHIP, SIBLING_DISCOUNT, SPORTS_QUOTA, WAIVER)
  - `amount NUMERIC(12,2) NOT NULL`
  - `approved_by_user_id UUID NOT NULL REFERENCES people_users(id)`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

### 6.5 `finance_invoices`
- **Purpose**: Official institutional billing statement.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `academic_year_id UUID NOT NULL REFERENCES core_academic_years(id) ON DELETE RESTRICT`
  - `semester_id UUID REFERENCES core_semesters(id) ON DELETE RESTRICT`
  - `invoice_number VARCHAR(64) NOT NULL` (e.g., "INV-2024-00124")
  - `issue_date DATE NOT NULL`
  - `due_date DATE NOT NULL`
  - `gross_amount NUMERIC(12,2) NOT NULL`
  - `concession_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00`
  - `net_payable NUMERIC(12,2) NOT NULL`
  - `paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00`
  - `balance_amount NUMERIC(12,2) NOT NULL`
  - `status VARCHAR(32) NOT NULL DEFAULT 'DRAFT'` (DRAFT, ISSUED, PARTIALLY_PAID, PAID, OVERDUE, CANCELLED)
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, invoice_number)`
- **Indexes**: `CREATE INDEX idx_invoices_student_status ON finance_invoices(student_id, status);`

### 6.6 `finance_invoice_items`
- **Purpose**: Itemized fee breakdown on an invoice.
- **Primary Key**: `id UUID`
- **Columns**:
  - `invoice_id UUID NOT NULL REFERENCES finance_invoices(id) ON DELETE CASCADE`
  - `category_id UUID NOT NULL REFERENCES finance_fee_categories(id) ON DELETE RESTRICT`
  - `description VARCHAR(255) NOT NULL`
  - `amount NUMERIC(12,2) NOT NULL`
  - `waived_amount NUMERIC(12,2) NOT NULL DEFAULT 0.00`

### 6.7 `finance_payments`
- **Purpose**: Inward payment transactions (electronic or manual).
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `transaction_reference VARCHAR(128) NOT NULL`
  - `payment_mode VARCHAR(32) NOT NULL` (CASH, CHEQUE, DD, NEFT_RTGS, UPI, GATEWAY)
  - `gateway_provider VARCHAR(64)` (RAZORPAY, STRIPE, CASHFREE, BILLDESK)
  - `gateway_transaction_id VARCHAR(128)`
  - `payment_date TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `amount NUMERIC(12,2) NOT NULL`
  - `currency VARCHAR(8) NOT NULL DEFAULT 'INR'`
  - `status VARCHAR(32) NOT NULL DEFAULT 'INITIATED'` (INITIATED, SUCCESS, FAILED, REVERSED)
  - `received_by_user_id UUID REFERENCES people_users(id)`
  - `remarks TEXT`
  - `created_at / updated_at TIMESTAMPTZ`
- **Unique Constraints**: `UNIQUE(tenant_id, transaction_reference)`

### 6.8 `finance_allocations`
- **Purpose**: Explicit allocation of payments to invoices.
- **Primary Key**: `id UUID`
- **Columns**:
  - `payment_id UUID NOT NULL REFERENCES finance_payments(id) ON DELETE RESTRICT`
  - `invoice_id UUID NOT NULL REFERENCES finance_invoices(id) ON DELETE RESTRICT`
  - `allocated_amount NUMERIC(12,2) NOT NULL`
  - `allocated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

### 6.9 `finance_receipts`
- **Purpose**: Legal receipts issued for successful payments.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `payment_id UUID NOT NULL REFERENCES finance_payments(id) ON DELETE RESTRICT`
  - `receipt_number VARCHAR(64) NOT NULL` (e.g., "RCP-2024-00982")
  - `issue_date TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `pdf_storage_key VARCHAR(255)`
  - `is_cancelled BOOLEAN NOT NULL DEFAULT FALSE`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Unique Constraints**: `UNIQUE(tenant_id, receipt_number)`

### 6.10 `finance_refunds` & `finance_adjustments`
- **Purpose**: Controlled credit/debit adjustments and formal refunds without mutating history.
- **Primary Key**: `id UUID`
- **Columns**:
  - Reference to `invoice_id`, `payment_id`, `amount`, `reason`, `authorized_by_user_id`, `status`.

---

## 7. Placement Domain Tables (`placement_*`)

### 7.1 `placement_companies` & `placement_contacts`
- **Purpose**: Recruiting companies and HR contact profiles.
- **Company Key**: `id UUID`, `tenant_id`, `name`, `industry`, `tier`, `website`.
- **Contact Key**: `id UUID`, `company_id`, `name`, `email`, `phone`, `designation`.

### 7.2 `placement_drives`
- **Purpose**: Recruitment event for an academic year.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `company_id UUID NOT NULL REFERENCES placement_companies(id) ON DELETE RESTRICT`
  - `academic_year_id UUID NOT NULL REFERENCES core_academic_years(id) ON DELETE RESTRICT`
  - `title VARCHAR(255) NOT NULL`
  - `drive_type VARCHAR(32) NOT NULL DEFAULT 'ON_CAMPUS'` (ON_CAMPUS, POOLED, OFF_CAMPUS, VIRTUAL)
  - `registration_deadline TIMESTAMPTZ NOT NULL`
  - `drive_date DATE NOT NULL`
  - `status VARCHAR(32) NOT NULL DEFAULT 'ANNOUNCED'` (DRAFT, ANNOUNCED, REGISTRATION_OPEN, ONGOING, COMPLETED, CANCELLED)
  - `created_at / updated_at TIMESTAMPTZ`

### 7.3 `placement_positions` & `placement_eligibility_rules`
- **Purpose**: Job position, salary packages (CTC), and automated eligibility criteria.
- **Columns (Positions)**:
  - `job_drive_id UUID NOT NULL REFERENCES placement_drives(id) ON DELETE CASCADE`
  - `designation VARCHAR(128) NOT NULL`
  - `ctc_annual NUMERIC(10,2) NOT NULL` (LPA)
  - `stipend_monthly NUMERIC(10,2)`
  - `location VARCHAR(128)`
- **Columns (Rules)**:
  - `position_id UUID NOT NULL REFERENCES placement_positions(id) ON DELETE CASCADE`
  - `min_cgpa NUMERIC(4,2) NOT NULL DEFAULT 6.00`
  - `max_active_backlogs INT NOT NULL DEFAULT 0`
  - `max_history_backlogs INT NOT NULL DEFAULT 0`
  - `min_attendance_percent NUMERIC(5,2) NOT NULL DEFAULT 75.00`

### 7.4 `placement_applications`
- **Purpose**: Student application and progression through selection rounds.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `position_id UUID NOT NULL REFERENCES placement_positions(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `application_number VARCHAR(64) NOT NULL`
  - `status VARCHAR(32) NOT NULL DEFAULT 'APPLIED'` (APPLIED, ELIGIBLE, INELIGIBLE, SHORTLISTED, IN_SELECTION, OFFERED, REJECTED, WITHDRAWN)
  - `applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Unique Constraints**: `UNIQUE(tenant_id, position_id, student_id)`

### 7.5 `placement_interview_rounds` & `placement_interview_results`
- **Purpose**: Multi-stage interviews (Aptitude, Coding, Technical, HR).
- **Columns**: Round number, round name, score, outcome (`CLEARED`, `ELIMINATED`, `ON_HOLD`).

### 7.6 `placement_offers`
- **Purpose**: Formal job offers extended to students.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `application_id UUID NOT NULL REFERENCES placement_applications(id) ON DELETE RESTRICT`
  - `student_id UUID NOT NULL REFERENCES people_students(id) ON DELETE RESTRICT`
  - `offered_ctc NUMERIC(10,2) NOT NULL`
  - `offer_letter_storage_key VARCHAR(255)`
  - `valid_until DATE NOT NULL`
  - `student_decision VARCHAR(32) NOT NULL DEFAULT 'PENDING'` (PENDING, ACCEPTED, REJECTED, RENEGED)
  - `decision_date TIMESTAMPTZ`
  - `created_at / updated_at TIMESTAMPTZ`

---

## 8. Campus Domain Tables (`campus_*`)

### 8.1 `campus_clubs` & `campus_club_memberships`
- **Purpose**: Student clubs, societies, and member roles (`MEMBER`, `EXECUTIVE`, `PRESIDENT`).

### 8.2 `campus_events` & `campus_event_registrations`
- **Purpose**: Campus events, symposiums, hackathons, and participant attendance check-ins.

### 8.3 `campus_announcements` & `campus_notifications`
- **Purpose**: Institutional targeted broadcast notices (targeted by institution, campus, department, semester, section, or role) and individual user notification inbox items.

---

## 9. Infrastructure Domain Tables (`infrastructure_*`)

### 9.1 Hostel: `infrastructure_hostels`, `blocks`, `floors`, `rooms`, `beds`
- **Physical Hierarchy**: Hostel -> Block -> Floor -> Room -> Bed (`B101-A`).

### 9.2 `infrastructure_hostel_allocations`
- **Purpose**: Non-destructive historical bed allocation tracking (`check_in_date`, `check_out_date`, status `ALLOCATED -> VACATED -> CANCELLED`).

### 9.3 `infrastructure_hostel_passes` & `complaints`
- **Purpose**: Outing/leave passes with parental consent tracking and maintenance ticketing.

### 9.4 Transport: `infrastructure_vehicles`, `drivers`, `routes`, `stops`
- **Route Hierarchy**: Vehicle & Driver -> Route -> Ordered Stops with pickup times and fare tiers.

### 9.5 `infrastructure_transport_allocations`
- **Purpose**: Historical and active student transport passes bound to a stop, route, and academic year.

---

## 10. Documents Domain Tables (`documents_*`)

### 10.1 `documents_categories` & `documents_storage_records`
- **Decoupled Binary Storage**: Relational table holds metadata (file name, MIME type, size, SHA-256 checksum, S3 bucket, storage key).

### 10.2 `documents_student_records` & `documents_faculty_records`
- **Document Verification**: Links student/faculty to storage records with verification status (`PENDING -> VERIFIED -> REJECTED`), verifier ID, and audit notes.

### 10.3 `documents_certificate_templates` & `documents_issued_certificates`
- **Verifiable Credentials**: Jinja templates and cryptographically hashed digital certificates issued to students.

---

## 11. Intelligence & Audit Tables (`intelligence_*`)

### 11.1 `intelligence_audit_logs`
- **Purpose**: Immutable append-only audit trail for all sensitive operations.
- **Primary Key**: `id UUID`
- **Tenant Scope**: Tenant-scoped.
- **Columns**:
  - `tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT`
  - `user_id UUID REFERENCES people_users(id) ON DELETE SET NULL`
  - `action VARCHAR(64) NOT NULL` (CREATE, UPDATE, DELETE, PUBLISH, APPROVE, REVERSE)
  - `entity_type VARCHAR(64) NOT NULL` (Student, Invoice, Payment, Mark, Attendance)
  - `entity_id UUID NOT NULL`
  - `old_values_json JSONB`
  - `new_values_json JSONB`
  - `ip_address VARCHAR(45)`
  - `user_agent TEXT`
  - `business_context TEXT`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Indexes**: `CREATE INDEX idx_audit_entity ON intelligence_audit_logs(tenant_id, entity_type, entity_id);`, `CREATE INDEX idx_audit_created ON intelligence_audit_logs(tenant_id, created_at);`

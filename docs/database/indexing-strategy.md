# CampusOS — Database Indexing Strategy

## 1. Indexing Principles

In a high-scale institutional ERP supporting thousands of concurrent students, faculty, and administrative staff, query performance depends on deliberate, query-driven indexing:

1. **Tenant-First Indexing**: Because CampusOS employs row-level multi-tenancy, queries universally filter by `tenant_id`. B-Tree composite indexes must place `tenant_id` as the leading column.
2. **Foreign Key Indexing**: PostgreSQL does not automatically index foreign key columns. Unindexed foreign keys cause sequential table scans during joins and lock parent/child rows during deletions. All foreign keys in CampusOS are explicitly indexed.
3. **Partial Indexing for Active Records**: Operational queries overwhelmingly seek active records (`is_active = TRUE` or `status = 'ACTIVE'`). Partial indexes minimize index size and memory footprint while accelerating hot operational queries.

---

## 2. Core Operational Indexing Specifications

### 2.1 Core & People Domains
```sql
-- Fast lookups of students by institutional identifier within tenant
CREATE UNIQUE INDEX uq_students_tenant_admission ON people_students(tenant_id, admission_number);
CREATE UNIQUE INDEX uq_students_tenant_registration ON people_students(tenant_id, registration_number);
CREATE INDEX idx_students_tenant_program_batch ON people_students(tenant_id, program_id, batch_id);
CREATE INDEX idx_students_tenant_section ON people_students(tenant_id, current_section_id);

-- Partial index for active enrolled students
CREATE INDEX idx_students_active_cohort ON people_students(tenant_id, program_id, current_semester_id)
WHERE status = 'ACTIVE';

-- Fast user email lookup for authentication
CREATE UNIQUE INDEX uq_users_email ON people_users(email);

-- Scoped role lookups
CREATE INDEX idx_user_roles_lookup ON people_user_roles(tenant_id, user_id, role_id);
CREATE INDEX idx_user_roles_dept_scope ON people_user_roles(tenant_id, department_id) WHERE department_id IS NOT NULL;
```

### 2.2 Academics Domain
```sql
-- Course offering lookup for student timetables
CREATE INDEX idx_course_offerings_term ON academics_course_offerings(tenant_id, academic_year_id, semester_id, section_id);

-- Student course enrollment index
CREATE UNIQUE INDEX uq_course_enrollments_student ON academics_course_enrollments(tenant_id, student_id, course_offering_id);

-- Timetable slot collision detection (Room & Faculty conflict prevention)
CREATE INDEX idx_timetable_room_conflict ON academics_timetable_slots(tenant_id, day_of_week, period_number, room_identifier);
CREATE INDEX idx_timetable_faculty_conflict ON academics_timetable_slots(tenant_id, day_of_week, period_number, faculty_id);
```

### 2.3 Attendance Domain
```sql
-- Attendance session lookup by course and date
CREATE INDEX idx_attendance_sessions_course_date ON attendance_sessions(tenant_id, course_offering_id, session_date);

-- Fast attendance percentage derivation per student
CREATE INDEX idx_attendance_records_student_status ON attendance_records(student_id, status);

-- Session-level record retrieval
CREATE INDEX idx_attendance_records_session ON attendance_records(session_id);
```

### 2.4 Examination Domain
```sql
-- Student marksheet generation query
CREATE INDEX idx_exam_student_marks ON examination_student_marks(tenant_id, student_id);
CREATE INDEX idx_exam_assessment_marks ON examination_student_marks(assessment_id);

-- Published results lookup for transcript and grade card printing
CREATE UNIQUE INDEX uq_exam_results_published ON examination_results(tenant_id, student_id, course_offering_id, exam_term_id);
CREATE INDEX idx_exam_results_student_term ON examination_results(tenant_id, student_id, exam_term_id);
```

### 2.5 Finance Domain
```sql
-- Student ledger and fee clearance query
CREATE INDEX idx_invoices_student_due ON finance_invoices(tenant_id, student_id, status, due_date);

-- Payment allocation lookup
CREATE INDEX idx_payment_allocations_invoice ON finance_allocations(invoice_id);
CREATE INDEX idx_payment_allocations_payment ON finance_allocations(payment_id);

-- Transaction reference lookup for gateway webhook idempotency
CREATE UNIQUE INDEX uq_payments_tenant_ref ON finance_payments(tenant_id, transaction_reference);
```

### 2.6 Placement Domain
```sql
-- Placement drive active applicants
CREATE INDEX idx_placement_applications_position ON placement_applications(tenant_id, position_id, status);
CREATE INDEX idx_placement_applications_student ON placement_applications(tenant_id, student_id);
```

### 2.7 Audit & Intelligence Domain
```sql
-- Entity mutation history timeline
CREATE INDEX idx_audit_tenant_entity ON intelligence_audit_logs(tenant_id, entity_type, entity_id, created_at DESC);

-- Chronological tenant activity feed
CREATE INDEX idx_audit_tenant_chronological ON intelligence_audit_logs(tenant_id, created_at DESC);
```

# CampusOS — DDD Bounded Contexts & Aggregate Boundaries

## 1. Domain-Driven Design in a Modular Monolith

CampusOS organizes its codebase and database around **11 discrete Bounded Contexts**. In a distributed microservices architecture, bounded contexts often become distinct network services with separate databases and eventual consistency overhead. In CampusOS's **Modular Monolith**, bounded contexts are preserved through strictly encapsulated Python modules (`app/domains/*`), while sharing a unified transactional database engine (PostgreSQL).

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CAMPUSOS MODULAR MONOLITH                       │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ 1. Core           │ 2. People         │ 3. Academics                   │
│ (Org Metadata)    │ (Single Identity) │ (Curriculum & Delivery)        │
├───────────────────┼───────────────────┼────────────────────────────────┤
│ 4. Attendance     │ 5. Examination    │ 6. Finance                     │
│ (Class Records)   │ (Grades & Trans.) │ (Immutable Ledger & Billing)   │
├───────────────────┼───────────────────┼────────────────────────────────┤
│ 7. Placement      │ 8. Campus Life    │ 9. Infrastructure              │
│ (Corporate Hiring)│ (Clubs & Events)  │ (Hostel & Transport Logistics) │
├───────────────────┼───────────────────┼────────────────────────────────┤
│ 10. Documents     │ 11. Intelligence  │                                │
│ (Object Storage)  │ (Audit & AI Tools)│                                │
└───────────────────┴───────────────────┴────────────────────────────────┘
```

---

## 2. Core Aggregates and Invariants

An **Aggregate** is a cluster of domain objects that can be treated as a single unit for data changes. Every aggregate has an **Aggregate Root** (the only entity external callers can reference directly):

### 2.1 The `Student` Aggregate (Bounded Context: People)
- **Aggregate Root**: `StudentProfile` (`people_students`)
- **Owned Entities**:
  - `StudentGuardianRelationship` (`people_student_guardians`)
  - `StudentSemesterEnrollment` (`people_student_semester_enrollments`)
  - `StudentStatusHistory` (`people_student_status_history`)
- **Key Invariants**:
  1. A student cannot possess two overlapping active semester enrollments within the same academic period.
  2. Transitioning a student status (e.g. from `ACTIVE` to `GRADUATED`) requires recording an entry in `StudentStatusHistory`.
  3. A student's `admission_number` and `registration_number` must be universally unique within their tenant.

---

### 2.2 The `CourseOffering` Aggregate (Bounded Context: Academics)
- **Aggregate Root**: `CourseOffering` (`academics_course_offerings`)
- **Owned Entities**:
  - `CourseFacultyAssignment` (`academics_course_faculty`)
  - `CourseEnrollment` (`academics_course_enrollments`)
  - `TimetableSlot` (`academics_timetable_slots`)
- **Key Invariants**:
  1. Exactly one primary faculty member must be assigned before a course offering can transition to `ACTIVE`.
  2. Timetable slots within the offering cannot produce time or room collisions with other active timetable slots.
  3. A student cannot be enrolled multiple times in the same offering.

---

### 2.3 The `AttendanceSession` Aggregate (Bounded Context: Attendance)
- **Aggregate Root**: `AttendanceSession` (`attendance_sessions`)
- **Owned Entities**:
  - `AttendanceRecord` (`attendance_records`)
- **Key Invariants**:
  1. Attendance records can only be created for students actively enrolled in the parent `CourseOffering`.
  2. Once the session transitions to `LOCKED`, child `AttendanceRecord` rows cannot be modified in-place; modifications require an approved `AttendanceCorrectionRequest`.
  3. Duplicate attendance sessions for the same section, course offering, date, and period number are prohibited.

---

### 2.4 The `Invoice` Aggregate (Bounded Context: Finance)
- **Aggregate Root**: `Invoice` (`finance_invoices`)
- **Owned Entities**:
  - `InvoiceLineItem` (`finance_invoice_items`)
  - `FinancialAdjustment` (`finance_adjustments`)
- **Key Invariants**:
  1. `gross_amount` must equal the exact sum of `InvoiceLineItem.amount`.
  2. `net_payable` must equal `gross_amount - concession_amount`.
  3. `balance_amount` must equal `net_payable - paid_amount`.
  4. Once `status == 'ISSUED'`, line item amounts cannot be altered; discounts must be applied as formal credit adjustments.

---

### 2.5 The `Payment` Aggregate (Bounded Context: Finance)
- **Aggregate Root**: `PaymentTransaction` (`finance_payments`)
- **Owned Entities**:
  - `PaymentAllocation` (`finance_allocations`)
  - `Receipt` (`finance_receipts`)
- **Key Invariants**:
  1. The sum of `PaymentAllocation.allocated_amount` across all targeted invoices must be `<= PaymentTransaction.amount`.
  2. An official `Receipt` can only be generated when `status == 'SUCCESS'`.
  3. A successful payment record is strictly immutable; corrections require a `RefundTransaction`.

---

### 2.6 The `ExamTerm` & `SemesterResult` Aggregate (Bounded Context: Examination)
- **Aggregate Root**: `SemesterExamResult` (`examination_results`)
- **Key Invariants**:
  1. `total_marks` must equal `internal_marks + external_marks`.
  2. `grade_letter` and `grade_point` must strictly correspond to the institution's official `GradeScale` based on `total_marks`.
  3. Once `publication_status == 'PUBLISHED'`, the record is locked against direct mutation.

---

### 2.7 The `JobDrive` Aggregate (Bounded Context: Placement)
- **Aggregate Root**: `JobDrive` (`placement_drives`)
- **Owned Entities**:
  - `JobPosition` (`placement_positions`)
  - `PlacementEligibilityRule` (`placement_eligibility_rules`)
  - `InterviewRound` (`placement_interview_rounds`)
- **Key Invariants**:
  1. Applications cannot be submitted after `registration_deadline`.
  2. Students who do not meet the minimum CGPA, backlog, or attendance rules defined in `PlacementEligibilityRule` are marked `INELIGIBLE`.

---

## 3. Transaction Boundaries (Atomic Operations)

Because CampusOS is a modular monolith running on a single PostgreSQL instance, operations that cross domain boundaries can be coordinated inside a single **ACID database transaction**:

### 3.1 Student Admission & Billing Atomic Transaction
```text
BEGIN TRANSACTION;
  1. INSERT INTO people_users (id, email, password_hash, ...)
  2. INSERT INTO people_students (id, user_id, admission_number, program_id, batch_id, ...)
  3. INSERT INTO people_student_semester_enrollments (student_id, semester_id, section_id, ...)
  4. Query finance_fee_structures for program & batch
  5. INSERT INTO finance_invoices (student_id, gross_amount, net_payable, ...)
  6. INSERT INTO finance_invoice_items (...)
  7. INSERT INTO intelligence_audit_logs (action = 'STUDENT_ADMISSION', entity_id = student_id, ...)
COMMIT;
```
If fee invoice generation fails, the entire student creation is safely rolled back, preventing orphaned records.

### 3.2 Payment Capture & Allocation Atomic Transaction
```text
BEGIN TRANSACTION;
  1. INSERT INTO finance_payments (transaction_reference, amount, status = 'SUCCESS', ...)
  2. INSERT INTO finance_allocations (payment_id, invoice_id, allocated_amount)
  3. UPDATE finance_invoices SET paid_amount = paid_amount + :allocated_amount, balance_amount = balance_amount - :allocated_amount
  4. UPDATE finance_invoices SET status = CASE WHEN balance_amount = 0 THEN 'PAID' ELSE 'PARTIALLY_PAID' END
  5. INSERT INTO finance_receipts (receipt_number, payment_id, issue_date, ...)
  6. INSERT INTO intelligence_audit_logs (action = 'PAYMENT_RECORDED', ...)
COMMIT;
```

---

## 4. Cross-Domain Communication Rules

1. **No Direct Cross-Domain Table Writes**: Code in `app/domains/attendance` must never write to tables owned by `finance` or `academics`.
2. **Explicit Python Domain Service Interfaces**: Domains expose public service methods (e.g. `AcademicsService.verify_course_enrollment(student_id, course_id)`).
3. **Idempotent Ingestion**: Event-based actions (e.g. biometric attendance records or payment webhook updates) must be strictly idempotent using unique database constraints.

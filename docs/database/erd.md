# CampusOS — Entity Relationship Diagrams (ERD)

This document contains visual Entity Relationship Diagrams for CampusOS using standard Mermaid syntax.

---

## 1. High-Level System Architecture ERD

```mermaid
erDiagram
    INSTITUTION ||--o{ CAMPUS : operates
    INSTITUTION ||--o{ DEPARTMENT : owns
    DEPARTMENT ||--o{ PROGRAM : offers
    PROGRAM ||--o{ BATCH : enrolls
    BATCH ||--o{ STUDENT : contains
    USER ||--o{ USER_ROLE : assigned
    USER ||--o| STUDENT : profile
    USER ||--o| FACULTY : profile

    STUDENT ||--o{ SEMESTER_ENROLLMENT : progresses
    STUDENT ||--o{ COURSE_ENROLLMENT : registers
    STUDENT ||--o{ ATTENDANCE_RECORD : attends
    STUDENT ||--o{ ASSESSMENT_MARK : scores
    STUDENT ||--o{ EXAM_RESULT : attains
    STUDENT ||--o{ INVOICE : billed
    STUDENT ||--o{ PLACEMENT_APPLICATION : applies
    STUDENT ||--o{ HOSTEL_ALLOCATION : resides
    STUDENT ||--o{ TRANSPORT_ALLOCATION : travels
```

---

## 2. Core & People Domain ERD

```mermaid
erDiagram
    core_institutions ||--o{ core_campuses : contains
    core_institutions ||--o{ core_departments : organizes
    core_campuses ||--o{ core_departments : locates
    core_departments ||--o{ core_programs : manages
    core_programs ||--o{ core_batches : cohorts
    core_regulations ||--o{ core_batches : governs
    core_academic_years ||--o{ core_semesters : divides
    core_programs ||--o{ core_sections : partitions
    core_semesters ||--o{ core_sections : schedules
    core_batches ||--o{ core_sections : assigns

    people_users ||--o{ people_user_roles : assigned
    people_roles ||--o{ people_user_roles : grants
    people_roles ||--o{ people_role_permissions : bundles
    people_permissions ||--o{ people_role_permissions : contains

    people_users ||--o| people_students : student_profile
    people_users ||--o| people_faculty : faculty_profile
    people_users ||--o| people_staff : staff_profile
    people_users ||--o| people_guardians : guardian_profile

    core_programs ||--o{ people_students : enrolled_in
    core_batches ||--o{ people_students : belongs_to
    people_students ||--o{ people_student_guardians : has
    people_guardians ||--o{ people_student_guardians : sponsors

    people_students ||--o{ people_student_semester_enrollments : history
    core_semesters ||--o{ people_student_semester_enrollments : term
    core_sections ||--o{ people_student_semester_enrollments : placement
    people_students ||--o{ people_student_status_history : lifecycle_audits
```

---

## 3. Academics Domain ERD

```mermaid
erDiagram
    core_departments ||--o{ academics_subjects : defines
    core_programs ||--o{ academics_curriculums : structured_for
    core_regulations ||--o{ academics_curriculums : regulated_by
    academics_curriculums ||--o{ academics_curriculum_subjects : specifies
    academics_subjects ||--o{ academics_curriculum_subjects : included_in

    academics_subjects ||--o{ academics_course_offerings : delivered_as
    core_academic_years ||--o{ academics_course_offerings : during_year
    core_semesters ||--o{ academics_course_offerings : during_term
    core_sections ||--o{ academics_course_offerings : for_section

    academics_course_offerings ||--o{ academics_course_faculty : taught_by
    people_faculty ||--o{ academics_course_faculty : teaches

    academics_course_offerings ||--o{ academics_course_enrollments : student_list
    people_students ||--o{ academics_course_enrollments : attends

    academics_course_offerings ||--o{ academics_timetable_slots : scheduled_at
    people_faculty ||--o{ academics_timetable_slots : instructs
```

---

## 4. Attendance Domain ERD

```mermaid
erDiagram
    academics_course_offerings ||--o{ attendance_sessions : conducts
    core_sections ||--o{ attendance_sessions : class_group
    people_faculty ||--o{ attendance_sessions : marked_by
    academics_timetable_slots ||--o{ attendance_sessions : sourced_from

    attendance_sessions ||--o{ attendance_records : logs
    people_students ||--o{ attendance_records : for_student

    attendance_records ||--o| attendance_corrections : disputed
    people_users ||--o{ attendance_corrections : requested_by
    people_users ||--o{ attendance_corrections : reviewed_by

    people_students ||--o{ attendance_leave_requests : submits
    people_users ||--o{ attendance_leave_requests : approves
```

---

## 5. Examination & Grading ERD

```mermaid
erDiagram
    examination_grade_scales ||--o{ examination_grade_items : defines_bands
    core_academic_years ||--o{ examination_terms : exam_period
    core_semesters ||--o{ examination_terms : applies_to

    academics_course_offerings ||--o{ examination_assessments : evaluates
    examination_terms ||--o{ examination_assessments : scheduled_in

    examination_assessments ||--o{ examination_student_marks : scores
    people_students ||--o{ examination_student_marks : earned_by
    people_faculty ||--o{ examination_student_marks : evaluated_by

    examination_terms ||--o{ examination_results : finalized_in
    academics_course_offerings ||--o{ examination_results : course_result
    people_students ||--o{ examination_results : student_grade
    people_users ||--o{ examination_results : published_by
```

---

## 6. Finance & Billing Domain ERD

```mermaid
erDiagram
    finance_fee_categories ||--o{ finance_fee_items : categorized_as
    core_programs ||--o{ finance_fee_structures : mapped_for
    core_academic_years ||--o{ finance_fee_structures : valid_during
    finance_fee_structures ||--o{ finance_fee_items : composed_of

    people_students ||--o{ finance_concessions : granted_to
    finance_fee_categories ||--o{ finance_concessions : concession_on

    people_students ||--o{ finance_invoices : billed_to
    core_academic_years ||--o{ finance_invoices : period_year
    finance_invoices ||--o{ finance_invoice_items : itemized_as
    finance_fee_categories ||--o{ finance_invoice_items : head

    people_students ||--o{ finance_payments : paid_by
    finance_payments ||--o{ finance_allocations : allocated_via
    finance_invoices ||--o{ finance_allocations : credited_to

    finance_payments ||--o| finance_receipts : legal_proof
    finance_invoices ||--o{ finance_adjustments : credited_debited
    finance_payments ||--o{ finance_refunds : refunded_from
```

---

## 7. Placement Domain ERD

```mermaid
erDiagram
    placement_companies ||--o{ placement_contacts : employs
    placement_companies ||--o{ placement_drives : sponsors
    core_academic_years ||--o{ placement_drives : year

    placement_drives ||--o{ placement_positions : opens
    placement_positions ||--o{ placement_eligibility_rules : guarded_by

    placement_positions ||--o{ placement_applications : receives
    people_students ||--o{ placement_applications : submits

    placement_positions ||--o{ placement_interview_rounds : stages
    placement_interview_rounds ||--o{ placement_interview_results : outcomes
    placement_applications ||--o{ placement_interview_results : candidate

    placement_applications ||--o| placement_offers : awarded
    people_students ||--o{ placement_offers : received_by
```

---

## 8. Campus & Infrastructure ERD

```mermaid
erDiagram
    core_campuses ||--o{ infrastructure_hostels : campus_site
    infrastructure_hostels ||--o{ infrastructure_hostel_blocks : has_blocks
    infrastructure_hostel_blocks ||--o{ infrastructure_hostel_floors : has_floors
    infrastructure_hostel_floors ||--o{ infrastructure_hostel_rooms : has_rooms
    infrastructure_hostel_rooms ||--o{ infrastructure_hostel_beds : has_beds

    infrastructure_hostel_beds ||--o{ infrastructure_hostel_allocations : reserved_by
    people_students ||--o{ infrastructure_hostel_allocations : resides_in

    people_students ||--o{ infrastructure_hostel_passes : requests
    infrastructure_hostel_rooms ||--o{ infrastructure_hostel_complaints : logged_for
    people_students ||--o{ infrastructure_hostel_complaints : filed_by

    core_campuses ||--o{ infrastructure_routes : service_route
    infrastructure_vehicles ||--o{ infrastructure_routes : fleet_vehicle
    infrastructure_drivers ||--o{ infrastructure_routes : driver
    infrastructure_routes ||--o{ infrastructure_stops : route_stops

    infrastructure_stops ||--o{ infrastructure_transport_allocations : pickup_point
    people_students ||--o{ infrastructure_transport_allocations : bus_pass

    campus_clubs ||--o{ campus_club_memberships : roster
    people_students ||--o{ campus_club_memberships : member
    campus_clubs ||--o{ campus_events : organizes
    campus_events ||--o{ campus_event_registrations : attendees
    people_students ||--o{ campus_event_registrations : attendee
```

---

## 9. Documents & Audit ERD

```mermaid
erDiagram
    documents_categories ||--o{ documents_storage_records : categorized_as
    people_users ||--o{ documents_storage_records : uploaded_by

    documents_storage_records ||--o{ documents_student_records : file_meta
    people_students ||--o{ documents_student_records : student_doc
    people_users ||--o{ documents_student_records : verified_by

    documents_certificate_templates ||--o{ documents_issued_certificates : layout
    people_students ||--o{ documents_issued_certificates : awarded_to
    documents_storage_records ||--o| documents_issued_certificates : rendered_pdf

    core_institutions ||--o{ intelligence_audit_logs : tenant_log
    people_users ||--o{ intelligence_audit_logs : actor
```

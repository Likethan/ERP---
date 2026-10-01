# CampusOS — Database Architecture Master Guide

> **"One Campus. One System. One Source of Truth."**

This directory contains the production-grade relational database architecture specifications, domain models, entity catalogs, multi-tenancy models, and indexing strategies for CampusOS.

---

## 1. Architectural Tenets

1. **Relational Foundation**: CampusOS uses **PostgreSQL 16+** as its primary system of record.
2. **Modular Monolith Data Boundaries**: Every table belongs to one of 11 discrete business domains. Direct cross-domain foreign keys reference primary keys (`UUIDv4`) of canonical entities (e.g. `student_id -> people_students.id`), but cross-domain writes are strictly mediated by domain service boundaries.
3. **Multi-Tenancy Readiness**: Every tenant-scoped operational table includes `tenant_id: UUID NOT NULL REFERENCES core_institutions(id)`. Uniqueness is composite: `UNIQUE(tenant_id, business_identifier)`.
4. **Historical Immutability**: Critical operational events (financial payments, published examination results, attendance records, semester enrollments) preserve non-destructive history.
5. **Universal Timestamp Standards**: All timestamps are stored with timezone in UTC (`TIMESTAMPTZ NOT NULL DEFAULT NOW()`).

---

## 2. Standard Column & Table Naming Conventions

- **Table Names**: Lowercase snake_case prefixed by the domain identifier:
  - `core_*`: `core_institutions`, `core_campuses`, `core_departments`, `core_programs`, `core_regulations`, `core_batches`, `core_academic_years`, `core_semesters`, `core_sections`
  - `people_*`: `people_users`, `people_roles`, `people_permissions`, `people_role_permissions`, `people_user_roles`, `people_students`, `people_faculty`, `people_staff`, `people_guardians`, `people_student_guardians`, `people_student_semester_enrollments`, `people_student_status_history`
  - `academics_*`: `academics_subjects`, `academics_curriculums`, `academics_curriculum_subjects`, `academics_course_offerings`, `academics_course_faculty`, `academics_course_enrollments`, `academics_timetable_slots`
  - `attendance_*`: `attendance_policies`, `attendance_sessions`, `attendance_records`, `attendance_corrections`, `attendance_leave_requests`
  - `examination_*`: `examination_grade_scales`, `examination_grade_items`, `examination_terms`, `examination_assessments`, `examination_schedules`, `examination_student_marks`, `examination_results`, `examination_corrections`
  - `finance_*`: `finance_fee_categories`, `finance_fee_structures`, `finance_fee_items`, `finance_concessions`, `finance_invoices`, `finance_invoice_items`, `finance_payments`, `finance_allocations`, `finance_receipts`, `finance_refunds`, `finance_adjustments`
  - `placement_*`: `placement_companies`, `placement_contacts`, `placement_drives`, `placement_positions`, `placement_eligibility_rules`, `placement_applications`, `placement_interview_rounds`, `placement_interview_results`, `placement_offers`
  - `campus_*`: `campus_clubs`, `campus_club_memberships`, `campus_events`, `campus_event_registrations`, `campus_announcements`, `campus_notifications`
  - `infrastructure_*`: `infrastructure_hostels`, `infrastructure_hostel_blocks`, `infrastructure_hostel_floors`, `infrastructure_hostel_rooms`, `infrastructure_hostel_beds`, `infrastructure_hostel_allocations`, `infrastructure_hostel_passes`, `infrastructure_hostel_complaints`, `infrastructure_vehicles`, `infrastructure_drivers`, `infrastructure_routes`, `infrastructure_stops`, `infrastructure_transport_allocations`
  - `documents_*`: `documents_categories`, `documents_storage_records`, `documents_student_records`, `documents_faculty_records`, `documents_certificate_templates`, `documents_issued_certificates`
  - `intelligence_*`: `intelligence_audit_logs`, `intelligence_analytics_snapshots`, `intelligence_ai_tool_registry`
- **Primary Keys**: Always `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`.
- **Foreign Keys**: Named as `<referenced_entity_singular>_id` (e.g., `student_id`, `department_id`, `invoice_id`).
- **Boolean Flags**: Prefixed with `is_` or `has_` (e.g., `is_active`, `is_mandatory`, `is_verified`, `has_backlogs`).

---

## 3. Documentation Index

- [Domain Model Specification](./domain-model.md): Deep-dive into each domain's entities and lifecycles.
- [Entity Catalog & Schema Details](./entity-catalog.md): Complete field-by-field definitions, data types, constraints, and defaults.
- [Multi-Tenancy & Row-Level Security](./multi-tenancy.md): Tenancy isolation, RLS policies, and SQLAlchemy integration.
- [Indexing Strategy](./indexing-strategy.md): B-Tree indexes, composite keys, and query performance profiles.
- [Data Lifecycle & State Machines](./data-lifecycle.md): Operational lifecycles, state machine diagrams, and soft-delete boundaries.
- [Audit & Tamper-Resistance Model](./audit-model.md): Comprehensive logging of all critical business mutations.
- [Entity Relationship Diagrams (ERDs)](./erd.md): Complete Mermaid visual diagrams for system and domain models.

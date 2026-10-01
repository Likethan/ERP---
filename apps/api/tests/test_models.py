"""Automated verification suite for CampusOS domain models and database architecture."""

import app.models  # noqa: F401 - Loads all domain entities into Base.metadata
from app.models.base import Base, TenantScopedModel


def test_domain_models_registered_in_metadata() -> None:
    """Verify that all core domain models register cleanly in SQLAlchemy Base.metadata."""
    table_names = set(Base.metadata.tables.keys())

    expected_tables = {
        # Core
        "core_institutions",
        "core_campuses",
        "core_departments",
        "core_programs",
        "core_regulations",
        "core_batches",
        "core_academic_years",
        "core_semesters",
        "core_sections",
        # People
        "people_users",
        "people_user_sessions",
        "people_password_reset_tokens",
        "people_roles",
        "people_permissions",
        "people_role_permissions",
        "people_user_roles",
        "people_students",
        "people_faculty",
        "people_staff",
        "people_guardians",
        "people_student_guardians",
        "people_student_semester_enrollments",
        "people_student_status_history",
        # Academics
        "academics_subjects",
        "academics_curriculums",
        "academics_curriculum_subjects",
        "academics_course_offerings",
        "academics_course_faculty",
        "academics_course_enrollments",
        "academics_timetable_slots",
        # Attendance
        "attendance_policies",
        "attendance_sessions",
        "attendance_records",
        "attendance_corrections",
        "attendance_leave_requests",
        # Examination
        "examination_grade_scales",
        "examination_grade_items",
        "examination_terms",
        "examination_assessments",
        "examination_schedules",
        "examination_student_marks",
        "examination_results",
        "examination_corrections",
        # Finance
        "finance_fee_categories",
        "finance_fee_structures",
        "finance_fee_items",
        "finance_fee_assignments",
        "finance_concessions",
        "finance_invoices",
        "finance_invoice_items",
        "finance_payments",
        "finance_allocations",
        "finance_receipts",
        "finance_refunds",
        "finance_adjustments",
        # Placement
        "placement_companies",
        "placement_contacts",
        "placement_drives",
        "placement_positions",
        "placement_eligibility_rules",
        "placement_applications",
        "placement_interview_rounds",
        "placement_interview_evaluations",
        "placement_offers",
        # Campus
        "campus_event_categories",
        "campus_event_venues",
        "campus_events",
        "campus_event_registrations",
        "campus_event_attendances",
        "campus_clubs",
        "campus_club_memberships",
        "campus_announcements",
        "campus_announcement_audiences",
        "campus_notifications",
        "campus_notification_deliveries",
        "campus_notification_preferences",
        # Infrastructure
        "infrastructure_hostels",
        "infrastructure_hostel_blocks",
        "infrastructure_hostel_floors",
        "infrastructure_hostel_rooms",
        "infrastructure_hostel_beds",
        "infrastructure_hostel_allocations",
        "infrastructure_hostel_passes",
        "infrastructure_hostel_complaints",
        "infrastructure_vehicles",
        "infrastructure_drivers",
        "infrastructure_routes",
        "infrastructure_stops",
        "infrastructure_transport_allocations",
        # Documents
        "documents_categories",
        "documents_storage_records",
        "documents_student_records",
        "documents_faculty_records",
        "documents_certificate_templates",
        "documents_issued_certificates",
        # Audit
        "intelligence_audit_logs",
    }

    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"
    assert len(table_names) >= len(expected_tables)


def test_tenant_scoped_models_have_tenant_id() -> None:
    """Verify that all tenant-scoped entities include a tenant_id column."""
    for table_name, table in Base.metadata.tables.items():
        if table_name.startswith(("people_permissions", "core_institutions")):
            continue
        for mapper in Base.registry.mappers:
            if mapper.persist_selectable.name == table_name:
                if issubclass(mapper.class_, TenantScopedModel):
                    assert "tenant_id" in table.c, f"{table_name} missing tenant_id column"


def test_foreign_keys_target_valid_tables() -> None:
    """Verify that every foreign key defined across all tables points to an existing table."""
    table_names = set(Base.metadata.tables.keys())
    for table_name, table in Base.metadata.tables.items():
        for fk in table.foreign_keys:
            target_table = fk.column.table.name
            msg = f"Foreign key in {table_name}.{fk.parent.name} targets unknown {target_table}"
            assert target_table in table_names, msg

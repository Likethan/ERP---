"""Enterprise Academic Timetable, Resource Scheduling & Conflict Resolution Engine (Step 49).

Revision ID: 034_enterprise_timetable_resource_scheduling
Revises: 033_enterprise_admissions_enrollment_onboarding
Create Date: 2026-10-19 21:00:00.000000

Creates normalized tables for:
- timetable_schedules: Master timetable container bound to academic year, semester, and scope
- timetable_versions: Stage-managed and publication-controlled schedule versions
- timetable_sessions: Individual scheduled teaching session allocations with co-faculty and buffers
- timetable_teaching_periods: Institutional period, working hour, and break configuration
- timetable_calendar_periods: Institutional calendar milestones, holidays, and exam windows
- timetable_schedule_exceptions: Temporary date-specific schedule overrides and timetable day swaps
- timetable_faculty_availability: Faculty teaching availability windows and workload limits
- timetable_resource_reservations: Physical room or laboratory exclusive reservation ledger
- timetable_maintenance_windows: Facility maintenance or downtime windows
- timetable_generation_jobs: Asynchronous constraint-based timetable generation job records
- timetable_conflicts: Detected scheduling collisions, rule violations, and capacity breaches
- timetable_change_requests: Controlled schedule change requests with impact analysis and approval
- timetable_publications: Audit ledger of timetable publications, target audiences, and sync status
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "034_enterprise_timetable_resource_scheduling"
down_revision = "033_enterprise_admissions_enrollment_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Master Timetable Schedules
    op.create_table(
        "timetable_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "semester_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_semesters.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_sections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_timetable_schedules_tenant_code"),
    )
    op.create_index(
        "ix_timetable_sched_tenant_sem",
        "timetable_schedules",
        ["tenant_id", "academic_year_id", "semester_id"],
    )
    op.create_index(
        "ix_timetable_sched_tenant_sec",
        "timetable_schedules",
        ["tenant_id", "section_id"],
    )

    # 2. Timetable Versions
    op.create_table(
        "timetable_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "schedule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_schedules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("effective_start_date", sa.Date(), nullable=True),
        sa.Column("effective_end_date", sa.Date(), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "published_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("schedule_id", "version_number", name="uq_timetable_versions_sched_ver"),
    )
    op.create_index(
        "ix_timetable_ver_tenant_status",
        "timetable_versions",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_timetable_ver_schedule_status",
        "timetable_versions",
        ["schedule_id", "status"],
    )

    # 3. Teaching Period Configurations
    op.create_table(
        "timetable_teaching_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("teaching_days", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("day_start_time", sa.Time(), nullable=False),
        sa.Column("day_end_time", sa.Time(), nullable=False),
        sa.Column("period_duration_minutes", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("transition_buffer_minutes", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("lunch_start_time", sa.Time(), nullable=True),
        sa.Column("lunch_end_time", sa.Time(), nullable=True),
        sa.Column("breaks_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_periods_tenant_campus",
        "timetable_teaching_periods",
        ["tenant_id", "campus_id"],
    )

    # 4. Academic Calendar Periods & Holidays
    op.create_table(
        "timetable_calendar_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "semester_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_semesters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("calendar_type", sa.String(32), nullable=False, server_default="HOLIDAY"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("affects_teaching", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_cal_tenant_dates",
        "timetable_calendar_periods",
        ["tenant_id", "start_date", "end_date"],
    )

    # 5. Schedule Exceptions & Overrides
    op.create_table(
        "timetable_schedule_exceptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "schedule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_schedules.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("exception_date", sa.Date(), nullable=False),
        sa.Column("exception_type", sa.String(32), nullable=False, server_default="HOLIDAY_CLOSURE"),
        sa.Column("substitute_day_of_week", sa.Integer(), nullable=True),
        sa.Column("affected_room_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("affected_section_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_exceptions_tenant_date",
        "timetable_schedule_exceptions",
        ["tenant_id", "exception_date"],
    )

    # 6. Faculty Availability & Workload Policies
    op.create_table(
        "timetable_faculty_availability",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "faculty_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_faculty.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "semester_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_semesters.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("available_start_time", sa.Time(), nullable=False),
        sa.Column("available_end_time", sa.Time(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("max_hours_per_day", sa.Numeric(4, 2), nullable=False, server_default="4.00"),
        sa.Column("max_hours_per_week", sa.Numeric(4, 2), nullable=False, server_default="18.00"),
        sa.Column("preferred_session_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_fac_avail_tenant_fac",
        "timetable_faculty_availability",
        ["tenant_id", "faculty_id", "day_of_week"],
    )

    # 7. Timetable Sessions
    op.create_table(
        "timetable_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_offering_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_course_offerings.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_sections.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "subject_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_subjects.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "faculty_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_faculty.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("co_faculty_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "room_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_rooms.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column(
            "time_slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_time_slots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("session_type", sa.String(32), nullable=False, server_default="LECTURE"),
        sa.Column("session_group", sa.String(64), nullable=True),
        sa.Column("recurrence_pattern", sa.String(32), nullable=False, server_default="WEEKLY"),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column(
            "replacement_room_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_rooms.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "substitute_faculty_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_faculty.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("transition_buffer_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "canonical_slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_timetable_slots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_sessions_tenant_day",
        "timetable_sessions",
        ["tenant_id", "day_of_week"],
    )
    op.create_index(
        "ix_tt_sessions_tenant_room",
        "timetable_sessions",
        ["tenant_id", "room_id", "day_of_week"],
    )
    op.create_index(
        "ix_tt_sessions_tenant_fac",
        "timetable_sessions",
        ["tenant_id", "faculty_id", "day_of_week"],
    )
    op.create_index(
        "ix_tt_sessions_tenant_sec",
        "timetable_sessions",
        ["tenant_id", "section_id", "day_of_week"],
    )

    # 8. Resource Reservations
    op.create_table(
        "timetable_resource_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "room_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reservation_type", sa.String(32), nullable=False, server_default="TIMETABLE"),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="CONFIRMED"),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_exclusive", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_res_tenant_room_dates",
        "timetable_resource_reservations",
        ["tenant_id", "room_id", "start_datetime", "end_datetime"],
    )
    op.create_index(
        "ix_tt_res_tenant_status",
        "timetable_resource_reservations",
        ["tenant_id", "status"],
    )

    # 9. Maintenance Windows
    op.create_table(
        "timetable_maintenance_windows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "room_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_maint_tenant_room",
        "timetable_maintenance_windows",
        ["tenant_id", "room_id", "start_time", "end_time"],
    )

    # 10. Generation Jobs
    op.create_table(
        "timetable_generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "semester_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_semesters.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_sections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("job_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("config_parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("total_sessions_to_schedule", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scheduled_sessions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unscheduled_sessions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "candidate_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("result_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_gen_tenant_status",
        "timetable_generation_jobs",
        ["tenant_id", "job_status"],
    )

    # 11. Timetable Conflicts
    op.create_table(
        "timetable_conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("conflict_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="CRITICAL"),
        sa.Column("affected_date_or_day", sa.String(32), nullable=False),
        sa.Column("time_window", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rule_violated", sa.String(128), nullable=False),
        sa.Column(
            "session_id_1",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "session_id_2",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "faculty_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_faculty.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "room_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_rooms.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_sections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("remediation_suggestions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_conflicts_tenant_ver",
        "timetable_conflicts",
        ["tenant_id", "version_id"],
    )
    op.create_index(
        "ix_tt_conflicts_tenant_sev",
        "timetable_conflicts",
        ["tenant_id", "severity"],
    )

    # 12. Change Requests
    op.create_table(
        "timetable_change_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("change_type", sa.String(32), nullable=False, server_default="RESCHEDULE"),
        sa.Column("proposed_day_of_week", sa.Integer(), nullable=True),
        sa.Column("proposed_start_time", sa.Time(), nullable=True),
        sa.Column("proposed_end_time", sa.Time(), nullable=True),
        sa.Column(
            "proposed_room_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academics_rooms.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "proposed_faculty_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_faculty.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("is_emergency", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("impact_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reviewed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_change_tenant_ver",
        "timetable_change_requests",
        ["tenant_id", "version_id"],
    )
    op.create_index(
        "ix_tt_change_tenant_status",
        "timetable_change_requests",
        ["tenant_id", "status"],
    )

    # 13. Publications
    op.create_table(
        "timetable_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("publication_type", sa.String(32), nullable=False, server_default="INITIAL"),
        sa.Column("published_to_students", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("published_to_faculty", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("calendar_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "published_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_tt_pub_tenant_ver",
        "timetable_publications",
        ["tenant_id", "version_id"],
    )


def downgrade() -> None:
    op.drop_table("timetable_publications")
    op.drop_table("timetable_change_requests")
    op.drop_table("timetable_conflicts")
    op.drop_table("timetable_generation_jobs")
    op.drop_table("timetable_maintenance_windows")
    op.drop_table("timetable_resource_reservations")
    op.drop_table("timetable_sessions")
    op.drop_table("timetable_faculty_availability")
    op.drop_table("timetable_schedule_exceptions")
    op.drop_table("timetable_calendar_periods")
    op.drop_table("timetable_teaching_periods")
    op.drop_table("timetable_versions")
    op.drop_table("timetable_schedules")

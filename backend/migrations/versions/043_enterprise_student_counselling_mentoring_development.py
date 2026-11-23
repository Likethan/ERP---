"""Enterprise Student Counselling, Mentoring & Personal Development Management (Step 59).

Revision ID: 043_enterprise_student_counselling_mentoring_development
Revises: 042_enterprise_student_affairs_disciplinary_grievance
Create Date: 2026-10-25 21:00:00.000000

Creates normalized tables and schema objects for:
- ss_mentor_assignments: Faculty mentor assignments, student links, workload limits, reassignment history
- ss_mentoring_sessions: Non-clinical mentoring sessions, summaries, action items, attendance
- ss_session_attendees: Student session participation, feedback, and personal reflections
- ss_counselling_appointments: Scheduling, intake categories, mode/venue, statuses
- ss_confidential_counselling_records: Strictly confidential clinical notes isolated from mentors/admins
- ss_student_development_plans: Individual student development plans (IDP), reviews, aspirations
- ss_development_goals: Categorized goals (academic, professional, leadership), milestones
- ss_development_action_items: Concrete tasks, deadlines, completion statuses
- ss_support_referrals: Inter-service referrals across advising, careers, counselling, accessibility
- ss_support_follow_ups: Coordinated follow-up deadlines and reviews
- ss_support_audit_logs: Immutable access audits for sensitive counselling and referral records
- ss_policy_configs: Institutional limits, advance booking windows, consent requirements
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "043_enterprise_student_counselling_mentoring_development"
down_revision = "042_enterprise_student_affairs_disciplinary_grievance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Mentor Assignments
    op.create_table(
        "ss_mentor_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mentor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
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
        sa.Column("academic_year", sa.String(32), nullable=False),
        sa.Column("assignment_type", sa.String(32), nullable=False, server_default="MANUAL"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("assigned_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "reassigned_from_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ss_mentor_assignments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reassignment_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ss_mentor_assign_student", "ss_mentor_assignments", ["tenant_id", "student_id", "status"])
    op.create_index("idx_ss_mentor_assign_mentor", "ss_mentor_assignments", ["tenant_id", "mentor_user_id", "status"])

    # 2. Mentoring Sessions
    op.create_table(
        "ss_mentoring_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ss_mentor_assignments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "mentor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("session_title", sa.String(200), nullable=False),
        sa.Column("session_type", sa.String(32), nullable=False, server_default="ONE_ON_ONE"),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.String(8), nullable=False),
        sa.Column("end_time", sa.String(8), nullable=False),
        sa.Column("location_or_link", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("action_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ss_session_mentor_date", "ss_mentoring_sessions", ["tenant_id", "mentor_user_id", "session_date"])
    op.create_index("idx_ss_session_status", "ss_mentoring_sessions", ["tenant_id", "status"])

    # 3. Session Attendees
    op.create_table(
        "ss_session_attendees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ss_mentoring_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attendance_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("student_feedback", sa.Text(), nullable=True),
        sa.Column("student_reflection", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("session_id", "student_id", name="uq_session_student_attendee"),
    )
    op.create_index("idx_ss_attendee_student", "ss_session_attendees", ["tenant_id", "student_id", "attendance_status"])

    # 4. Counselling Appointments
    op.create_table(
        "ss_counselling_appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "counsellor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("category", sa.String(64), nullable=False, server_default="GENERAL_WELLBEING"),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.String(8), nullable=False),
        sa.Column("end_time", sa.String(8), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="45"),
        sa.Column("mode", sa.String(32), nullable=False, server_default="IN_PERSON"),
        sa.Column("venue_or_link", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="REQUESTED"),
        sa.Column("request_reason", sa.String(255), nullable=False),
        sa.Column(
            "booked_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("is_confidential", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ss_counsel_counsellor_date", "ss_counselling_appointments", ["tenant_id", "counsellor_user_id", "appointment_date", "status"])
    op.create_index("idx_ss_counsel_student_date", "ss_counselling_appointments", ["tenant_id", "student_id", "appointment_date"])

    # 5. Confidential Counselling Records
    op.create_table(
        "ss_confidential_counselling_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ss_counselling_appointments.id", ondelete="SET NULL"),
            nullable=True,
            unique=True,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "counsellor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("session_notes_restricted", sa.Text(), nullable=False),
        sa.Column("intervention_type", sa.String(64), nullable=False, server_default="COUNSELLING_DIALOGUE"),
        sa.Column("clinical_observations", sa.Text(), nullable=True),
        sa.Column("follow_up_recommended", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("follow_up_target_date", sa.Date(), nullable=True),
        sa.Column("consent_confirmed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ss_confidential_student", "ss_confidential_counselling_records", ["tenant_id", "student_id"])

    # 6. Student Development Plans (IDP)
    op.create_table(
        "ss_student_development_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mentor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("academic_year", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("overall_progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_frequency", sa.String(32), nullable=False, server_default="SEMESTER"),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("strengths_summary", sa.Text(), nullable=True),
        sa.Column("areas_for_growth", sa.Text(), nullable=True),
        sa.Column("career_aspirations", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ss_devplan_student_year", "ss_student_development_plans", ["tenant_id", "student_id", "academic_year"])
    op.create_index("idx_ss_devplan_status", "ss_student_development_plans", ["tenant_id", "status"])

    # 7. Development Goals
    op.create_table(
        "ss_development_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ss_student_development_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(32), nullable=False, server_default="ACADEMIC"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("measurable_milestones", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("mentor_notes", sa.Text(), nullable=True),
        sa.Column("student_reflection", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ss_goal_plan", "ss_development_goals", ["tenant_id", "plan_id", "status"])

    # 8. Development Action Items
    op.create_table(
        "ss_development_action_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "goal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ss_development_goals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("assigned_to_role", sa.String(32), nullable=False, server_default="STUDENT"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ss_action_goal", "ss_development_action_items", ["tenant_id", "goal_id", "status"])

    # 9. Support Referrals
    op.create_table(
        "ss_support_referrals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("referral_code", sa.String(64), nullable=False),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "referring_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("referring_role", sa.String(64), nullable=False),
        sa.Column("target_service", sa.String(64), nullable=False, server_default="ACADEMIC_ADVISING"),
        sa.Column("reason_category", sa.String(64), nullable=False, server_default="ACADEMIC_DIFFICULTY"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("summary_notes", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column(
            "assigned_staff_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("consent_obtained", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "referral_code", name="uq_ss_referral_tenant_code"),
    )
    op.create_index("idx_ss_referral_student", "ss_support_referrals", ["tenant_id", "student_id", "status"])
    op.create_index("idx_ss_referral_service", "ss_support_referrals", ["tenant_id", "target_service", "status"])

    # 10. Support Follow-ups
    op.create_table(
        "ss_support_follow_ups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ss_support_referrals.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ss_student_development_plans.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ss_counselling_appointments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "assigned_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ss_followup_assigned", "ss_support_follow_ups", ["tenant_id", "assigned_user_id", "status"])
    op.create_index("idx_ss_followup_due", "ss_support_follow_ups", ["tenant_id", "due_date", "status"])

    # 11. Support Audit Logs
    op.create_table(
        "ss_support_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_ss_audit_resource", "ss_support_audit_logs", ["tenant_id", "resource_type", "resource_id"])
    op.create_index("idx_ss_audit_user", "ss_support_audit_logs", ["tenant_id", "user_id", "created_at"])

    # 12. Policy Configs
    op.create_table(
        "ss_policy_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("max_mentees_per_mentor", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("allow_cross_department_mentors", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("appointment_advance_booking_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("appointment_cancellation_lead_hours", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("default_session_duration_minutes", sa.Integer(), nullable=False, server_default="45"),
        sa.Column("enable_confidential_counselling", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("require_student_consent_for_referral", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ss_policy_configs")
    op.drop_table("ss_support_audit_logs")
    op.drop_table("ss_support_follow_ups")
    op.drop_table("ss_support_referrals")
    op.drop_table("ss_development_action_items")
    op.drop_table("ss_development_goals")
    op.drop_table("ss_student_development_plans")
    op.drop_table("ss_confidential_counselling_records")
    op.drop_table("ss_counselling_appointments")
    op.drop_table("ss_session_attendees")
    op.drop_table("ss_mentoring_sessions")
    op.drop_table("ss_mentor_assignments")

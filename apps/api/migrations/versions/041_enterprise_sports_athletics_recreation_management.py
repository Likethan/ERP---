"""Enterprise Sports, Athletics, Recreation & Student Fitness Management (Step 57).

Revision ID: 041_enterprise_sports_athletics_recreation_management
Revises: 040_enterprise_transport_fleet_routes_mobility
Create Date: 2026-10-23 18:00:00.000000

Creates normalized tables and schema objects for:
- sports_departments: Sports departments, recreation centers, policies, operating hours
- sports_facilities: Courts, pitches, tracks, pools, gymnasiums, maintenance status
- sports_facility_bookings: Time-slot reservations, conflict prevention, maintenance blocks
- sports_participants: Student/staff sports profiles, health clearance, consent
- sports_teams: Varsity, intramural, and recreational teams, captains, coach links
- sports_team_memberships: Roster entries, jersey numbers, positions, join/leave history
- sports_coaching_assignments: Coach/trainer assignments to teams and sports
- sports_training_programs: Training camps, fitness academies, development programs
- sports_training_sessions: Recurring training sessions, drills, venue bookings
- sports_training_attendances: Participant check-in, presence recording, coach notes
- sports_competitions: Tournaments, leagues, meets, formats, scoring rules
- sports_competition_registrations: Team & individual registrations, seeding, fee links
- sports_match_fixtures: Bracket fixtures, stages, match schedules, venues
- sports_match_official_assignments: Referees, umpires, timekeepers, table officials
- sports_match_results: Score entry, set breakdowns, verification, audit trails
- sports_competition_standings: Computed league points, goal/point differentials, ranks
- sports_achievements: Medals, trophies, awards, institutional recognitions
- sports_equipment_assignments: Equipment checkouts, returns, condition tracking
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "041_enterprise_sports_athletics_recreation_management"
down_revision = "040_enterprise_transport_fleet_routes_mobility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Sports Departments
    op.create_table(
        "sports_departments",
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
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "head_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("operating_hours", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("policies", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sports_departments_tenant_code"),
    )
    op.create_index("idx_sports_dept_tenant", "sports_departments", ["tenant_id", "campus_id"])

    # 2. Sports Facilities
    op.create_table(
        "sports_facilities",
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
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("facility_type", sa.String(32), nullable=False, server_default="OUTDOOR_GROUND"),
        sa.Column("surface", sa.String(32), nullable=False, server_default="GRASS"),
        sa.Column("is_indoor", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("location_details", sa.String(255), nullable=True),
        sa.Column("operating_hours", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="AVAILABLE"),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("equipment_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("accessibility_features", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("maintenance_status", sa.String(32), nullable=False, server_default="GOOD"),
        sa.Column("last_inspected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sports_facilities_tenant_code"),
    )
    op.create_index("idx_sports_facilities_lookup", "sports_facilities", ["tenant_id", "status", "facility_type"])

    # 3. Sports Facility Bookings
    op.create_table(
        "sports_facility_bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "facility_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False, server_default="TRAINING"),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column(
            "booked_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("competition_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("training_program_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="CONFIRMED"),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("is_maintenance_block", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "idx_sports_fac_booking_slot",
        "sports_facility_bookings",
        ["tenant_id", "facility_id", "booking_date", "status"],
    )

    # 4. Sports Participants
    op.create_table(
        "sports_participants",
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
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("participant_code", sa.String(32), nullable=False),
        sa.Column("primary_sport", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("clearance_status", sa.String(32), nullable=False, server_default="CLEARED"),
        sa.Column("clearance_expiry", sa.Date(), nullable=True),
        sa.Column("consent_recorded", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("consent_recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("operational_restrictions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sports_history", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_sports_participants_tenant_user"),
        sa.UniqueConstraint("tenant_id", "participant_code", name="uq_sports_participants_tenant_code"),
    )
    op.create_index("idx_sports_participant_lookup", "sports_participants", ["tenant_id", "primary_sport", "status"])

    # 5. Sports Teams
    op.create_table(
        "sports_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("sport", sa.String(64), nullable=False),
        sa.Column("category", sa.String(32), nullable=False, server_default="VARSITY"),
        sa.Column("gender_category", sa.String(32), nullable=False, server_default="COED"),
        sa.Column(
            "captain_participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_participants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "head_coach_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("max_roster_size", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sports_teams_tenant_code"),
    )
    op.create_index("idx_sports_teams_lookup", "sports_teams", ["tenant_id", "sport", "category"])

    # 6. Team Memberships
    op.create_table(
        "sports_team_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_participants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(32), nullable=False, server_default="PLAYER"),
        sa.Column("jersey_number", sa.Integer(), nullable=True),
        sa.Column("position", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "team_id", "participant_id", name="uq_sports_team_memberships_unique"),
    )

    # 7. Coaching Assignments
    op.create_table(
        "sports_coaching_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(32), nullable=False, server_default="HEAD_COACH"),
        sa.Column("sport", sa.String(64), nullable=False),
        sa.Column("qualification", sa.String(128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("assigned_from", sa.Date(), nullable=False),
        sa.Column("assigned_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 8. Training Programs
    op.create_table(
        "sports_training_programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("program_type", sa.String(32), nullable=False, server_default="DEVELOPMENT"),
        sa.Column("sport", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "lead_coach_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "facility_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_facilities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("registration_deadline", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("fee_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sports_training_programs_tenant_code"),
    )

    # 9. Training Sessions
    op.create_table(
        "sports_training_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_training_programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "facility_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_facilities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 10. Training Attendances
    op.create_table(
        "sports_training_attendances",
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
            sa.ForeignKey("sports_training_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_participants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="PRESENT"),
        sa.Column("check_in_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "recorded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "session_id", "participant_id", name="uq_sports_train_att_unique"),
    )

    # 11. Sports Competitions
    op.create_table(
        "sports_competitions",
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
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("competition_type", sa.String(32), nullable=False, server_default="INTERNAL"),
        sa.Column("tournament_format", sa.String(32), nullable=False, server_default="SINGLE_ELIMINATION"),
        sa.Column("sport", sa.String(64), nullable=False),
        sa.Column("registration_type", sa.String(32), nullable=False, server_default="TEAM"),
        sa.Column("standing_rule", sa.String(32), nullable=False, server_default="STANDARD_POINTS"),
        sa.Column("points_for_win", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("points_for_draw", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("points_for_loss", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("registration_deadline", sa.Date(), nullable=False),
        sa.Column("max_participants", sa.Integer(), nullable=False, server_default="16"),
        sa.Column("fee_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("rules_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sports_competitions_tenant_code"),
    )
    op.create_index("idx_sports_comp_lookup", "sports_competitions", ["tenant_id", "sport", "status"])

    # 12. Competition Registrations
    op.create_table(
        "sports_competition_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "competition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_participants.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="REGISTERED"),
        sa.Column("seed_number", sa.Integer(), nullable=True),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("finance_invoices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("payment_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "competition_id",
            "team_id",
            "participant_id",
            name="uq_sports_comp_reg_unique",
        ),
    )

    # 13. Match Fixtures
    op.create_table(
        "sports_match_fixtures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "competition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("match_number", sa.String(32), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False, server_default="GROUP_STAGE"),
        sa.Column("round_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "home_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "away_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "home_participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_participants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "away_participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_participants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "facility_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_facilities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("match_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("postponement_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "competition_id", "match_number", name="uq_sports_match_fixtures_unique"),
    )
    op.create_index("idx_sports_fixtures_schedule", "sports_match_fixtures", ["tenant_id", "match_date", "facility_id"])

    # 14. Match Official Assignments
    op.create_table(
        "sports_match_official_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "fixture_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_match_fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(32), nullable=False, server_default="REFEREE"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ASSIGNED"),
        sa.Column("notes", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "fixture_id", "user_id", name="uq_sports_match_officials_unique"),
    )

    # 15. Match Results
    op.create_table(
        "sports_match_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "fixture_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_match_fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("home_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("away_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "winning_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "winning_participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_participants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_draw", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_forfeit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "forfeit_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "recorded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("audit_history", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "fixture_id", name="uq_sports_match_results_fixture"),
    )

    # 16. Competition Standings
    op.create_table(
        "sports_competition_standings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "competition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_participants.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("played", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("won", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("drawn", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points_for", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bonus_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "competition_id",
            "team_id",
            "participant_id",
            name="uq_sports_standings_unique",
        ),
    )
    op.create_index("idx_sports_standings_rank", "sports_competition_standings", ["tenant_id", "competition_id", "rank"])

    # 17. Sports Achievements
    op.create_table(
        "sports_achievements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "competition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_competitions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "participant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_participants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("achievement_type", sa.String(32), nullable=False, server_default="CHAMPION"),
        sa.Column("recognition_level", sa.String(32), nullable=False, server_default="INSTITUTIONAL"),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("citation", sa.Text(), nullable=True),
        sa.Column("awarded_date", sa.Date(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 18. Equipment Assignments
    op.create_table(
        "sports_equipment_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("equipment_name", sa.String(128), nullable=False),
        sa.Column("sport", sa.String(64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "assigned_to_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "facility_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_facilities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checkout_condition", sa.String(32), nullable=False, server_default="GOOD"),
        sa.Column("return_condition", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="CHECKED_OUT"),
        sa.Column("damage_notes", sa.Text(), nullable=True),
        sa.Column("replacement_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sports_equip_status", "sports_equipment_assignments", ["tenant_id", "status", "due_date"])


def downgrade() -> None:
    op.drop_table("sports_equipment_assignments")
    op.drop_table("sports_achievements")
    op.drop_table("sports_competition_standings")
    op.drop_table("sports_match_results")
    op.drop_table("sports_match_official_assignments")
    op.drop_table("sports_match_fixtures")
    op.drop_table("sports_competition_registrations")
    op.drop_table("sports_competitions")
    op.drop_table("sports_training_attendances")
    op.drop_table("sports_training_sessions")
    op.drop_table("sports_training_programs")
    op.drop_table("sports_coaching_assignments")
    op.drop_table("sports_team_memberships")
    op.drop_table("sports_teams")
    op.drop_table("sports_participants")
    op.drop_table("sports_facility_bookings")
    op.drop_table("sports_facilities")
    op.drop_table("sports_departments")

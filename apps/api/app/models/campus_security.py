"""Enterprise Campus Physical Security, Visitor Management, Gate Operations & Emergency Response Domain Models (Step 68).

Product: CampusOS — "One Campus. One System. One Source of Truth."

Entities:
- SecurityCheckpoint: Campus gates, barriers, turnstiles, and entry checkpoints.
- SecurityZone: Campus security zones, restricted areas, and clearance levels.
- VisitorProfile: Master visitor registry with masked ID documents.
- VisitorRequest: Visitor pre-registrations with host details and approval status.
- VisitorPass: Gate check-in and check-out sessions with cryptographically signed tokens.
- ContractorAccessProfile: Contractor profiles, work orders, and safety inductions.
- AccessGrant: Time-bounded logical access authorizations to campus zones.
- CampusSecurityIncident: Physical security incidents, status tracking, and escalations.
- EmergencyEvent: Institution-wide emergency coordination and checklists.
- EmergencyResponseTask: Emergency tasks and action items.
- SecurityPatrolPlan: Scheduled patrol routes and shifts.
- PatrolCheckpointRecord: Patrol checkpoint logs and supervisor reviews.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


class SecurityCheckpoint(TenantScopedModel):
    """Campus gate, perimeter entrance, barrier, or turnstile checkpoint."""

    __tablename__ = "campus_security_checkpoints"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_campus_sec_chkpt_tenant_code"),
        Index("ix_campus_sec_chkpt_tenant_active", "tenant_id", "is_active"),
        Index("ix_campus_sec_chkpt_type", "tenant_id", "checkpoint_type"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    checkpoint_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="MAIN_GATE"
    )  # MAIN_GATE, VEHICLE_BARRIER, PEDESTRIAN_TURNSTILE, SERVICE_GATE, EMERGENCY_EXIT
    location_description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_manned: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    operating_hours: Mapped[str] = mapped_column(String(64), nullable=False, default="24x7")
    guard_post_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)


class SecurityZone(TenantScopedModel):
    """Campus physical security zone or restricted area with clearance rules."""

    __tablename__ = "campus_security_zones"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_campus_sec_zone_tenant_code"),
        Index("ix_campus_sec_zone_tenant_clearance", "tenant_id", "clearance_level"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    clearance_level: Mapped[str] = mapped_column(
        String(32), nullable=False, default="CAMPUS_GENERAL"
    )  # PUBLIC, CAMPUS_GENERAL, FACULTY_STAFF_ONLY, RESTRICTED, HIGH_SECURITY
    building_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    floor_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requires_escort: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_occupancy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    emergency_assembly_point: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)


class VisitorProfile(TenantScopedModel):
    """Verified visitor directory record with masked identity reference."""

    __tablename__ = "campus_security_visitor_profiles"
    __table_args__ = (
        Index("ix_campus_sec_visitor_tenant_phone", "tenant_id", "phone"),
        Index("ix_campus_sec_visitor_tenant_email", "tenant_id", "email"),
    )

    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(128), nullable=True)
    id_document_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="OTHER"
    )  # AADHAAR, PASSPORT, DRIVING_LICENSE, VOTER_ID, EMPLOYER_ID, OTHER
    id_document_number_masked: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blacklist_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_visits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)


class VisitorRequest(TenantScopedModel):
    """Pre-registration or host invitation for campus entry."""

    __tablename__ = "campus_security_visitor_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_number", name="uq_campus_sec_visreq_number"),
        Index("ix_campus_sec_visreq_tenant_status", "tenant_id", "status"),
        Index("ix_campus_sec_visreq_arrival", "tenant_id", "expected_arrival_at"),
    )

    request_number: Mapped[str] = mapped_column(String(32), nullable=False)
    visitor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_visitor_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    visitor_name: Mapped[str] = mapped_column(String(128), nullable=False)
    visitor_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    visitor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    visitor_category: Mapped[str] = mapped_column(
        String(32), nullable=False, default="GUEST"
    )  # GUEST, PARENT, VENDOR, CONTRACTOR, INTERVIEW_CANDIDATE, EVENT_ATTENDEE, OFFICIAL, VIP

    host_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    host_name: Mapped[str] = mapped_column(String(128), nullable=False)
    host_department: Mapped[str | None] = mapped_column(String(128), nullable=True)

    visit_purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_zone_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_zones.id", ondelete="SET NULL"),
        nullable=True,
    )
    destination_description: Mapped[str] = mapped_column(String(255), nullable=False)

    expected_arrival_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING"
    )  # PENDING, APPROVED, REJECTED, CANCELLED
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    vehicle_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    has_vehicle: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accompanying_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)


class VisitorPass(TenantScopedModel):
    """Gate check-in pass and session with server-signed authentication token."""

    __tablename__ = "campus_security_visitor_passes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "pass_number", name="uq_campus_sec_vispass_number"),
        Index("ix_campus_sec_vispass_tenant_status", "tenant_id", "status"),
        Index("ix_campus_sec_vispass_signed_token", "signed_token"),
    )

    pass_number: Mapped[str] = mapped_column(String(32), nullable=False)
    request_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_visitor_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    visitor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_visitor_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    visitor_name: Mapped[str] = mapped_column(String(128), nullable=False)
    visitor_category: Mapped[str] = mapped_column(String(32), nullable=False)
    host_name: Mapped[str] = mapped_column(String(128), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)

    signed_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ISSUED"
    )  # ISSUED, CHECKED_IN, CHECKED_OUT, OVERDUE, REVOKED, EXPIRED

    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_in_checkpoint_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_checkpoints.id", ondelete="SET NULL"),
        nullable=True,
    )
    check_in_officer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_checkpoint_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_checkpoints.id", ondelete="SET NULL"),
        nullable=True,
    )
    check_out_officer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_overdue: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)


class ContractorAccessProfile(TenantScopedModel):
    """Recurring contractor credentials, work order permits, and safety inductions."""

    __tablename__ = "campus_security_contractor_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "contractor_code", name="uq_campus_sec_cont_code"),
        Index("ix_campus_sec_cont_tenant_status", "tenant_id", "status"),
    )

    contractor_code: Mapped[str] = mapped_column(String(32), nullable=False)
    organization_name: Mapped[str] = mapped_column(String(128), nullable=False)
    contractor_name: Mapped[str] = mapped_column(String(128), nullable=False)
    contractor_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    service_type: Mapped[str] = mapped_column(String(64), nullable=False)
    work_order_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    is_safety_induction_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    safety_induction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ACTIVE"
    )  # ACTIVE, PENDING_VERIFICATION, SUSPENDED, EXPIRED
    authorized_zone_ids: Mapped[list[str] | None] = mapped_column(JSONType, default=list)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    badge_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)


class AccessGrant(TenantScopedModel):
    """Time-bounded logical access authorization for campus zones or buildings."""

    __tablename__ = "campus_security_access_grants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "grant_number", name="uq_campus_sec_accgrant_number"),
        Index("ix_campus_sec_accgrant_tenant_zone", "tenant_id", "zone_id"),
        Index("ix_campus_sec_accgrant_grantee", "tenant_id", "grantee_id"),
    )

    grant_number: Mapped[str] = mapped_column(String(32), nullable=False)
    zone_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_zones.id", ondelete="CASCADE"),
        nullable=False,
    )
    grantee_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # STUDENT, STAFF, CONTRACTOR, VISITOR
    grantee_id: Mapped[str] = mapped_column(String(128), nullable=False)
    grantee_name: Mapped[str] = mapped_column(String(128), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_temporary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    grant_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ACTIVE"
    )  # ACTIVE, EXPIRED, REVOKED
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)


class CampusSecurityIncident(TenantScopedModel):
    """Physical campus security incident report, response lifecycle, and escalation."""

    __tablename__ = "campus_security_physical_incidents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "incident_number", name="uq_campus_sec_inc_number"),
        Index("ix_campus_sec_inc_tenant_status", "tenant_id", "status"),
        Index("ix_campus_sec_inc_tenant_severity", "tenant_id", "severity"),
    )

    incident_number: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # UNAUTHORIZED_ACCESS, PROPERTY_LOSS_DAMAGE, SAFETY_HAZARD, SUSPICIOUS_ACTIVITY, VEHICLE_GATE_INCIDENT, POLICY_VIOLATION, EMERGENCY_ASSISTANCE
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="MEDIUM"
    )  # LOW, MEDIUM, HIGH, CRITICAL
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="REPORTED"
    )  # REPORTED, ACKNOWLEDGED, ASSIGNED, IN_PROGRESS, ESCALATED, RESOLVED, CLOSED

    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reported_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reported_by_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reported_location: Mapped[str] = mapped_column(String(255), nullable=False)

    zone_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_zones.id", ondelete="SET NULL"),
        nullable=True,
    )
    checkpoint_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_checkpoints.id", ondelete="SET NULL"),
        nullable=True,
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_team: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    corrective_action_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_urls: Mapped[list[str] | None] = mapped_column(JSONType, default=list)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)


class EmergencyEvent(TenantScopedModel):
    """Institutional emergency situation workspace and coordination timeline."""

    __tablename__ = "campus_security_emergency_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "event_code", name="uq_campus_sec_emg_code"),
        Index("ix_campus_sec_emg_tenant_status", "tenant_id", "status"),
    )

    event_code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # FIRE_ALARM, SEVERE_WEATHER, MEDICAL_EMERGENCY, ACTIVE_THREAT, INFRASTRUCTURE_FAILURE, HAZMAT_LEAK, NATURAL_DISASTER
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="EMERGENCY"
    )  # ADVISORY, WARNING, EMERGENCY, CATASTROPHIC
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ACTIVE"
    )  # ACTIVE, CONTAINED, ALL_CLEAR, CLOSED

    affected_campus_areas: Mapped[str] = mapped_column(String(255), nullable=False)
    affected_zone_ids: Mapped[list[str] | None] = mapped_column(JSONType, default=list)

    coordinator_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    coordinator_name: Mapped[str] = mapped_column(String(128), nullable=False)
    emergency_broadcast_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    all_clear_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    after_action_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_services_contacted: Mapped[list[str] | None] = mapped_column(JSONType, default=list)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)

    tasks: Mapped[list["EmergencyResponseTask"]] = relationship(
        back_populates="emergency_event", cascade="all, delete-orphan", lazy="selectin"
    )


class EmergencyResponseTask(TenantScopedModel):
    """Specific response action task or checklist item during an active emergency."""

    __tablename__ = "campus_security_emergency_tasks"
    __table_args__ = (
        Index("ix_campus_sec_emgtask_event", "tenant_id", "event_id"),
        Index("ix_campus_sec_emgtask_status", "tenant_id", "status"),
    )

    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_emergency_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, default="HIGH"
    )  # LOW, MEDIUM, HIGH, URGENT
    assigned_to_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING"
    )  # PENDING, IN_PROGRESS, COMPLETED, BLOCKED
    action_checklist: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, default=list)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    emergency_event: Mapped["EmergencyEvent"] = relationship(back_populates="tasks")


class SecurityPatrolPlan(TenantScopedModel):
    """Scheduled physical security patrol route, shift window, and checkpoints."""

    __tablename__ = "campus_security_patrol_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "plan_code", name="uq_campus_sec_patrol_code"),
        Index("ix_campus_sec_patrol_tenant_active", "tenant_id", "is_active"),
    )

    plan_code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    shift_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="MORNING_SHIFT"
    )  # MORNING_SHIFT, AFTERNOON_SHIFT, NIGHT_SHIFT, WEEKEND_SHIFT
    frequency_hours: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    assigned_team_name: Mapped[str] = mapped_column(String(64), nullable=False)
    checkpoints_sequence: Mapped[list[str] | None] = mapped_column(JSONType, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supervisor_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)


class PatrolCheckpointRecord(TenantScopedModel):
    """Recorded visit or scan of a security checkpoint during a patrol round."""

    __tablename__ = "campus_security_patrol_records"
    __table_args__ = (
        Index("ix_campus_sec_patrolrec_plan", "tenant_id", "plan_id"),
        Index("ix_campus_sec_patrolrec_chkpt", "tenant_id", "checkpoint_id"),
        Index("ix_campus_sec_patrolrec_status", "tenant_id", "status"),
    )

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_patrol_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    checkpoint_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_checkpoints.id", ondelete="CASCADE"),
        nullable=False,
    )
    officer_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    officer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    scheduled_round_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="COMPLETED"
    )  # COMPLETED, MISSED, DELAYED, EXCEPTION_NOTED
    verification_token: Mapped[str | None] = mapped_column(String(128), nullable=True)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    incident_created_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_security_physical_incidents.id", ondelete="SET NULL"),
        nullable=True,
    )
    supervisor_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supervisor_review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, default=dict)

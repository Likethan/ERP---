"""Pydantic schemas for Enterprise Campus Physical Security, Visitor Management & Emergency Response (Step 68)."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# 1. CHECKPOINTS & ACCESS ZONES
# =============================================================================

class SecurityCheckpointCreate(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    checkpoint_type: str = Field("MAIN_GATE", max_length=32)
    location_description: str = Field(..., max_length=255)
    is_manned: bool = True
    operating_hours: str = Field("24x7", max_length=64)
    guard_post_phone: str | None = None
    is_active: bool = True
    metadata_json: dict[str, Any] | None = None


class SecurityCheckpointResponse(SecurityCheckpointCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


class SecurityZoneCreate(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    clearance_level: str = Field("CAMPUS_GENERAL", max_length=32)
    building_name: str | None = None
    floor_number: int | None = None
    requires_escort: bool = False
    max_occupancy: int | None = None
    emergency_assembly_point: str | None = None
    is_active: bool = True
    metadata_json: dict[str, Any] | None = None


class SecurityZoneResponse(SecurityZoneCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 2. VISITOR DIRECTORY & PRE-REGISTRATION
# =============================================================================

class VisitorProfileCreate(BaseModel):
    full_name: str = Field(..., max_length=128)
    email: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=32)
    organization: str | None = None
    id_document_type: str = Field("OTHER", max_length=32)
    id_document_number_masked: str | None = None
    is_vip: bool = False
    metadata_json: dict[str, Any] | None = None


class VisitorProfileResponse(VisitorProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    is_blacklisted: bool
    blacklist_reason: str | None
    total_visits: int
    created_at: datetime
    updated_at: datetime


class VisitorRequestCreate(BaseModel):
    visitor_name: str = Field(..., max_length=128)
    visitor_phone: str = Field(..., max_length=32)
    visitor_email: str = Field(..., max_length=255)
    visitor_category: str = Field("GUEST", max_length=32)
    organization: str | None = None
    id_document_type: str = "OTHER"
    id_document_number_masked: str | None = None
    host_name: str = Field(..., max_length=128)
    host_department: str | None = None
    visit_purpose: str = Field(..., max_length=255)
    destination_zone_id: UUID | None = None
    destination_description: str = Field(..., max_length=255)
    expected_arrival_at: datetime
    expected_departure_at: datetime
    has_vehicle: bool = False
    vehicle_number: str | None = None
    accompanying_count: int = 0
    metadata_json: dict[str, Any] | None = None


class VisitorRequestReview(BaseModel):
    decision: str = Field(..., max_length=16)  # APPROVED, REJECTED
    rejection_reason: str | None = None


class VisitorRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    request_number: str
    visitor_id: UUID
    visitor_name: str
    visitor_phone: str
    visitor_email: str
    visitor_category: str
    host_user_id: UUID | None
    host_name: str
    host_department: str | None
    visit_purpose: str
    destination_zone_id: UUID | None
    destination_description: str
    expected_arrival_at: datetime
    expected_departure_at: datetime
    status: str
    approval_required: bool
    approved_by_user_id: UUID | None
    approved_at: datetime | None
    rejection_reason: str | None
    vehicle_number: str | None
    has_vehicle: bool
    accompanying_count: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 3. VISITOR PASSES & GATE OPERATIONS
# =============================================================================

class VisitorGateCheckIn(BaseModel):
    checkpoint_id: UUID
    checkpoint_code: str | None = None
    vehicle_number: str | None = None
    officer_notes: str | None = None


class VisitorGateCheckOut(BaseModel):
    checkpoint_id: UUID
    officer_notes: str | None = None


class VisitorPassRevoke(BaseModel):
    revocation_reason: str = Field(..., max_length=255)


class VisitorPassVerifyRequest(BaseModel):
    signed_token: str


class VisitorPassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    pass_number: str
    request_id: UUID | None
    visitor_id: UUID
    visitor_name: str
    visitor_category: str
    host_name: str
    destination: str
    signed_token: str
    valid_from: datetime
    valid_until: datetime
    status: str
    check_in_at: datetime | None
    check_in_checkpoint_id: UUID | None
    check_in_officer_id: UUID | None
    check_out_at: datetime | None
    check_out_checkpoint_id: UUID | None
    check_out_officer_id: UUID | None
    is_overdue: bool
    revoked_at: datetime | None
    revocation_reason: str | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 4. CONTRACTOR PROFILES & ACCESS GRANTS
# =============================================================================

class ContractorProfileCreate(BaseModel):
    organization_name: str = Field(..., max_length=128)
    contractor_name: str = Field(..., max_length=128)
    contractor_phone: str = Field(..., max_length=32)
    service_type: str = Field(..., max_length=64)
    work_order_reference: str | None = None
    valid_from: date
    valid_until: date
    is_safety_induction_completed: bool = False
    safety_induction_date: date | None = None
    authorized_zone_ids: list[str] | None = None
    emergency_contact_phone: str | None = None
    badge_reference: str | None = None
    metadata_json: dict[str, Any] | None = None


class ContractorProfileUpdate(BaseModel):
    status: str | None = None
    is_safety_induction_completed: bool | None = None
    safety_induction_date: date | None = None
    valid_until: date | None = None
    authorized_zone_ids: list[str] | None = None


class ContractorProfileResponse(ContractorProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    contractor_code: str
    status: str
    created_at: datetime
    updated_at: datetime


class AccessGrantCreate(BaseModel):
    zone_id: UUID
    grantee_type: str = Field(..., max_length=32)
    grantee_id: str = Field(..., max_length=128)
    grantee_name: str = Field(..., max_length=128)
    valid_from: datetime
    valid_until: datetime
    is_temporary: bool = True
    grant_reason: str = Field(..., max_length=255)
    metadata_json: dict[str, Any] | None = None


class AccessGrantRevoke(BaseModel):
    revocation_reason: str = Field(..., max_length=255)


class AccessGrantResponse(AccessGrantCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    grant_number: str
    status: str
    granted_by_user_id: UUID | None
    revoked_at: datetime | None
    revoked_by_user_id: UUID | None
    revocation_reason: str | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 5. PHYSICAL SECURITY INCIDENTS
# =============================================================================

class SecurityIncidentCreate(BaseModel):
    title: str = Field(..., max_length=255)
    category: str = Field(..., max_length=32)
    severity: str = Field("MEDIUM", max_length=16)
    reported_location: str = Field(..., max_length=255)
    zone_id: UUID | None = None
    checkpoint_id: UUID | None = None
    description: str
    reported_by_name: str | None = None
    assigned_team: str | None = None
    evidence_urls: list[str] | None = None
    metadata_json: dict[str, Any] | None = None


class SecurityIncidentUpdate(BaseModel):
    status: str | None = None
    assigned_team: str | None = None
    assigned_to_user_id: UUID | None = None
    resolution_summary: str | None = None
    corrective_action_notes: str | None = None


class SecurityIncidentEscalate(BaseModel):
    escalation_reason: str = Field(..., max_length=255)
    target_team: str | None = None


class CampusSecurityIncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    incident_number: str
    title: str
    category: str
    severity: str
    status: str
    reported_at: datetime
    reported_by_user_id: UUID | None
    reported_by_name: str | None
    reported_location: str
    zone_id: UUID | None
    checkpoint_id: UUID | None
    description: str
    assigned_team: str | None
    assigned_to_user_id: UUID | None
    assigned_at: datetime | None
    is_escalated: bool
    escalated_at: datetime | None
    escalation_reason: str | None
    resolution_summary: str | None
    resolved_at: datetime | None
    resolved_by_user_id: UUID | None
    corrective_action_notes: str | None
    evidence_urls: list[str] | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 6. EMERGENCY RESPONSE COORDINATION
# =============================================================================

class EmergencyEventCreate(BaseModel):
    title: str = Field(..., max_length=255)
    event_type: str = Field(..., max_length=32)
    severity: str = Field("EMERGENCY", max_length=16)
    affected_campus_areas: str = Field(..., max_length=255)
    affected_zone_ids: list[str] | None = None
    coordinator_name: str = Field(..., max_length=128)
    emergency_broadcast_message: str | None = None
    external_services_contacted: list[str] | None = None
    metadata_json: dict[str, Any] | None = None


class EmergencyEventUpdate(BaseModel):
    status: str | None = None
    after_action_report: str | None = None
    external_services_contacted: list[str] | None = None


class EmergencyTaskCreate(BaseModel):
    task_title: str = Field(..., max_length=255)
    priority: str = Field("HIGH", max_length=16)
    assigned_to_role: str | None = None
    action_checklist: list[dict[str, Any]] | None = None
    notes: str | None = None


class EmergencyTaskUpdate(BaseModel):
    status: str
    notes: str | None = None


class EmergencyResponseTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    event_id: UUID
    task_title: str
    priority: str
    assigned_to_role: str | None
    assigned_to_user_id: UUID | None
    status: str
    action_checklist: list[dict[str, Any]] | None
    completed_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class EmergencyEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    event_code: str
    title: str
    event_type: str
    severity: str
    status: str
    affected_campus_areas: str
    affected_zone_ids: list[str] | None
    coordinator_user_id: UUID | None
    coordinator_name: str
    emergency_broadcast_message: str | None
    initiated_at: datetime
    all_clear_at: datetime | None
    closed_at: datetime | None
    after_action_report: str | None
    external_services_contacted: list[str] | None
    tasks: list[EmergencyResponseTaskResponse] = []
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 7. SECURITY PATROLS & CHECKPOINT ROUNDS
# =============================================================================

class PatrolPlanCreate(BaseModel):
    title: str = Field(..., max_length=128)
    shift_name: str = Field("MORNING_SHIFT", max_length=64)
    frequency_hours: int = 2
    assigned_team_name: str = Field(..., max_length=64)
    checkpoints_sequence: list[str] | None = None
    is_active: bool = True
    metadata_json: dict[str, Any] | None = None


class PatrolCheckpointRecordCreate(BaseModel):
    plan_id: UUID
    checkpoint_id: UUID
    officer_name: str = Field(..., max_length=128)
    scheduled_round_time: datetime
    verification_token: str | None = None
    observations: str | None = None
    status: str = "COMPLETED"


class PatrolSupervisorReview(BaseModel):
    supervisor_review_notes: str = Field(..., max_length=255)


class PatrolCheckpointRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    checkpoint_id: UUID
    officer_user_id: UUID | None
    officer_name: str
    scheduled_round_time: datetime
    scanned_at: datetime | None
    status: str
    verification_token: str | None
    observations: str | None
    incident_created_id: UUID | None
    supervisor_reviewed: bool
    supervisor_review_notes: str | None
    created_at: datetime
    updated_at: datetime


class SecurityPatrolPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    plan_code: str
    title: str
    shift_name: str
    frequency_hours: int
    assigned_team_name: str
    checkpoints_sequence: list[str] | None
    is_active: bool
    supervisor_user_id: UUID | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 8. EXECUTIVE OPERATIONS DASHBOARD OVERVIEW
# =============================================================================

class SecurityOperationsOverviewResponse(BaseModel):
    visitors_currently_on_campus: int
    expected_arrivals_today: int
    pending_visitor_approvals: int
    overdue_visitor_departures: int
    active_contractors_on_site: int
    active_access_grants: int
    open_security_incidents: int
    critical_incidents_count: int
    active_emergency_events: int
    patrol_completion_rate_pct: float
    manned_checkpoints_count: int
    security_readiness_score: float


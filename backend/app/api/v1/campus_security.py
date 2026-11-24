"""CampusOS Enterprise Campus Physical Security, Visitor Management & Emergency Response API Router (Step 68).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    CAMPUS_SECURITY_ACCESS_GRANT_MANAGE,
    CAMPUS_SECURITY_ACCESS_ZONE_MANAGE,
    CAMPUS_SECURITY_ACCESS_ZONE_READ,
    CAMPUS_SECURITY_ANALYTICS_READ,
    CAMPUS_SECURITY_CONFIG_MANAGE,
    CAMPUS_SECURITY_CONFIG_READ,
    CAMPUS_SECURITY_CONTRACTOR_MANAGE,
    CAMPUS_SECURITY_CONTRACTOR_READ,
    CAMPUS_SECURITY_EMERGENCY_MANAGE,
    CAMPUS_SECURITY_EMERGENCY_READ,
    CAMPUS_SECURITY_GATE_CHECKIN,
    CAMPUS_SECURITY_GATE_CHECKOUT,
    CAMPUS_SECURITY_INCIDENT_MANAGE,
    CAMPUS_SECURITY_INCIDENT_READ,
    CAMPUS_SECURITY_INCIDENT_REPORT,
    CAMPUS_SECURITY_PASS_REVOKE,
    CAMPUS_SECURITY_PATROL_MANAGE,
    CAMPUS_SECURITY_PATROL_READ,
    CAMPUS_SECURITY_VISITOR_APPROVE,
    CAMPUS_SECURITY_VISITOR_READ,
    CAMPUS_SECURITY_VISITOR_REQUEST,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.campus_security import (
    AccessGrantCreate,
    AccessGrantResponse,
    AccessGrantRevoke,
    CampusSecurityIncidentResponse,
    ContractorProfileCreate,
    ContractorProfileResponse,
    ContractorProfileUpdate,
    EmergencyEventCreate,
    EmergencyEventResponse,
    EmergencyEventUpdate,
    EmergencyResponseTaskResponse,
    EmergencyTaskCreate,
    EmergencyTaskUpdate,
    PatrolCheckpointRecordCreate,
    PatrolCheckpointRecordResponse,
    PatrolPlanCreate,
    PatrolSupervisorReview,
    SecurityCheckpointCreate,
    SecurityCheckpointResponse,
    SecurityIncidentCreate,
    SecurityIncidentEscalate,
    SecurityIncidentUpdate,
    SecurityOperationsOverviewResponse,
    SecurityPatrolPlanResponse,
    SecurityZoneCreate,
    SecurityZoneResponse,
    VisitorGateCheckIn,
    VisitorGateCheckOut,
    VisitorPassResponse,
    VisitorPassRevoke,
    VisitorPassVerifyRequest,
    VisitorProfileCreate,
    VisitorProfileResponse,
    VisitorRequestCreate,
    VisitorRequestResponse,
    VisitorRequestReview,
)
from app.services.campus_security_service import CampusSecurityService

router = APIRouter(prefix="/campus-security", tags=["Campus Security & Visitor Management"])


# =============================================================================
# 1. EXECUTIVE COMMAND DASHBOARD & ANALYTICS
# =============================================================================

@router.get(
    "/overview",
    response_model=SecurityOperationsOverviewResponse,
    summary="Get campus physical security operations scorecard and metrics",
)
async def get_security_overview(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_ANALYTICS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    data = await service.get_overview(tenant_context.tenant_id)
    return SecurityOperationsOverviewResponse(**data)


# =============================================================================
# 2. CHECKPOINTS & SECURITY ZONES
# =============================================================================

@router.get(
    "/checkpoints",
    response_model=list[SecurityCheckpointResponse],
    summary="List physical security gates, turnstiles, and barriers",
)
async def list_checkpoints(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_CONFIG_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_manned: bool | None = None,
):
    service = CampusSecurityService(db)
    return await service.list_checkpoints(tenant_context.tenant_id, is_manned=is_manned)


@router.post(
    "/checkpoints",
    response_model=SecurityCheckpointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new security gate or checkpoint",
)
async def create_checkpoint(
    payload: SecurityCheckpointCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_CONFIG_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.create_checkpoint(tenant_context.tenant_id, payload)


@router.get(
    "/zones",
    response_model=list[SecurityZoneResponse],
    summary="List campus security zones and clearance levels",
)
async def list_zones(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_ACCESS_ZONE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    clearance_level: str | None = None,
):
    service = CampusSecurityService(db)
    return await service.list_zones(tenant_context.tenant_id, clearance_level=clearance_level)


@router.post(
    "/zones",
    response_model=SecurityZoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Define a new security zone or restricted area",
)
async def create_zone(
    payload: SecurityZoneCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_ACCESS_ZONE_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.create_zone(tenant_context.tenant_id, payload)


# =============================================================================
# 3. VISITOR DIRECTORY & PRE-REGISTRATION
# =============================================================================

@router.get(
    "/visitors",
    response_model=list[VisitorProfileResponse],
    summary="List verified visitor directory profiles",
)
async def list_visitor_profiles(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_VISITOR_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    search: str | None = None,
):
    service = CampusSecurityService(db)
    return await service.list_visitor_profiles(tenant_context.tenant_id, search=search)


@router.post(
    "/visitors",
    response_model=VisitorProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or resolve a visitor directory record",
)
async def create_visitor_profile(
    payload: VisitorProfileCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_VISITOR_REQUEST))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.get_or_create_visitor_profile(tenant_context.tenant_id, payload)


@router.get(
    "/requests",
    response_model=list[VisitorRequestResponse],
    summary="List visitor pre-registration and host invitation requests",
)
async def list_visitor_requests(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_VISITOR_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    request_status: str | None = Query(None, alias="status"),
):
    service = CampusSecurityService(db)
    return await service.list_visitor_requests(tenant_context.tenant_id, status=request_status)


@router.post(
    "/requests",
    response_model=VisitorRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit visitor pre-registration request",
)
async def submit_visitor_request(
    payload: VisitorRequestCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_VISITOR_REQUEST))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.submit_visitor_request(tenant_context.tenant_id, payload, host_user_id=current_user.id)


@router.post(
    "/requests/{request_id}/review",
    response_model=VisitorRequestResponse,
    summary="Approve or reject visitor pre-registration",
)
async def review_visitor_request(
    request_id: UUID,
    payload: VisitorRequestReview,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_VISITOR_APPROVE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    req, _ = await service.review_visitor_request(
        tenant_context.tenant_id, request_id, current_user.id, payload
    )
    return req


# =============================================================================
# 4. GATE OPERATIONS (PASSES, CHECK-IN, CHECK-OUT)
# =============================================================================

@router.get(
    "/passes",
    response_model=list[VisitorPassResponse],
    summary="List active, checked-in, and completed visitor passes",
)
async def list_visitor_passes(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_VISITOR_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    pass_status: str | None = Query(None, alias="status"),
):
    service = CampusSecurityService(db)
    return await service.list_passes(tenant_context.tenant_id, status=pass_status)


@router.post(
    "/passes/verify",
    response_model=VisitorPassResponse,
    summary="Cryptographically verify a visitor pass QR token",
)
async def verify_pass_token(
    payload: VisitorPassVerifyRequest,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_GATE_CHECKIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.verify_pass_token(tenant_context.tenant_id, payload.signed_token)


@router.post(
    "/passes/{pass_id}/check-in",
    response_model=VisitorPassResponse,
    summary="Record visitor arrival and gate check-in",
)
async def gate_check_in(
    pass_id: UUID,
    payload: VisitorGateCheckIn,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_GATE_CHECKIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.gate_check_in(
        tenant_context.tenant_id, pass_id, payload, officer_user_id=current_user.id
    )


@router.post(
    "/passes/{pass_id}/check-out",
    response_model=VisitorPassResponse,
    summary="Record visitor departure and gate check-out",
)
async def gate_check_out(
    pass_id: UUID,
    payload: VisitorGateCheckOut,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_GATE_CHECKOUT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.gate_check_out(
        tenant_context.tenant_id, pass_id, payload, officer_user_id=current_user.id
    )


@router.post(
    "/passes/{pass_id}/revoke",
    response_model=VisitorPassResponse,
    summary="Revoke visitor pass or cancel active access",
)
async def revoke_visitor_pass(
    pass_id: UUID,
    payload: VisitorPassRevoke,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_PASS_REVOKE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.revoke_pass(
        tenant_context.tenant_id, pass_id, payload.revocation_reason, officer_user_id=current_user.id
    )


@router.post(
    "/passes/flag-overdue",
    summary="Batch identify and tag overdue visitors who have not checked out",
)
async def flag_overdue_passes(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_GATE_CHECKOUT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    count = await service.flag_overdue_visitors(tenant_context.tenant_id)
    return {"status": "SUCCESS", "overdue_flagged_count": count}


# =============================================================================
# 5. CONTRACTORS & ZONE ACCESS GRANTS
# =============================================================================

@router.get(
    "/contractors",
    response_model=list[ContractorProfileResponse],
    summary="List recurring contractor profiles and work permits",
)
async def list_contractors(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_CONTRACTOR_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    contractor_status: str | None = Query(None, alias="status"),
):
    service = CampusSecurityService(db)
    return await service.list_contractor_profiles(tenant_context.tenant_id, status=contractor_status)


@router.post(
    "/contractors",
    response_model=ContractorProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register recurring contractor with safety induction details",
)
async def create_contractor(
    payload: ContractorProfileCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_CONTRACTOR_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.create_contractor_profile(tenant_context.tenant_id, payload)


@router.put(
    "/contractors/{contractor_id}",
    response_model=ContractorProfileResponse,
    summary="Update contractor induction status or access authorization",
)
async def update_contractor(
    contractor_id: UUID,
    payload: ContractorProfileUpdate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_CONTRACTOR_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.update_contractor_profile(tenant_context.tenant_id, contractor_id, payload)


@router.get(
    "/access-grants",
    response_model=list[AccessGrantResponse],
    summary="List logical zone access authorizations",
)
async def list_access_grants(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_ACCESS_ZONE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    zone_id: UUID | None = None,
    grant_status: str | None = Query(None, alias="status"),
):
    service = CampusSecurityService(db)
    return await service.list_access_grants(tenant_context.tenant_id, zone_id=zone_id, status=grant_status)


@router.post(
    "/access-grants",
    response_model=AccessGrantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a time-bounded zone access grant",
)
async def create_access_grant(
    payload: AccessGrantCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_ACCESS_GRANT_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.create_access_grant(tenant_context.tenant_id, payload, granter_user_id=current_user.id)


@router.post(
    "/access-grants/{grant_id}/revoke",
    response_model=AccessGrantResponse,
    summary="Revoke an active zone access grant",
)
async def revoke_access_grant(
    grant_id: UUID,
    payload: AccessGrantRevoke,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_ACCESS_GRANT_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.revoke_access_grant(
        tenant_context.tenant_id, grant_id, payload.revocation_reason, revoker_user_id=current_user.id
    )


# =============================================================================
# 6. PHYSICAL SECURITY INCIDENTS
# =============================================================================

@router.get(
    "/incidents",
    response_model=list[CampusSecurityIncidentResponse],
    summary="List physical security incident logs and case statuses",
)
async def list_incidents(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_INCIDENT_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    incident_status: str | None = Query(None, alias="status"),
    severity: str | None = None,
    category: str | None = None,
):
    service = CampusSecurityService(db)
    return await service.list_incidents(
        tenant_context.tenant_id, status=incident_status, severity=severity, category=category
    )


@router.post(
    "/incidents",
    response_model=CampusSecurityIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a campus physical security incident or safety hazard",
)
async def report_incident(
    payload: SecurityIncidentCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_INCIDENT_REPORT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.create_incident(tenant_context.tenant_id, payload, reporter_user_id=current_user.id)


@router.put(
    "/incidents/{incident_id}",
    response_model=CampusSecurityIncidentResponse,
    summary="Update incident progress, assigned responder, or status",
)
async def update_incident(
    incident_id: UUID,
    payload: SecurityIncidentUpdate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_INCIDENT_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.update_incident(tenant_context.tenant_id, incident_id, payload)


@router.post(
    "/incidents/{incident_id}/escalate",
    response_model=CampusSecurityIncidentResponse,
    summary="Escalate incident to senior response team",
)
async def escalate_incident(
    incident_id: UUID,
    payload: SecurityIncidentEscalate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_INCIDENT_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.escalate_incident(
        tenant_context.tenant_id, incident_id, payload.escalation_reason, target_team=payload.target_team
    )


# =============================================================================
# 7. EMERGENCY RESPONSE COORDINATION
# =============================================================================

@router.get(
    "/emergency/events",
    response_model=list[EmergencyEventResponse],
    summary="List emergency event workspaces and timelines",
)
async def list_emergency_events(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_EMERGENCY_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_status: str | None = Query(None, alias="status"),
):
    service = CampusSecurityService(db)
    return await service.list_emergency_events(tenant_context.tenant_id, status=event_status)


@router.post(
    "/emergency/events",
    response_model=EmergencyEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate institution-wide emergency response event",
)
async def create_emergency_event(
    payload: EmergencyEventCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_EMERGENCY_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.create_emergency_event(
        tenant_context.tenant_id, payload, coordinator_user_id=current_user.id
    )


@router.put(
    "/emergency/events/{event_id}",
    response_model=EmergencyEventResponse,
    summary="Update emergency situation status or file after-action report",
)
async def update_emergency_event(
    event_id: UUID,
    payload: EmergencyEventUpdate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_EMERGENCY_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.update_emergency_event(tenant_context.tenant_id, event_id, payload)


@router.post(
    "/emergency/events/{event_id}/tasks",
    response_model=EmergencyResponseTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an emergency checklist action task",
)
async def create_emergency_task(
    event_id: UUID,
    payload: EmergencyTaskCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_EMERGENCY_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.create_emergency_task(tenant_context.tenant_id, event_id, payload)


@router.put(
    "/emergency/tasks/{task_id}",
    response_model=EmergencyResponseTaskResponse,
    summary="Update emergency task completion status",
)
async def update_emergency_task(
    task_id: UUID,
    payload: EmergencyTaskUpdate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_EMERGENCY_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.update_emergency_task(tenant_context.tenant_id, task_id, payload)


# =============================================================================
# 8. PATROLS & CHECKPOINT ROUNDS
# =============================================================================

@router.get(
    "/patrols/plans",
    response_model=list[SecurityPatrolPlanResponse],
    summary="List security patrol schedules and checkpoint sequences",
)
async def list_patrol_plans(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_PATROL_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.list_patrol_plans(tenant_context.tenant_id)


@router.post(
    "/patrols/plans",
    response_model=SecurityPatrolPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a security patrol plan",
)
async def create_patrol_plan(
    payload: PatrolPlanCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_PATROL_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.create_patrol_plan(tenant_context.tenant_id, payload, supervisor_user_id=current_user.id)


@router.post(
    "/patrols/records",
    response_model=PatrolCheckpointRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a completed checkpoint round observation",
)
async def record_patrol_checkpoint(
    payload: PatrolCheckpointRecordCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_PATROL_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.record_patrol_checkpoint(tenant_context.tenant_id, payload, officer_user_id=current_user.id)


@router.post(
    "/patrols/records/{record_id}/review",
    response_model=PatrolCheckpointRecordResponse,
    summary="Supervisor review and sign-off on checkpoint log",
)
async def review_patrol_record(
    record_id: UUID,
    payload: PatrolSupervisorReview,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CAMPUS_SECURITY_PATROL_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = CampusSecurityService(db)
    return await service.review_patrol_record(tenant_context.tenant_id, record_id, payload.supervisor_review_notes)


campus_security_router = router

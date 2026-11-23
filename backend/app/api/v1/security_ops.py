"""Security Operations & Incident Response REST APIs (Step 33).

Provides endpoints for:
- Security Operations Center (SOC) telemetry overview
- Incident management with valid state lifecycle transitions
- Responder assignment, forensic investigation notes, and remediation tasks
- Detection signal and evidence review
- Controlled containment response actions (propose, approve, reject, execute, rollback)
- Threat detection rule inspection and runtime tuning
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import (
    require_permission,
    resolve_user_permissions,
)
from app.core.permissions import (
    SECURITY_ACTIONS_APPROVE,
    SECURITY_ACTIONS_EXECUTE,
    SECURITY_ACTIONS_PROPOSE,
    SECURITY_INCIDENTS_MANAGE,
    SECURITY_INCIDENTS_READ,
    SECURITY_RULES_MANAGE,
)
from app.models.people import User
from app.schemas.security_ops import (
    SecurityDetectionListResponse,
    SecurityDetectionResponse,
    SecurityDetectionRuleResponse,
    SecurityDetectionRuleUpdateRequest,
    SecurityIncidentAssignRequest,
    SecurityIncidentListResponse,
    SecurityIncidentNoteCreateRequest,
    SecurityIncidentNoteResponse,
    SecurityIncidentResponse,
    SecurityIncidentStatusUpdateRequest,
    SecurityRemediationTaskCreateRequest,
    SecurityRemediationTaskResponse,
    SecurityRemediationTaskStatusUpdateRequest,
    SecurityResponseActionProposeRequest,
    SecurityResponseActionRejectRequest,
    SecurityResponseActionResponse,
    SocOverviewResponse,
)
from app.services.security_ops_service import SecurityOpsService
from app.services.security_response_service import SecurityResponseService

router = APIRouter(prefix="/security", tags=["Enterprise Security Operations"])


def is_platform_sec_operator(user: User) -> bool:
    """Check if the actor possesses platform-wide or cross-tenant security privileges."""
    user_roles = {ur.role.name for ur in user.roles if ur.role}
    if "SUPER_ADMIN" in user_roles or "PLATFORM_OPERATOR" in user_roles:
        return True
    user_permissions = resolve_user_permissions(user)
    return (
        "*" in user_permissions
        or "security:platform:read" in user_permissions
        or "security.platform.read" in user_permissions
    )


def extract_actor_tenant_id(user: User, request: Request) -> UUID | None:
    """Extract authoritative server-side tenant ID for the current actor."""
    if hasattr(request.state, "tenant") and request.state.tenant and request.state.tenant.tenant_id:
        return request.state.tenant.tenant_id
    return user.primary_tenant_id


# -----------------------------------------------------------------------------
# 1. SOC Overview
# -----------------------------------------------------------------------------
@router.get(
    "/overview",
    response_model=SocOverviewResponse,
    summary="Get Security Operations Center metrics overview",
)
async def get_soc_overview(
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SocOverviewResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    stats = await SecurityOpsService.get_soc_overview(db, tenant_id, is_plat)
    return SocOverviewResponse(**stats)


# -----------------------------------------------------------------------------
# 2. Security Incidents
# -----------------------------------------------------------------------------
@router.get(
    "/incidents",
    response_model=SecurityIncidentListResponse,
    summary="List security incidents with tenant isolation",
)
async def list_incidents(
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by status (NEW, TRIAGED, INVESTIGATING, etc.)"),
    severity: str | None = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> SecurityIncidentListResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    items, total = await SecurityOpsService.list_incidents(
        db, tenant_id, is_plat, status, severity, skip, limit
    )
    return SecurityIncidentListResponse(
        items=[SecurityIncidentResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get(
    "/incidents/{incident_id}",
    response_model=SecurityIncidentResponse,
    summary="Get comprehensive incident details and timeline",
)
async def get_incident(
    incident_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityIncidentResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    incident = await SecurityOpsService.get_incident(db, incident_id, tenant_id, is_plat)
    return SecurityIncidentResponse.model_validate(incident)


@router.post(
    "/incidents/{incident_id}/status",
    response_model=SecurityIncidentResponse,
    summary="Transition incident lifecycle state",
)
async def update_incident_status(
    incident_id: UUID,
    body: SecurityIncidentStatusUpdateRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityIncidentResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    incident = await SecurityOpsService.transition_status(
        db=db,
        incident_id=incident_id,
        new_status=body.status,
        user_id=current_user.id,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
        reason=body.reason,
        closure_summary=body.closure_summary,
    )
    return SecurityIncidentResponse.model_validate(incident)


@router.post(
    "/incidents/{incident_id}/assign",
    response_model=SecurityIncidentResponse,
    summary="Assign responder to security incident",
)
async def assign_responder(
    incident_id: UUID,
    body: SecurityIncidentAssignRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityIncidentResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    incident = await SecurityOpsService.assign_responder(
        db=db,
        incident_id=incident_id,
        assigned_to_user_id=body.assigned_to_user_id,
        actor_user_id=current_user.id,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
    )
    return SecurityIncidentResponse.model_validate(incident)


@router.post(
    "/incidents/{incident_id}/notes",
    response_model=SecurityIncidentNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add investigation timeline note to incident",
)
async def add_incident_note(
    incident_id: UUID,
    body: SecurityIncidentNoteCreateRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityIncidentNoteResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    note = await SecurityOpsService.add_note(
        db=db,
        incident_id=incident_id,
        author_user_id=current_user.id,
        content=body.content,
        note_type=body.note_type,
        evidence_references=body.evidence_references,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
    )
    return SecurityIncidentNoteResponse.model_validate(note)


# -----------------------------------------------------------------------------
# 3. Remediation Tasks
# -----------------------------------------------------------------------------
@router.post(
    "/incidents/{incident_id}/tasks",
    response_model=SecurityRemediationTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a post-incident verification remediation task",
)
async def create_remediation_task(
    incident_id: UUID,
    body: SecurityRemediationTaskCreateRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityRemediationTaskResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    task = await SecurityOpsService.create_remediation_task(
        db=db,
        incident_id=incident_id,
        title=body.title,
        description=body.description,
        assigned_to_user_id=body.assigned_to_user_id,
        due_at=body.due_at,
        actor_user_id=current_user.id,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
    )
    return SecurityRemediationTaskResponse.model_validate(task)


@router.patch(
    "/tasks/{task_id}/status",
    response_model=SecurityRemediationTaskResponse,
    summary="Update remediation task status",
)
async def update_task_status(
    task_id: UUID,
    body: SecurityRemediationTaskStatusUpdateRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityRemediationTaskResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    task = await SecurityOpsService.update_remediation_task_status(
        db=db,
        task_id=task_id,
        new_status=body.status,
        actor_user_id=current_user.id,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
    )
    return SecurityRemediationTaskResponse.model_validate(task)


# -----------------------------------------------------------------------------
# 4. Security Detections
# -----------------------------------------------------------------------------
@router.get(
    "/detections",
    response_model=SecurityDetectionListResponse,
    summary="List normalized threat detections and signals",
)
async def list_detections(
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    rule_id: str | None = Query(None),
    severity: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> SecurityDetectionListResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    items, total = await SecurityOpsService.list_detections(
        db, tenant_id, is_plat, rule_id, severity, skip, limit
    )
    return SecurityDetectionListResponse(
        items=[SecurityDetectionResponse.model_validate(d) for d in items],
        total=total,
    )


# -----------------------------------------------------------------------------
# 5. Security Response Actions
# -----------------------------------------------------------------------------
@router.post(
    "/actions/propose",
    response_model=SecurityResponseActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Propose a containment or remediation response action",
)
async def propose_response_action(
    body: SecurityResponseActionProposeRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_ACTIONS_PROPOSE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityResponseActionResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    action = await SecurityResponseService.propose_action(
        db=db,
        incident_id=body.incident_id,
        action_type=body.action_type,
        target_type=body.target_type,
        target_identifier=body.target_identifier,
        risk_level=body.risk_level,
        requires_approval=body.requires_approval,
        proposed_by_user_id=current_user.id,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
        payload=body.payload,
    )
    return SecurityResponseActionResponse.model_validate(action)


@router.post(
    "/actions/{action_id}/approve",
    response_model=SecurityResponseActionResponse,
    summary="Approve a proposed containment action",
)
async def approve_response_action(
    action_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_ACTIONS_APPROVE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityResponseActionResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    action = await SecurityResponseService.approve_action(
        db=db,
        action_id=action_id,
        approving_user_id=current_user.id,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
    )
    return SecurityResponseActionResponse.model_validate(action)


@router.post(
    "/actions/{action_id}/reject",
    response_model=SecurityResponseActionResponse,
    summary="Reject a proposed containment action",
)
async def reject_response_action(
    action_id: UUID,
    body: SecurityResponseActionRejectRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_ACTIONS_APPROVE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityResponseActionResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    action = await SecurityResponseService.reject_action(
        db=db,
        action_id=action_id,
        rejecting_user_id=current_user.id,
        reason=body.reason,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
    )
    return SecurityResponseActionResponse.model_validate(action)


@router.post(
    "/actions/{action_id}/execute",
    response_model=SecurityResponseActionResponse,
    summary="Execute an approved containment action with safety controls",
)
async def execute_response_action(
    action_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_ACTIONS_EXECUTE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityResponseActionResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    action = await SecurityResponseService.execute_action(
        db=db,
        action_id=action_id,
        executing_user_id=current_user.id,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
    )
    return SecurityResponseActionResponse.model_validate(action)


@router.post(
    "/actions/{action_id}/rollback",
    response_model=SecurityResponseActionResponse,
    summary="Rollback an executed reversible containment action",
)
async def rollback_response_action(
    action_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(SECURITY_ACTIONS_EXECUTE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityResponseActionResponse:
    tenant_id = extract_actor_tenant_id(current_user, request)
    is_plat = is_platform_sec_operator(current_user)
    action = await SecurityResponseService.rollback_action(
        db=db,
        action_id=action_id,
        user_id=current_user.id,
        tenant_id=tenant_id,
        is_platform_operator=is_plat,
    )
    return SecurityResponseActionResponse.model_validate(action)


# -----------------------------------------------------------------------------
# 6. Detection Rules Configuration
# -----------------------------------------------------------------------------
@router.get(
    "/rules",
    response_model=list[SecurityDetectionRuleResponse],
    summary="List configurable threat detection rules",
)
async def list_detection_rules(
    current_user: Annotated[User, Depends(require_permission(SECURITY_INCIDENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SecurityDetectionRuleResponse]:
    rules = await SecurityOpsService.list_rules(db)
    return [SecurityDetectionRuleResponse.model_validate(r) for r in rules]


@router.patch(
    "/rules/{rule_id}",
    response_model=SecurityDetectionRuleResponse,
    summary="Tune detection rule parameters and thresholds",
)
async def update_detection_rule(
    rule_id: str,
    body: SecurityDetectionRuleUpdateRequest,
    current_user: Annotated[User, Depends(require_permission(SECURITY_RULES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SecurityDetectionRuleResponse:
    rule = await SecurityOpsService.configure_rule(
        db=db,
        rule_id=rule_id,
        is_enabled=body.is_enabled,
        threshold=body.threshold,
        evaluation_window_seconds=body.evaluation_window_seconds,
        severity=body.severity,
    )
    return SecurityDetectionRuleResponse.model_validate(rule)

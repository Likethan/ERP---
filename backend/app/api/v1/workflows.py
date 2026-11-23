"""Enterprise Workflow and Automated Operations API Endpoints.

Supports:
- Workflow CRUD, lifecycle (Draft, Active, Paused, Archived), and immutable versioning
- Granular PBAC permission enforcement on every action and endpoint
- Manual and scheduled execution dispatch with deterministic idempotency
- Full execution audit tracking and dead-letter visibility
- Event and Action registries for frontend/operator introspection
- Operational telemetry and health metrics
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.events import EVENT_REGISTRY
from app.core.permissions import (
    WORKFLOW_EXECUTIONS_READ,
    WORKFLOWS_ACTIVATE,
    WORKFLOWS_ARCHIVE,
    WORKFLOWS_CANCEL,
    WORKFLOWS_CREATE,
    WORKFLOWS_EXECUTE,
    WORKFLOWS_PAUSE,
    WORKFLOWS_READ,
    WORKFLOWS_RETRY,
    WORKFLOWS_UPDATE,
)
from app.core.tenant import TenantContext
from app.core.workflow_actions import ACTION_REGISTRY
from app.models.people import User
from app.models.workflow import WorkflowTriggerType
from app.schemas.common import ApiResponse
from app.schemas.workflow import (
    ActionRegistryItem,
    EventRegistryItem,
    WorkflowCreate,
    WorkflowExecutionRead,
    WorkflowManualExecutionRequest,
    WorkflowOperationalMetrics,
    WorkflowRead,
    WorkflowUpdate,
    WorkflowVersionRead,
)
from app.services.workflow_service import WorkflowService

router = APIRouter(tags=["Workflow & Automation Engine"])


# =============================================================================
# 1. REGISTRIES & METRICS (MUST PRECEDE PARAMETERIZED /workflows/{id})
# =============================================================================

@router.get("/workflows/events", response_model=ApiResponse[list[EventRegistryItem]])
async def get_event_registry(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_READ))],
) -> ApiResponse[list[EventRegistryItem]]:
    """Retrieve central allowlist of registered domain events and their allowed payload keys."""
    items = [
        EventRegistryItem(
            event_type=e.event_type.value,
            aggregate_type=e.aggregate_type,
            description=e.description,
            allowed_payload_keys=sorted(list(e.allowed_payload_keys)),
        )
        for e in EVENT_REGISTRY.values()
    ]
    return ApiResponse(data=items, message="Event registry retrieved successfully")


@router.get("/workflows/actions", response_model=ApiResponse[list[ActionRegistryItem]])
async def get_action_registry(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_READ))],
) -> ApiResponse[list[ActionRegistryItem]]:
    """Retrieve central allowlist of permitted workflow actions and their parameter definitions."""
    items = [
        ActionRegistryItem(
            action_type=a.action_type.value,
            description=a.description,
            required_permission=a.required_permission,
            is_system_only=a.is_system_only,
            allowed_params=sorted(list(a.allowed_params)),
        )
        for a in ACTION_REGISTRY.values()
    ]
    return ApiResponse(data=items, message="Action registry retrieved successfully")


@router.get("/workflows/metrics", response_model=ApiResponse[WorkflowOperationalMetrics])
async def get_workflow_metrics(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowOperationalMetrics]:
    """Retrieve operational telemetry and health metrics for the tenant's workflow subsystem."""
    metrics = await WorkflowService.get_operational_metrics(db, tenant.tenant_id)
    return ApiResponse(data=metrics, message="Workflow metrics retrieved successfully")


# =============================================================================
# 2. WORKFLOW CRUD & LIFECYCLE
# =============================================================================

@router.get("/workflows", response_model=ApiResponse[list[WorkflowRead]])
async def list_workflows(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by status (DRAFT, ACTIVE, PAUSED, ARCHIVED)"),
    domain: str | None = Query(None, description="Filter by domain"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ApiResponse[list[WorkflowRead]]:
    """List all workflow definitions for the authenticated tenant."""
    workflows, total = await WorkflowService.list_workflows(
        db=db,
        tenant_id=tenant.tenant_id,
        status=status,
        domain=domain,
        limit=limit,
        offset=offset,
    )
    result = [WorkflowRead.model_validate(w) for w in workflows]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} workflows")


@router.post("/workflows", response_model=ApiResponse[WorkflowRead], status_code=status.HTTP_201_CREATED)
async def create_workflow(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_CREATE))],
    payload: WorkflowCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowRead]:
    """Create a new workflow definition in DRAFT status with initial Version 1."""
    wf = await WorkflowService.create_workflow(
        db=db,
        tenant_id=tenant.tenant_id,
        payload=payload,
        actor_id=current_user.id,
        is_system=False,
    )
    return ApiResponse(
        data=WorkflowRead.model_validate(wf),
        message="Workflow created successfully in DRAFT status"
    )


@router.get("/workflows/{id}", response_model=ApiResponse[WorkflowRead])
async def get_workflow(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowRead]:
    """Fetch complete workflow definition and active configuration."""
    wf = await WorkflowService.get_workflow(db, tenant.tenant_id, id)
    return ApiResponse(data=WorkflowRead.model_validate(wf), message="Workflow retrieved successfully")


@router.patch("/workflows/{id}", response_model=ApiResponse[WorkflowRead])
async def update_workflow(
    id: UUID,
    payload: WorkflowUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowRead]:
    """Update workflow definition. Bumps version number if trigger or steps changed."""
    wf = await WorkflowService.update_workflow(
        db=db,
        tenant_id=tenant.tenant_id,
        workflow_id=id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=WorkflowRead.model_validate(wf), message="Workflow updated successfully")


@router.post("/workflows/{id}/activate", response_model=ApiResponse[WorkflowRead])
async def activate_workflow(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_ACTIVATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowRead]:
    """Validate definition, verify permissions and actions, and transition workflow to ACTIVE."""
    wf = await WorkflowService.activate_workflow(db, tenant.tenant_id, id, actor_id=current_user.id)
    return ApiResponse(data=WorkflowRead.model_validate(wf), message="Workflow activated successfully")


@router.post("/workflows/{id}/pause", response_model=ApiResponse[WorkflowRead])
async def pause_workflow(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_PAUSE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowRead]:
    """Pause an active workflow. Prevents new scheduled or event-driven executions."""
    wf = await WorkflowService.pause_workflow(db, tenant.tenant_id, id, actor_id=current_user.id)
    return ApiResponse(data=WorkflowRead.model_validate(wf), message="Workflow paused successfully")


@router.post("/workflows/{id}/archive", response_model=ApiResponse[WorkflowRead])
async def archive_workflow(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_ARCHIVE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowRead]:
    """Archive a workflow definition permanently."""
    wf = await WorkflowService.archive_workflow(db, tenant.tenant_id, id, actor_id=current_user.id)
    return ApiResponse(data=WorkflowRead.model_validate(wf), message="Workflow archived successfully")


@router.get("/workflows/{id}/versions", response_model=ApiResponse[list[WorkflowVersionRead]])
async def get_workflow_versions(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[WorkflowVersionRead]]:
    """Retrieve full immutable version history of a workflow."""
    wf = await WorkflowService.get_workflow(db, tenant.tenant_id, id)
    versions = [WorkflowVersionRead.model_validate(v) for v in sorted(wf.versions, key=lambda x: x.version)]
    return ApiResponse(data=versions, message=f"Retrieved {len(versions)} versions")


# =============================================================================
# 3. WORKFLOW EXECUTION & TRACKING
# =============================================================================

@router.post("/workflows/{id}/execute", response_model=ApiResponse[WorkflowExecutionRead])
async def execute_workflow_manually(
    id: UUID,
    payload: WorkflowManualExecutionRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_EXECUTE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowExecutionRead]:
    """Trigger manual execution of an active workflow with optional input context."""
    execution = await WorkflowService.execute_workflow(
        db=db,
        tenant_id=tenant.tenant_id,
        workflow_id=id,
        trigger_type=WorkflowTriggerType.MANUAL,
        trigger_reference=f"manual:{current_user.id}",
        input_context=payload.input_context,
        actor_id=current_user.id,
        correlation_id=payload.correlation_id,
    )
    return ApiResponse(
        data=WorkflowExecutionRead.model_validate(execution),
        message=f"Workflow execution completed with status '{execution.status}'"
    )


@router.get("/workflows/{id}/executions", response_model=ApiResponse[list[WorkflowExecutionRead]])
async def list_workflow_executions(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOW_EXECUTIONS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by execution status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ApiResponse[list[WorkflowExecutionRead]]:
    """List execution history for a specific workflow."""
    executions, total = await WorkflowService.list_executions(
        db=db,
        tenant_id=tenant.tenant_id,
        workflow_id=id,
        status=status,
        limit=limit,
        offset=offset,
    )
    result = [WorkflowExecutionRead.model_validate(e) for e in executions]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} executions")


@router.get("/workflow-executions", response_model=ApiResponse[list[WorkflowExecutionRead]])
async def list_all_executions(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOW_EXECUTIONS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by execution status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ApiResponse[list[WorkflowExecutionRead]]:
    """List all workflow executions across the tenant."""
    executions, total = await WorkflowService.list_executions(
        db=db,
        tenant_id=tenant.tenant_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    result = [WorkflowExecutionRead.model_validate(e) for e in executions]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} executions")


@router.get("/workflow-executions/{id}", response_model=ApiResponse[WorkflowExecutionRead])
async def get_execution_detail(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOW_EXECUTIONS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowExecutionRead]:
    """Fetch execution details including individual step statuses, outputs, and errors."""
    execution = await WorkflowService.get_execution(db, tenant.tenant_id, id)
    return ApiResponse(
        data=WorkflowExecutionRead.model_validate(execution),
        message="Workflow execution retrieved successfully"
    )


@router.post("/workflow-executions/{id}/retry", response_model=ApiResponse[WorkflowExecutionRead])
async def retry_execution(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_RETRY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowExecutionRead]:
    """Retry a failed workflow execution under audit tracking."""
    execution = await WorkflowService.retry_execution(
        db=db,
        tenant_id=tenant.tenant_id,
        execution_id=id,
        actor_id=current_user.id,
    )
    return ApiResponse(
        data=WorkflowExecutionRead.model_validate(execution),
        message=f"Execution retry finished with status '{execution.status}'"
    )


@router.post("/workflow-executions/{id}/cancel", response_model=ApiResponse[WorkflowExecutionRead])
async def cancel_execution(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_CANCEL))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowExecutionRead]:
    """Cancel an active or queued workflow execution."""
    execution = await WorkflowService.cancel_execution(
        db=db,
        tenant_id=tenant.tenant_id,
        execution_id=id,
        actor_id=current_user.id,
    )
    return ApiResponse(
        data=WorkflowExecutionRead.model_validate(execution),
        message="Execution successfully cancelled"
    )

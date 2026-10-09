"""Enterprise Workflow, Case Management & Human-in-the-Loop Operations API (Step 25)."""

from math import ceil
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    CASES_CLOSE,
    CASES_COMMENT,
    CASES_CREATE,
    CASES_READ,
    CASES_REOPEN,
    CASES_RESOLVE,
    CASES_UPDATE,
    QUEUES_MANAGE,
    QUEUES_READ,
    SLA_POLICIES_MANAGE,
    SLA_POLICIES_READ,
    TASKS_CLAIM,
    TASKS_COMPLETE,
    TASKS_DELEGATE,
    TASKS_READ,
    TASKS_REASSIGN,
    TASKS_RELEASE,
    WORKFLOWS_TRANSITION,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.case_management import (
    CaseAnalyticsMetrics,
    CaseAttachmentCreate,
    CaseAttachmentResponse,
    CaseCommentCreate,
    CaseCommentResponse,
    CaseCreate,
    CaseDetailResponse,
    CaseRelationshipCreate,
    CaseRelationshipResponse,
    CaseReopenRequest,
    CaseResolveRequest,
    CaseResponse,
    CaseTimelineEventResponse,
    CaseTypeCreate,
    CaseTypeResponse,
    CaseTypeUpdate,
    CaseUpdate,
    QueueMemberCreate,
    QueueMemberResponse,
    SlaPolicyCreate,
    SlaPolicyResponse,
    SlaPolicyUpdate,
    TaskClaimResponse,
    TaskCompleteRequest,
    TaskCreate,
    TaskDelegationCreate,
    TaskDelegationResponse,
    TaskDetailResponse,
    TaskReassignRequest,
    TaskReleaseRequest,
    TaskResponse,
    WorkflowInstanceTransitionRequest,
    WorkflowInstanceTransitionResponse,
    WorkQueueCreate,
    WorkQueueResponse,
    WorkQueueUpdate,
)
from app.schemas.common import ApiResponse, PaginatedMeta, PaginatedResponse
from app.services.case_service import CaseService
from app.services.sla_service import SlaService
from app.services.task_service import TaskService

router = APIRouter(tags=["Case Management & HITL Operations"])


# =============================================================================
# 1. CASE ANALYTICS (Must precede /{id})
# =============================================================================


@router.get("/cases/analytics", response_model=ApiResponse[CaseAnalyticsMetrics])
async def get_case_analytics(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseAnalyticsMetrics]:
    """Retrieve operational case performance and SLA metrics for the tenant."""
    service = CaseService(db)
    metrics = await service.get_analytics(tenant.tenant_id)
    return ApiResponse(
        data=CaseAnalyticsMetrics.model_validate(metrics),
        message="Case analytics retrieved successfully",
    )


# =============================================================================
# 2. CASE TYPES
# =============================================================================


@router.get("/case-types", response_model=ApiResponse[list[CaseTypeResponse]])
async def list_case_types(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    module: str | None = Query(None, description="Filter by operational module"),
    is_active: bool | None = Query(None, description="Filter by active status"),
) -> ApiResponse[list[CaseTypeResponse]]:
    """List configurable case types available for the tenant."""
    service = CaseService(db)
    types = await service.list_case_types(tenant.tenant_id, module=module, is_active=is_active)
    result = [CaseTypeResponse.model_validate(t) for t in types]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} case types")


@router.post(
    "/case-types", response_model=ApiResponse[CaseTypeResponse], status_code=status.HTTP_201_CREATED
)
async def create_case_type(
    payload: CaseTypeCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(QUEUES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseTypeResponse]:
    """Create a new tenant-scoped case classification type."""
    service = CaseService(db)
    ct = await service.create_case_type(tenant.tenant_id, payload, actor_id=current_user.id)
    return ApiResponse(
        data=CaseTypeResponse.model_validate(ct), message="Case type created successfully"
    )


@router.patch("/case-types/{id}", response_model=ApiResponse[CaseTypeResponse])
async def update_case_type(
    id: UUID,
    payload: CaseTypeUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(QUEUES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseTypeResponse]:
    """Update a case classification type."""
    service = CaseService(db)
    ct = await service.update_case_type(tenant.tenant_id, id, payload)
    return ApiResponse(
        data=CaseTypeResponse.model_validate(ct), message="Case type updated successfully"
    )


# =============================================================================
# 3. WORK QUEUES & MEMBERS
# =============================================================================


@router.get("/queues", response_model=ApiResponse[list[WorkQueueResponse]])
async def list_work_queues(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(QUEUES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    module: str | None = Query(None, description="Filter by module"),
    is_active: bool | None = Query(None, description="Filter by active status"),
) -> ApiResponse[list[WorkQueueResponse]]:
    """List operational work queues for the tenant."""
    service = CaseService(db)
    queues = await service.list_work_queues(tenant.tenant_id, module=module, is_active=is_active)
    result = [WorkQueueResponse.model_validate(q) for q in queues]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} work queues")


@router.post(
    "/queues", response_model=ApiResponse[WorkQueueResponse], status_code=status.HTTP_201_CREATED
)
async def create_work_queue(
    payload: WorkQueueCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(QUEUES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkQueueResponse]:
    """Create a new operational work queue."""
    service = CaseService(db)
    q = await service.create_work_queue(tenant.tenant_id, payload, actor_id=current_user.id)
    return ApiResponse(
        data=WorkQueueResponse.model_validate(q), message="Work queue created successfully"
    )


@router.get("/queues/{id}", response_model=ApiResponse[WorkQueueResponse])
async def get_work_queue(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(QUEUES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkQueueResponse]:
    """Retrieve work queue details and assigned operators."""
    service = CaseService(db)
    q = await service.get_work_queue(tenant.tenant_id, id)
    return ApiResponse(
        data=WorkQueueResponse.model_validate(q), message="Work queue retrieved successfully"
    )


@router.patch("/queues/{id}", response_model=ApiResponse[WorkQueueResponse])
async def update_work_queue(
    id: UUID,
    payload: WorkQueueUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(QUEUES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkQueueResponse]:
    """Update work queue configuration and capacity."""
    service = CaseService(db)
    q = await service.update_work_queue(tenant.tenant_id, id, payload, actor_id=current_user.id)
    return ApiResponse(
        data=WorkQueueResponse.model_validate(q), message="Work queue updated successfully"
    )


@router.post(
    "/queues/{id}/members",
    response_model=ApiResponse[QueueMemberResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_queue_member(
    id: UUID,
    payload: QueueMemberCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(QUEUES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[QueueMemberResponse]:
    """Assign an operator or supervisor to a work queue."""
    service = CaseService(db)
    member = await service.add_queue_member(tenant.tenant_id, id, payload, actor_id=current_user.id)
    return ApiResponse(
        data=QueueMemberResponse.model_validate(member), message="Queue member added successfully"
    )


@router.delete("/queues/{id}/members/{user_id}", response_model=ApiResponse[dict[str, Any]])
async def remove_queue_member(
    id: UUID,
    user_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(QUEUES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, Any]]:
    """Remove an operator from a work queue."""
    service = CaseService(db)
    removed = await service.remove_queue_member(
        tenant.tenant_id, id, user_id, actor_id=current_user.id
    )
    return ApiResponse(data={"removed": removed}, message="Queue member removed successfully")


# =============================================================================
# 4. CASES
# =============================================================================


@router.get("/cases", response_model=PaginatedResponse[CaseResponse])
async def list_cases(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    queue_id: UUID | None = Query(None, description="Filter by assigned queue"),
    owner_id: UUID | None = Query(None, description="Filter by case owner"),
    case_type_code: str | None = Query(None, description="Filter by case type"),
    subject_type: str | None = Query(None, description="Filter by subject entity type"),
    subject_id: UUID | None = Query(None, description="Filter by subject entity id"),
    search: str | None = Query(None, description="Free text search on title/case number"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[CaseResponse]:
    """List operational cases under tenant boundaries and pagination."""
    service = CaseService(db)
    offset = (page - 1) * page_size
    cases, total = await service.list_cases(
        tenant_id=tenant.tenant_id,
        status=status,
        priority=priority,
        queue_id=queue_id,
        owner_id=owner_id,
        case_type_code=case_type_code,
        subject_entity_type=subject_type,
        subject_entity_id=subject_id,
        search=search,
        limit=page_size,
        offset=offset,
    )
    items = [CaseResponse.model_validate(c) for c in cases]
    return PaginatedResponse(
        data=items,
        meta=PaginatedMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if page_size else 1,
        ),
    )


@router.post(
    "/cases", response_model=ApiResponse[CaseResponse], status_code=status.HTTP_201_CREATED
)
async def create_case(
    payload: CaseCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseResponse]:
    """Create a new operational case with concurrency-safe sequence numbering."""
    service = CaseService(db)
    case = await service.create_case(tenant.tenant_id, payload, actor_id=current_user.id)
    return ApiResponse(data=CaseResponse.model_validate(case), message="Case created successfully")


@router.get("/cases/{id}", response_model=ApiResponse[CaseDetailResponse])
async def get_case(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseDetailResponse]:
    """Retrieve full case operational details including tasks, comments, and timeline."""
    service = CaseService(db)
    case = await service.get_case(tenant.tenant_id, id)
    return ApiResponse(
        data=CaseDetailResponse.model_validate(case), message="Case retrieved successfully"
    )


@router.patch("/cases/{id}", response_model=ApiResponse[CaseResponse])
async def update_case(
    id: UUID,
    payload: CaseUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseResponse]:
    """Update case priority, assignment, or metadata."""
    service = CaseService(db)
    case = await service.update_case(tenant.tenant_id, id, payload, actor_id=current_user.id)
    return ApiResponse(data=CaseResponse.model_validate(case), message="Case updated successfully")


@router.post("/cases/{id}/resolve", response_model=ApiResponse[CaseResponse])
async def resolve_case(
    id: UUID,
    payload: CaseResolveRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_RESOLVE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseResponse]:
    """Resolve an operational case with justification after verifying task completion."""
    service = CaseService(db)
    case = await service.resolve_case(tenant.tenant_id, id, payload, actor_id=current_user.id)
    return ApiResponse(data=CaseResponse.model_validate(case), message="Case resolved successfully")


@router.post("/cases/{id}/close", response_model=ApiResponse[CaseResponse])
async def close_case(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_CLOSE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    closure_notes: str | None = None,
) -> ApiResponse[CaseResponse]:
    """Formally close an operational case."""
    service = CaseService(db)
    case = await service.close_case(
        tenant.tenant_id, id, closure_notes=closure_notes, actor_id=current_user.id
    )
    return ApiResponse(data=CaseResponse.model_validate(case), message="Case closed successfully")


@router.post("/cases/{id}/reopen", response_model=ApiResponse[CaseResponse])
async def reopen_case(
    id: UUID,
    payload: CaseReopenRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_REOPEN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseResponse]:
    """Reopen a previously resolved or closed case with justification."""
    service = CaseService(db)
    case = await service.reopen_case(
        tenant.tenant_id, id, payload.reopen_reason, actor_id=current_user.id
    )
    return ApiResponse(data=CaseResponse.model_validate(case), message="Case reopened successfully")


@router.get("/cases/{id}/timeline", response_model=ApiResponse[list[CaseTimelineEventResponse]])
async def get_case_timeline(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[CaseTimelineEventResponse]]:
    """Retrieve unified operational lifecycle timeline for a case."""
    service = CaseService(db)
    events = await service.get_timeline(tenant.tenant_id, id)
    result = [CaseTimelineEventResponse.model_validate(e) for e in events]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} timeline events")


@router.get("/cases/{id}/comments", response_model=ApiResponse[list[CaseCommentResponse]])
async def list_case_comments(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[CaseCommentResponse]]:
    """List case comments filtered by caller visibility permissions."""
    service = CaseService(db)
    comments = await service.list_comments(tenant.tenant_id, id, user_role=None)
    result = [CaseCommentResponse.model_validate(c) for c in comments]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} comments")


@router.post(
    "/cases/{id}/comments",
    response_model=ApiResponse[CaseCommentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_case_comment(
    id: UUID,
    payload: CaseCommentCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_COMMENT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseCommentResponse]:
    """Post an operational note or comment on a case."""
    service = CaseService(db)
    comment = await service.add_comment(tenant.tenant_id, id, payload, author_id=current_user.id)
    return ApiResponse(
        data=CaseCommentResponse.model_validate(comment), message="Comment posted successfully"
    )


@router.get("/cases/{id}/attachments", response_model=ApiResponse[list[CaseAttachmentResponse]])
async def list_case_attachments(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[CaseAttachmentResponse]]:
    """List document attachments linked to a case."""
    service = CaseService(db)
    attachments = await service.list_attachments(tenant.tenant_id, id)
    result = [CaseAttachmentResponse.model_validate(a) for a in attachments]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} attachments")


@router.post(
    "/cases/{id}/attachments",
    response_model=ApiResponse[CaseAttachmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_case_attachment(
    id: UUID,
    payload: CaseAttachmentCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseAttachmentResponse]:
    """Attach an existing storage document to an operational case."""
    service = CaseService(db)
    attachment = await service.add_attachment(
        tenant.tenant_id, id, payload, uploader_id=current_user.id
    )
    return ApiResponse(
        data=CaseAttachmentResponse.model_validate(attachment),
        message="Document attached successfully",
    )


@router.get("/cases/{id}/relationships", response_model=ApiResponse[list[CaseRelationshipResponse]])
async def list_case_relationships(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[CaseRelationshipResponse]]:
    """List established relationships linking this case to others."""
    service = CaseService(db)
    relationships = await service.list_relationships(tenant.tenant_id, id)
    result = [CaseRelationshipResponse.model_validate(r) for r in relationships]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} relationships")


@router.post(
    "/cases/{id}/relationships",
    response_model=ApiResponse[CaseRelationshipResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_case_relationship(
    id: UUID,
    payload: CaseRelationshipCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CaseRelationshipResponse]:
    """Establish an operational link (e.g. duplicate, dependency, parent-child)."""
    service = CaseService(db)
    rel = await service.create_relationship(tenant.tenant_id, id, payload, actor_id=current_user.id)
    return ApiResponse(
        data=CaseRelationshipResponse.model_validate(rel),
        message="Case relationship created successfully",
    )


# =============================================================================
# 5. HUMAN TASKS & DECISIONS
# =============================================================================


@router.get("/tasks", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(TASKS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    case_id: UUID | None = Query(None, description="Filter by case"),
    status: str | None = Query(None, description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    assigned_user_id: UUID | None = Query(None, description="Filter by assigned user"),
    assigned_queue_id: UUID | None = Query(None, description="Filter by assigned queue"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[TaskResponse]:
    """List human tasks across queues and operators."""
    service = TaskService(db)
    offset = (page - 1) * page_size
    tasks, total = await service.list_tasks(
        tenant_id=tenant.tenant_id,
        case_id=case_id,
        status=status,
        priority=priority,
        assigned_user_id=assigned_user_id,
        assigned_queue_id=assigned_queue_id,
        limit=page_size,
        offset=offset,
    )
    items = [TaskResponse.model_validate(t) for t in tasks]
    return PaginatedResponse(
        data=items,
        meta=PaginatedMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if page_size else 1,
        ),
    )


@router.post(
    "/tasks", response_model=ApiResponse[TaskResponse], status_code=status.HTTP_201_CREATED
)
async def create_task(
    payload: TaskCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CASES_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TaskResponse]:
    """Create a human task linked to an operational case."""
    service = TaskService(db)
    task = await service.create_task(tenant.tenant_id, payload, actor_id=current_user.id)
    return ApiResponse(data=TaskResponse.model_validate(task), message="Task created successfully")


@router.get("/tasks/{id}", response_model=ApiResponse[TaskDetailResponse])
async def get_task(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(TASKS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TaskDetailResponse]:
    """Retrieve task details, recorded decisions, and comments."""
    service = TaskService(db)
    task = await service.get_task(tenant.tenant_id, id)
    return ApiResponse(
        data=TaskDetailResponse.model_validate(task), message="Task retrieved successfully"
    )


@router.post("/tasks/{id}/claim", response_model=ApiResponse[TaskClaimResponse])
async def claim_task(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(TASKS_CLAIM))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TaskClaimResponse]:
    """Exclusively claim an unassigned or queue task under concurrency protection."""
    service = TaskService(db)
    task = await service.claim_task(tenant.tenant_id, id, user_id=current_user.id)
    return ApiResponse(
        data=TaskClaimResponse(
            task=TaskResponse.model_validate(task),
            claimed_by_id=current_user.id,
            claimed_at=task.claimed_at or task.updated_at,
        ),
        message="Task claimed successfully",
    )


@router.post("/tasks/{id}/release", response_model=ApiResponse[TaskResponse])
async def release_task(
    id: UUID,
    payload: TaskReleaseRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(TASKS_RELEASE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TaskResponse]:
    """Release a claimed task back to the pending queue."""
    service = TaskService(db)
    task = await service.release_task(
        tenant.tenant_id, id, user_id=current_user.id, reason=payload.reason
    )
    return ApiResponse(data=TaskResponse.model_validate(task), message="Task released successfully")


@router.post("/tasks/{id}/reassign", response_model=ApiResponse[TaskResponse])
async def reassign_task(
    id: UUID,
    payload: TaskReassignRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(TASKS_REASSIGN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TaskResponse]:
    """Reassign a task to another operator or work queue."""
    service = TaskService(db)
    task = await service.reassign_task(tenant.tenant_id, id, actor_id=current_user.id, dto=payload)
    return ApiResponse(
        data=TaskResponse.model_validate(task), message="Task reassigned successfully"
    )


@router.post("/tasks/{id}/complete", response_model=ApiResponse[TaskResponse])
async def complete_task(
    id: UUID,
    payload: TaskCompleteRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(TASKS_COMPLETE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TaskResponse]:
    """Record authoritative human decision and complete human task."""
    service = TaskService(db)
    task = await service.complete_task(tenant.tenant_id, id, actor_id=current_user.id, dto=payload)
    return ApiResponse(
        data=TaskResponse.model_validate(task), message="Task completed successfully"
    )


# =============================================================================
# 6. TASK DELEGATIONS
# =============================================================================


@router.get("/tasks/delegations", response_model=ApiResponse[list[TaskDelegationResponse]])
async def list_delegations(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(TASKS_DELEGATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_active: bool | None = Query(None, description="Filter active delegations"),
) -> ApiResponse[list[TaskDelegationResponse]]:
    """List operational delegations for the current operator or tenant."""
    service = TaskService(db)
    delegations = await service.list_delegations(
        tenant.tenant_id, user_id=current_user.id, is_active=is_active
    )
    result = [TaskDelegationResponse.model_validate(d) for d in delegations]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} delegations")


@router.post(
    "/tasks/delegations",
    response_model=ApiResponse[TaskDelegationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_delegation(
    payload: TaskDelegationCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(TASKS_DELEGATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TaskDelegationResponse]:
    """Create a temporary, time-bounded operational authority delegation."""
    service = TaskService(db)
    delegation = await service.create_delegation(
        tenant.tenant_id, delegator_id=current_user.id, dto=payload
    )
    return ApiResponse(
        data=TaskDelegationResponse.model_validate(delegation),
        message="Delegation created successfully",
    )


# =============================================================================
# 7. SLA POLICIES
# =============================================================================


@router.get("/sla-policies", response_model=ApiResponse[list[SlaPolicyResponse]])
async def list_sla_policies(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(SLA_POLICIES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    module: str | None = Query(None, description="Filter by module"),
    is_active: bool | None = Query(None, description="Filter by active status"),
) -> ApiResponse[list[SlaPolicyResponse]]:
    """List configured Service Level Agreement duration and escalation policies."""
    service = SlaService(db)
    policies = await service.list_sla_policies(tenant.tenant_id, module=module, is_active=is_active)
    result = [SlaPolicyResponse.model_validate(p) for p in policies]
    return ApiResponse(data=result, message=f"Retrieved {len(result)} SLA policies")


@router.post(
    "/sla-policies",
    response_model=ApiResponse[SlaPolicyResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_sla_policy(
    payload: SlaPolicyCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(SLA_POLICIES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SlaPolicyResponse]:
    """Create a new operational SLA policy."""
    service = SlaService(db)
    policy = await service.create_sla_policy(tenant.tenant_id, payload, actor_id=current_user.id)
    return ApiResponse(
        data=SlaPolicyResponse.model_validate(policy), message="SLA policy created successfully"
    )


@router.patch("/sla-policies/{id}", response_model=ApiResponse[SlaPolicyResponse])
async def update_sla_policy(
    id: UUID,
    payload: SlaPolicyUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(SLA_POLICIES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SlaPolicyResponse]:
    """Update SLA target duration, thresholds, or escalation targets."""
    service = SlaService(db)
    policy = await service.update_sla_policy(
        tenant.tenant_id, id, payload, actor_id=current_user.id
    )
    return ApiResponse(
        data=SlaPolicyResponse.model_validate(policy), message="SLA policy updated successfully"
    )


# =============================================================================
# 8. WORKFLOW INSTANCE HITL TRANSITIONS
# =============================================================================


@router.post(
    "/workflow-instances/{id}/transition",
    response_model=ApiResponse[WorkflowInstanceTransitionResponse],
)
async def transition_workflow_instance(
    id: UUID,
    payload: WorkflowInstanceTransitionRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(WORKFLOWS_TRANSITION))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkflowInstanceTransitionResponse]:
    """Bridge human decision into Step 17 workflow execution engine."""
    service = CaseService(db)
    res = await service.transition_workflow_instance(
        tenant_id=tenant.tenant_id,
        execution_id=id,
        action=payload.action,
        reason=payload.reason,
        target_step_key=payload.target_step_key,
        task_id=payload.task_id,
        actor_id=current_user.id,
        context_updates=payload.context_updates,
    )
    return ApiResponse(
        data=WorkflowInstanceTransitionResponse.model_validate(res),
        message=f"Workflow execution transitioned with action '{payload.action}'",
    )

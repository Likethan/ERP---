"""CampusOS Enterprise Student Affairs, Grievance Redressal & Disciplinary API Router (Step 58).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    SA_APPEAL_FILE,
    SA_APPEAL_REVIEW,
    SA_CASE_ASSIGN,
    SA_CASE_READ_ASSIGNED,
    SA_CASE_READ_OWN,
    SA_CASE_SUBMIT_OWN,
    SA_CASE_UPDATE,
    SA_CATEGORY_MANAGE,
    SA_CATEGORY_READ,
    SA_COMMUNICATION_SEND,
    SA_DISCIPLINARY_MANAGE,
    SA_ESCALATION_MANAGE,
    SA_EVIDENCE_REDACT,
    SA_EVIDENCE_UPLOAD,
    SA_MEETING_MANAGE,
    SA_OFFICE_MANAGE,
    SA_OFFICE_READ,
    SA_REPORT_READ,
    SA_RESOLUTION_APPROVE,
    SA_RESOLUTION_PROPOSE,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.models.student_affairs import CaseAuditAction
from app.schemas.student_affairs import (
    AppealRecordCreate,
    AppealRecordResponse,
    AppealReviewDecision,
    CaseCommunicationCreate,
    CaseCommunicationResponse,
    CaseEscalationCreate,
    CaseEscalationResponse,
    CaseEvidenceRedact,
    CaseEvidenceResponse,
    CaseEvidenceUpload,
    CaseMeetingCreate,
    CaseMeetingResponse,
    CaseMeetingUpdate,
    CaseParticipantResponse,
    CaseReassignRequest,
    ConflictDeclaration,
    DisciplinaryFindingsRecord,
    DisciplinaryProceedingCreate,
    DisciplinaryProceedingResponse,
    DisciplinarySanctionApprove,
    GrievanceCaseResponse,
    GrievanceCaseSubmit,
    GrievanceCaseUpdate,
    GrievanceCategoryCreate,
    GrievanceCategoryResponse,
    ResolutionActionCreate,
    ResolutionActionResponse,
    ResolutionActionUpdate,
    StudentAffairsDashboardTelemetry,
    StudentAffairsOfficeCreate,
    StudentAffairsOfficeResponse,
    StudentAffairsPolicyConfigResponse,
)
from app.services.student_affairs_service import StudentAffairsService

student_affairs_router = APIRouter(prefix="/student-affairs", tags=["Student Affairs & Grievance Redressal"])


# =============================================================================
# 1. OFFICES & CATEGORIES
# =============================================================================


@student_affairs_router.get("/offices", response_model=list[StudentAffairsOfficeResponse])
async def list_offices(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_OFFICE_READ))],
) -> list[StudentAffairsOfficeResponse]:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.list_offices()


@student_affairs_router.post("/offices", response_model=StudentAffairsOfficeResponse, status_code=status.HTTP_201_CREATED)
async def create_office(
    data: StudentAffairsOfficeCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_OFFICE_MANAGE))],
) -> StudentAffairsOfficeResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.create_office(data.model_dump())


@student_affairs_router.get("/categories", response_model=list[GrievanceCategoryResponse])
async def list_categories(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_CATEGORY_READ))],
    is_active: bool = Query(True),
) -> list[GrievanceCategoryResponse]:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.list_categories(is_active_only=is_active)


@student_affairs_router.post("/categories", response_model=GrievanceCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: GrievanceCategoryCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_CATEGORY_MANAGE))],
) -> GrievanceCategoryResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.create_category(data.model_dump())


# =============================================================================
# 2. CASES
# =============================================================================


@student_affairs_router.post("/cases", response_model=GrievanceCaseResponse, status_code=status.HTTP_201_CREATED)
async def submit_case(
    data: GrievanceCaseSubmit,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_CASE_SUBMIT_OWN))],
) -> GrievanceCaseResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    name = f"{user.first_name} {user.last_name}" if user else "Authenticated Submitter"
    return await service.submit_case(data, user_id=user.id, user_display_name=name)


@student_affairs_router.get("/cases", response_model=list[GrievanceCaseResponse])
async def list_cases(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_CASE_READ_ASSIGNED))],
    case_type: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    priority_filter: str | None = Query(None, alias="priority"),
    assigned_officer_id: UUID | None = None,
) -> list[GrievanceCaseResponse]:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.list_cases(
        case_type=case_type,
        status_filter=status_filter,
        priority_filter=priority_filter,
        assigned_officer_id=assigned_officer_id,
    )


@student_affairs_router.get("/cases/my", response_model=list[GrievanceCaseResponse])
async def list_my_cases(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_CASE_READ_OWN))],
) -> list[GrievanceCaseResponse]:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.list_cases(submitter_user_id=user.id)


@student_affairs_router.get("/cases/{case_id}", response_model=GrievanceCaseResponse)
async def get_case(
    case_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> GrievanceCaseResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    case = await service.get_case(case_id)
    await service.log_access_audit(case.id, user.id, CaseAuditAction.VIEWED_CASE, "Viewed general case profile")
    return case


@student_affairs_router.patch("/cases/{case_id}", response_model=GrievanceCaseResponse)
async def update_case(
    case_id: UUID,
    data: GrievanceCaseUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_CASE_UPDATE))],
) -> GrievanceCaseResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.update_case(case_id, data)


@student_affairs_router.post("/cases/{case_id}/assign", response_model=GrievanceCaseResponse)
async def assign_case(
    case_id: UUID,
    data: CaseReassignRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_CASE_ASSIGN))],
) -> GrievanceCaseResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.assign_case(case_id, data.new_officer_id, user.id, data.reason)


@student_affairs_router.post("/cases/{case_id}/conflict", response_model=CaseParticipantResponse)
async def declare_conflict(
    case_id: UUID,
    data: ConflictDeclaration,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> CaseParticipantResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.declare_conflict(case_id, user.id, data)


# =============================================================================
# 3. DISCIPLINARY PROCEEDINGS
# =============================================================================


@student_affairs_router.post("/cases/{case_id}/disciplinary", response_model=DisciplinaryProceedingResponse, status_code=status.HTTP_201_CREATED)
async def create_disciplinary_proceeding(
    case_id: UUID,
    data: DisciplinaryProceedingCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_DISCIPLINARY_MANAGE))],
) -> DisciplinaryProceedingResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.create_disciplinary_proceeding(case_id, data)


@student_affairs_router.post("/cases/{case_id}/disciplinary/findings", response_model=DisciplinaryProceedingResponse)
async def record_disciplinary_findings(
    case_id: UUID,
    data: DisciplinaryFindingsRecord,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_DISCIPLINARY_MANAGE))],
) -> DisciplinaryProceedingResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.record_findings(case_id, data)


@student_affairs_router.post("/cases/{case_id}/disciplinary/sanction", response_model=DisciplinaryProceedingResponse)
async def approve_disciplinary_sanction(
    case_id: UUID,
    data: DisciplinarySanctionApprove,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_DISCIPLINARY_MANAGE))],
) -> DisciplinaryProceedingResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.approve_sanction(case_id, data)


# =============================================================================
# 4. EVIDENCE & REDACTIONS
# =============================================================================


@student_affairs_router.post("/cases/{case_id}/evidence", response_model=CaseEvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: UUID,
    data: CaseEvidenceUpload,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_EVIDENCE_UPLOAD))],
) -> CaseEvidenceResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.upload_evidence(case_id, data, user.id)


@student_affairs_router.post("/evidence/{evidence_id}/redact", response_model=CaseEvidenceResponse, status_code=status.HTTP_201_CREATED)
async def redact_evidence(
    evidence_id: UUID,
    data: CaseEvidenceRedact,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_EVIDENCE_REDACT))],
) -> CaseEvidenceResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.redact_evidence(evidence_id, data, user.id)


# =============================================================================
# 5. MEETINGS & HEARINGS
# =============================================================================


@student_affairs_router.post("/cases/{case_id}/meetings", response_model=CaseMeetingResponse, status_code=status.HTTP_201_CREATED)
async def schedule_meeting(
    case_id: UUID,
    data: CaseMeetingCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_MEETING_MANAGE))],
) -> CaseMeetingResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.schedule_meeting(case_id, data)


@student_affairs_router.patch("/meetings/{meeting_id}", response_model=CaseMeetingResponse)
async def update_meeting(
    meeting_id: UUID,
    data: CaseMeetingUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_MEETING_MANAGE))],
) -> CaseMeetingResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.update_meeting(meeting_id, data)


# =============================================================================
# 6. RESOLUTION ACTIONS & REMEDIES
# =============================================================================


@student_affairs_router.post("/cases/{case_id}/resolutions", response_model=ResolutionActionResponse, status_code=status.HTTP_201_CREATED)
async def add_resolution_action(
    case_id: UUID,
    data: ResolutionActionCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_RESOLUTION_PROPOSE))],
) -> ResolutionActionResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.add_resolution_action(case_id, data)


@student_affairs_router.patch("/resolutions/{action_id}", response_model=ResolutionActionResponse)
async def update_resolution_action(
    action_id: UUID,
    data: ResolutionActionUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_RESOLUTION_APPROVE))],
) -> ResolutionActionResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.update_resolution_action(action_id, data)


# =============================================================================
# 7. APPEALS
# =============================================================================


@student_affairs_router.post("/cases/{case_id}/appeals", response_model=AppealRecordResponse, status_code=status.HTTP_201_CREATED)
async def file_appeal(
    case_id: UUID,
    data: AppealRecordCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_APPEAL_FILE))],
) -> AppealRecordResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.file_appeal(case_id, data, user.id)


@student_affairs_router.post("/appeals/{appeal_id}/review", response_model=AppealRecordResponse)
async def review_appeal(
    appeal_id: UUID,
    data: AppealReviewDecision,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_APPEAL_REVIEW))],
) -> AppealRecordResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.review_appeal(appeal_id, data)


# =============================================================================
# 8. COMMUNICATIONS & ESCALATIONS
# =============================================================================


@student_affairs_router.post("/cases/{case_id}/communications", response_model=CaseCommunicationResponse, status_code=status.HTTP_201_CREATED)
async def send_communication(
    case_id: UUID,
    data: CaseCommunicationCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_COMMUNICATION_SEND))],
) -> CaseCommunicationResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    name = f"{user.first_name} {user.last_name}" if user else "Case Participant"
    return await service.send_communication(case_id, data, user.id, name)


@student_affairs_router.post("/cases/{case_id}/escalate", response_model=CaseEscalationResponse, status_code=status.HTTP_201_CREATED)
async def escalate_case(
    case_id: UUID,
    data: CaseEscalationCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_ESCALATION_MANAGE))],
) -> CaseEscalationResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.escalate_case(case_id, data, user.id)


# =============================================================================
# 9. TELEMETRY & POLICY CONFIG
# =============================================================================


@student_affairs_router.get("/telemetry", response_model=StudentAffairsDashboardTelemetry)
async def get_dashboard_telemetry(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SA_REPORT_READ))],
) -> StudentAffairsDashboardTelemetry:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    data = await service.get_dashboard_telemetry()
    return StudentAffairsDashboardTelemetry(**data)


@student_affairs_router.get("/policy-config", response_model=StudentAffairsPolicyConfigResponse)
async def get_policy_config(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> StudentAffairsPolicyConfigResponse:
    service = StudentAffairsService(db, tenant_ctx.tenant_id)
    return await service.get_or_create_policy_config()

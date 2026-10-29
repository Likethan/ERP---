"""Enterprise Institutional Legal Affairs, Contract Lifecycle, Policy Compliance & Institutional Risk Management API Router (Step 62).

CampusOS Identity: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    LEGAL_COMPLIANCE_MANAGE,
    LEGAL_COMPLIANCE_READ,
    LEGAL_CONTRACTS_EXECUTE,
    LEGAL_CONTRACTS_MANAGE,
    LEGAL_CONTRACTS_READ,
    LEGAL_MATTERS_MANAGE,
    LEGAL_MATTERS_READ,
    LEGAL_OBLIGATIONS_MANAGE,
    LEGAL_OBLIGATIONS_READ,
    LEGAL_OPERATIONS_READ,
    LEGAL_RISKS_MANAGE,
    LEGAL_RISKS_READ,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.legal import (
    ComplianceAssessRequest,
    ComplianceCreate,
    ComplianceResponse,
    ContractAmendmentCreate,
    ContractAmendmentResponse,
    ContractCreate,
    ContractExecutionConfirmRequest,
    ContractObligationCreate,
    ContractObligationResponse,
    ContractResponse,
    ContractTransitionRequest,
    ContractUpdate,
    LegalOperationsDashboardResponse,
    MatterCreate,
    MatterResponse,
    MatterUpdate,
    ObligationCompleteRequest,
    ObligationWaiveRequest,
    RenewalSweepResult,
    RiskAcceptRequest,
    RiskCreate,
    RiskResponse,
    RiskUpdate,
)
from app.services.legal_service import LegalService

legal_router = APIRouter(prefix="/legal-operations", tags=["Enterprise Legal Affairs & Contract Operations"])


# =============================================================================
# 1. OPERATIONS DASHBOARD & AUTOMATED SWEEPS
# =============================================================================


@legal_router.get(
    "/dashboard",
    response_model=LegalOperationsDashboardResponse,
    summary="Unified Institutional Legal Operations Dashboard",
)
async def get_legal_operations_dashboard(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_OPERATIONS_READ))],
) -> LegalOperationsDashboardResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.get_operations_dashboard(current_user)


@legal_router.post(
    "/renewals/sweep",
    response_model=RenewalSweepResult,
    summary="Execute scheduled contract renewal and deadline sweep",
)
async def execute_renewal_sweep(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_CONTRACTS_MANAGE))],
) -> RenewalSweepResult:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.execute_renewal_and_deadline_sweep()


# =============================================================================
# 2. CONTRACT LIFECYCLE MANAGEMENT
# =============================================================================


@legal_router.post(
    "/contracts",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create institutional contract draft",
)
async def create_contract(
    data: ContractCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_CONTRACTS_MANAGE))],
) -> ContractResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.create_contract(data, current_user)


@legal_router.get(
    "/contracts",
    response_model=list[ContractResponse],
    summary="List institutional contracts with filters",
)
async def list_contracts(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_CONTRACTS_READ))],
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    internal_owner_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ContractResponse]:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.list_contracts(
        status=status,
        category=category,
        department_id=department_id,
        internal_owner_id=internal_owner_id,
        search=search,
        limit=limit,
        offset=offset,
    )


@legal_router.get(
    "/contracts/{contract_id}",
    response_model=ContractResponse,
    summary="Get full contract 360 record with amendments and obligations",
)
async def get_contract(
    contract_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_CONTRACTS_READ))],
) -> ContractResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.get_contract(contract_id)


@legal_router.patch(
    "/contracts/{contract_id}",
    response_model=ContractResponse,
    summary="Update contract details",
)
async def update_contract(
    contract_id: UUID,
    data: ContractUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_CONTRACTS_MANAGE))],
) -> ContractResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.update_contract(contract_id, data, current_user)


@legal_router.post(
    "/contracts/{contract_id}/transition",
    response_model=ContractResponse,
    summary="Transition contract lifecycle state with review comments",
)
async def transition_contract(
    contract_id: UUID,
    request: ContractTransitionRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_CONTRACTS_READ))],
) -> ContractResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    user_perms = set(getattr(current_user, "permissions", []))
    return await service.transition_contract(contract_id, request, current_user, user_perms)


@legal_router.post(
    "/contracts/{contract_id}/execute",
    response_model=ContractResponse,
    summary="Record verified execution and external signature of contract",
)
async def confirm_contract_execution(
    contract_id: UUID,
    request: ContractExecutionConfirmRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_CONTRACTS_EXECUTE))],
) -> ContractResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    user_perms = set(getattr(current_user, "permissions", []))
    return await service.confirm_contract_execution(contract_id, request, current_user, user_perms)


@legal_router.post(
    "/contracts/{contract_id}/amendments",
    response_model=ContractAmendmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record contract amendment and version extension",
)
async def add_contract_amendment(
    contract_id: UUID,
    data: ContractAmendmentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_CONTRACTS_MANAGE))],
) -> ContractAmendmentResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.add_contract_amendment(contract_id, data, current_user)


# =============================================================================
# 3. CONTRACT OBLIGATIONS & COMMITMENTS
# =============================================================================


@legal_router.post(
    "/obligations",
    response_model=ContractObligationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create contract obligation or deliverable commitment",
)
async def create_obligation(
    data: ContractObligationCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_OBLIGATIONS_MANAGE))],
) -> ContractObligationResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.create_obligation(data, current_user)


@legal_router.get(
    "/obligations",
    response_model=list[ContractObligationResponse],
    summary="List contractual obligations",
)
async def list_obligations(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_OBLIGATIONS_READ))],
    contract_id: UUID | None = Query(default=None),
    responsible_owner_id: UUID | None = Query(default=None),
    accountable_department_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ContractObligationResponse]:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.list_obligations(
        contract_id=contract_id,
        responsible_owner_id=responsible_owner_id,
        accountable_department_id=accountable_department_id,
        status=status,
        overdue_only=overdue_only,
        limit=limit,
        offset=offset,
    )


@legal_router.post(
    "/obligations/{obligation_id}/complete",
    response_model=ContractObligationResponse,
    summary="Complete contractual obligation with evidence",
)
async def complete_obligation(
    obligation_id: UUID,
    request: ObligationCompleteRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_OBLIGATIONS_MANAGE))],
) -> ContractObligationResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.complete_obligation(obligation_id, request, current_user)


@legal_router.post(
    "/obligations/{obligation_id}/waive",
    response_model=ContractObligationResponse,
    summary="Formally waive contractual obligation with rationale",
)
async def waive_obligation(
    obligation_id: UUID,
    request: ObligationWaiveRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_OBLIGATIONS_MANAGE))],
) -> ContractObligationResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.waive_obligation(obligation_id, request, current_user)


# =============================================================================
# 4. RESTRICTED INSTITUTIONAL LEGAL MATTERS
# =============================================================================


@legal_router.post(
    "/matters",
    response_model=MatterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open restricted institutional legal matter",
)
async def create_matter(
    data: MatterCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_MATTERS_MANAGE))],
) -> MatterResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.create_matter(data, current_user)


@legal_router.get(
    "/matters",
    response_model=list[MatterResponse],
    summary="List authorized legal matters (confidential notes redacted in list view)",
)
async def list_matters(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_MATTERS_READ))],
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[MatterResponse]:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.list_matters(
        category=category,
        status=status,
        priority=priority,
        department_id=department_id,
        limit=limit,
        offset=offset,
    )


@legal_router.get(
    "/matters/{matter_id}",
    response_model=MatterResponse,
    summary="Get single legal matter with resource-level confidentiality checks",
)
async def get_matter(
    matter_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_MATTERS_READ))],
) -> MatterResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    user_perms = set(getattr(current_user, "permissions", []))
    return await service.get_matter(matter_id, current_user, user_perms)


@legal_router.patch(
    "/matters/{matter_id}",
    response_model=MatterResponse,
    summary="Update legal matter details, status, or resolution",
)
async def update_matter(
    matter_id: UUID,
    data: MatterUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_MATTERS_MANAGE))],
) -> MatterResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.update_matter(matter_id, data, current_user)


# =============================================================================
# 5. COMPLIANCE OBLIGATIONS & ASSESSMENTS
# =============================================================================


@legal_router.post(
    "/compliance",
    response_model=ComplianceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register statutory/accreditation compliance obligation",
)
async def create_compliance_obligation(
    data: ComplianceCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_COMPLIANCE_MANAGE))],
) -> ComplianceResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.create_compliance_obligation(data, current_user)


@legal_router.get(
    "/compliance",
    response_model=list[ComplianceResponse],
    summary="List institutional compliance obligations",
)
async def list_compliance_obligations(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_COMPLIANCE_READ))],
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ComplianceResponse]:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.list_compliance_obligations(
        category=category,
        status=status,
        department_id=department_id,
        limit=limit,
        offset=offset,
    )


@legal_router.post(
    "/compliance/{compliance_id}/assess",
    response_model=ComplianceResponse,
    summary="Perform compliance assessment and record corrective actions",
)
async def assess_compliance(
    compliance_id: UUID,
    request: ComplianceAssessRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_COMPLIANCE_MANAGE))],
) -> ComplianceResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.assess_compliance(compliance_id, request, current_user)


# =============================================================================
# 6. ENTERPRISE INSTITUTIONAL RISK REGISTER
# =============================================================================


@legal_router.post(
    "/risks",
    response_model=RiskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create enterprise institutional risk assessment",
)
async def create_risk(
    data: RiskCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_RISKS_MANAGE))],
) -> RiskResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.create_risk(data, current_user)


@legal_router.get(
    "/risks",
    response_model=list[RiskResponse],
    summary="List enterprise risks with 5x5 matrix scoring",
)
async def list_risks(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_RISKS_READ))],
    category: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    status: str | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[RiskResponse]:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.list_risks(
        category=category,
        risk_level=risk_level,
        status=status,
        department_id=department_id,
        limit=limit,
        offset=offset,
    )


@legal_router.patch(
    "/risks/{risk_id}",
    response_model=RiskResponse,
    summary="Update risk likelihood, impact, controls, or mitigation",
)
async def update_risk(
    risk_id: UUID,
    data: RiskUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_RISKS_MANAGE))],
) -> RiskResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.update_risk(risk_id, data, current_user)


@legal_router.post(
    "/risks/{risk_id}/accept",
    response_model=RiskResponse,
    summary="Formally record executive acceptance of residual risk",
)
async def accept_risk(
    risk_id: UUID,
    request: RiskAcceptRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(LEGAL_RISKS_MANAGE))],
) -> RiskResponse:
    service = LegalService(db, tenant_ctx.tenant_id)
    return await service.accept_risk(risk_id, request, current_user)

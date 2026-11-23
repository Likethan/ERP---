"""CampusOS Enterprise Asset Lifecycle, Maintenance, Facilities & Equipment Management REST API Router (Step 53).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    ASSETS_ASSIGN,
    ASSETS_AUDIT_MANAGE,
    ASSETS_CREATE,
    ASSETS_FINANCIAL_READ,
    ASSETS_INSPECTION_MANAGE,
    ASSETS_LIFECYCLE_MANAGE,
    ASSETS_MAINTENANCE_MANAGE,
    ASSETS_MAINTENANCE_READ,
    ASSETS_MANAGE,
    ASSETS_READ,
    ASSETS_REPORT_READ,
    ASSETS_RETIREMENT_APPROVE,
    ASSETS_RETIREMENT_REQUEST,
    ASSETS_TRANSFER,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.assets import (
    AssetAssignmentAcknowledgeRequest,
    AssetAssignmentCreate,
    AssetAssignmentResponse,
    AssetAssignmentReturnRequest,
    AssetAuditCampaignCreate,
    AssetAuditCampaignResponse,
    AssetAuditItemResponse,
    AssetAuditItemScanRequest,
    AssetBulkCreateRequest,
    AssetBulkCreateResponse,
    AssetCategoryCreate,
    AssetCategoryResponse,
    AssetCategoryUpdate,
    AssetCreate,
    AssetDepreciationScheduleResponse,
    AssetLifecycleEventResponse,
    AssetLifecycleTransitionRequest,
    AssetResponse,
    AssetRetirementApprovalRequest,
    AssetRetirementExecuteRequest,
    AssetRetirementRequestCreate,
    AssetRetirementRequestResponse,
    AssetSummaryAnalyticsReport,
    AssetTransferActionRequest,
    AssetTransferCreate,
    AssetTransferResponse,
    AssetUpdate,
    AssetWarrantyContractCreate,
    AssetWarrantyContractResponse,
    DepreciationCalculationRequest,
    DepreciationPostRequest,
    DepreciationPostResponse,
    InspectionRecordCreate,
    InspectionRecordResponse,
    InspectionTemplateCreate,
    InspectionTemplateResponse,
    MaintenancePlanCreate,
    MaintenancePlanResponse,
    MaintenanceWorkOrderCloseRequest,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderReopenRequest,
    MaintenanceWorkOrderResponse,
    MaintenanceWorkOrderUpdate,
    MaintenanceWorkOrderVerifyRequest,
    PartConsumptionRequest,
    PartReservationRequest,
    WarrantyClaimCreate,
    WarrantyClaimResponse,
    WorkOrderPartConsumptionResponse,
)
from app.services.asset_service import AssetService

assets_router = APIRouter(prefix="/assets", tags=["Enterprise Assets & Facilities"])


# =============================================================================
# 1. ASSET CATEGORIES
# =============================================================================


@assets_router.get(
    "/categories",
    response_model=list[AssetCategoryResponse],
    summary="List asset categories and classification taxonomy",
)
async def list_categories(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_READ))],
    is_active: bool | None = Query(None),
):
    return await AssetService.list_categories(db, tenant.tenant_id, is_active)


@assets_router.post(
    "/categories",
    response_model=AssetCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create configurable asset category and management policy",
)
async def create_category(
    payload: AssetCategoryCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_MANAGE))],
):
    return await AssetService.create_category(db, tenant.tenant_id, payload)


@assets_router.get(
    "/categories/{category_id}",
    response_model=AssetCategoryResponse,
    summary="Get asset category details",
)
async def get_category(
    category_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_READ))],
):
    return await AssetService.get_category(db, tenant.tenant_id, category_id)


@assets_router.put(
    "/categories/{category_id}",
    response_model=AssetCategoryResponse,
    summary="Update asset category policy",
)
async def update_category(
    category_id: UUID,
    payload: AssetCategoryUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_MANAGE))],
):
    return await AssetService.update_category(db, tenant.tenant_id, category_id, payload)


# =============================================================================
# 2. ASSET REGISTRY & BULK REGISTRATION
# =============================================================================


@assets_router.get(
    "",
    response_model=list[AssetResponse],
    summary="List institutional assets with filtering and pagination",
)
async def list_assets(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_READ))],
    category_id: UUID | None = Query(None),
    lifecycle_state: str | None = Query(None),
    operational_status: str | None = Query(None),
    campus_id: UUID | None = Query(None),
    department_id: UUID | None = Query(None),
    custodian_id: UUID | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return await AssetService.list_assets(
        db=db,
        tenant_id=tenant.tenant_id,
        category_id=category_id,
        lifecycle_state=lifecycle_state,
        operational_status=operational_status,
        campus_id=campus_id,
        department_id=department_id,
        custodian_id=custodian_id,
        search=search,
        skip=skip,
        limit=limit,
    )


@assets_router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new institutional asset or facility equipment",
)
async def create_asset(
    payload: AssetCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_CREATE))],
):
    return await AssetService.create_asset(db, tenant.tenant_id, payload, current_user.id)


@assets_router.post(
    "/bulk",
    response_model=AssetBulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk register institutional assets with validation",
)
async def bulk_create_assets(
    payload: AssetBulkCreateRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_CREATE))],
):
    return await AssetService.bulk_create_assets(db, tenant.tenant_id, payload, current_user.id)


@assets_router.get(
    "/reports/summary",
    response_model=AssetSummaryAnalyticsReport,
    summary="Executive summary analytics on assets, valuations, and condition",
)
async def get_summary_report(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_REPORT_READ))],
):
    return await AssetService.get_summary_analytics(db, tenant.tenant_id)


@assets_router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Get complete asset profile by ID",
)
async def get_asset(
    asset_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_READ))],
):
    return await AssetService.get_asset(db, tenant.tenant_id, asset_id)


@assets_router.put(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Update asset profile",
)
async def update_asset(
    asset_id: UUID,
    payload: AssetUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MANAGE))],
):
    return await AssetService.update_asset(db, tenant.tenant_id, asset_id, payload, current_user.id)


# =============================================================================
# 3. ASSET LIFECYCLE STATE MACHINE
# =============================================================================


@assets_router.post(
    "/{asset_id}/lifecycle",
    response_model=AssetResponse,
    summary="Transition asset lifecycle state according to state machine",
)
async def transition_asset_lifecycle(
    asset_id: UUID,
    payload: AssetLifecycleTransitionRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_LIFECYCLE_MANAGE))],
):
    return await AssetService.transition_lifecycle(db, tenant.tenant_id, asset_id, payload, current_user.id)


@assets_router.get(
    "/{asset_id}/lifecycle",
    response_model=list[AssetLifecycleEventResponse],
    summary="Get chronological lifecycle event history for asset",
)
async def get_asset_lifecycle_history(
    asset_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_READ))],
):
    asset = await AssetService.get_asset(db, tenant.tenant_id, asset_id)
    return asset.lifecycle_history


# =============================================================================
# 4. ASSET ASSIGNMENT, CUSTODY & TRANSFERS
# =============================================================================


@assets_router.post(
    "/{asset_id}/assignments",
    response_model=AssetAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign custody or issue temporary loan for asset",
)
async def assign_asset(
    asset_id: UUID,
    payload: AssetAssignmentCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_ASSIGN))],
):
    return await AssetService.assign_asset(db, tenant.tenant_id, asset_id, payload, current_user.id)


@assets_router.get(
    "/{asset_id}/assignments",
    response_model=list[AssetAssignmentResponse],
    summary="Get custody assignment history for asset",
)
async def get_asset_assignments(
    asset_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_READ))],
):
    asset = await AssetService.get_asset(db, tenant.tenant_id, asset_id)
    return asset.assignments


@assets_router.post(
    "/assignments/{assignment_id}/acknowledge",
    response_model=AssetAssignmentResponse,
    summary="Acknowledge receipt of asset custody",
)
async def acknowledge_assignment(
    assignment_id: UUID,
    payload: AssetAssignmentAcknowledgeRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await AssetService.acknowledge_assignment(
        db, tenant.tenant_id, assignment_id, current_user.id, payload.acknowledgement_notes
    )


@assets_router.post(
    "/assignments/{assignment_id}/return",
    response_model=AssetAssignmentResponse,
    summary="Process return to store of assigned asset custody",
)
async def return_assignment(
    assignment_id: UUID,
    payload: AssetAssignmentReturnRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_ASSIGN))],
):
    return await AssetService.return_assignment(
        db=db,
        tenant_id=tenant.tenant_id,
        assignment_id=assignment_id,
        return_date=payload.actual_return_date,
        condition_at_return=payload.condition_at_return,
        current_user_id=current_user.id,
        handover_notes=payload.handover_notes,
        evidence=payload.supporting_evidence,
    )


@assets_router.post(
    "/{asset_id}/transfers",
    response_model=AssetTransferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate inter-campus or departmental asset transfer",
)
async def transfer_asset(
    asset_id: UUID,
    payload: AssetTransferCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_TRANSFER))],
):
    return await AssetService.transfer_asset(db, tenant.tenant_id, asset_id, payload, current_user.id)


@assets_router.post(
    "/transfers/{transfer_id}/action",
    response_model=AssetTransferResponse,
    summary="Process transfer action (APPROVE, DISPATCH, RECEIVE, REJECT, CANCEL)",
)
async def process_transfer_action(
    transfer_id: UUID,
    payload: AssetTransferActionRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_TRANSFER))],
):
    return await AssetService.process_transfer_action(
        db, tenant.tenant_id, transfer_id, payload.action, current_user.id, payload.notes
    )


# =============================================================================
# 5. PREVENTIVE & CORRECTIVE MAINTENANCE
# =============================================================================


@assets_router.get(
    "/maintenance/plans",
    response_model=list[MaintenancePlanResponse],
    summary="List recurring preventive maintenance plans",
)
async def list_maintenance_plans(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_READ))],
    category_id: UUID | None = Query(None),
):
    return await AssetService.list_maintenance_plans(db, tenant.tenant_id, category_id)


@assets_router.post(
    "/maintenance/plans",
    response_model=MaintenancePlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create preventive maintenance plan",
)
async def create_maintenance_plan(
    payload: MaintenancePlanCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_MANAGE))],
):
    return await AssetService.create_maintenance_plan(db, tenant.tenant_id, payload)


@assets_router.get(
    "/maintenance/work-orders",
    response_model=list[MaintenanceWorkOrderResponse],
    summary="List maintenance work orders with filtering",
)
async def list_work_orders(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_READ))],
    asset_id: UUID | None = Query(None),
    status: str | None = Query(None),
    priority: str | None = Query(None),
    technician_id: UUID | None = Query(None),
):
    return await AssetService.list_work_orders(db, tenant.tenant_id, asset_id, status, priority, technician_id)


@assets_router.post(
    "/maintenance/work-orders",
    response_model=MaintenanceWorkOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create preventive or corrective maintenance work order",
)
async def create_work_order(
    payload: MaintenanceWorkOrderCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_MANAGE))],
):
    return await AssetService.create_work_order(db, tenant.tenant_id, payload, current_user.id)


@assets_router.get(
    "/maintenance/work-orders/{work_order_id}",
    response_model=MaintenanceWorkOrderResponse,
    summary="Get maintenance work order details",
)
async def get_work_order(
    work_order_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_READ))],
):
    return await AssetService.get_work_order(db, tenant.tenant_id, work_order_id)


@assets_router.put(
    "/maintenance/work-orders/{work_order_id}",
    response_model=MaintenanceWorkOrderResponse,
    summary="Update maintenance work order status, diagnosis or schedule",
)
async def update_work_order(
    work_order_id: UUID,
    payload: MaintenanceWorkOrderUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_MANAGE))],
):
    return await AssetService.update_work_order(db, tenant.tenant_id, work_order_id, payload, current_user.id)


@assets_router.post(
    "/maintenance/work-orders/{work_order_id}/close",
    response_model=MaintenanceWorkOrderResponse,
    summary="Complete and close maintenance work order",
)
async def close_work_order(
    work_order_id: UUID,
    payload: MaintenanceWorkOrderCloseRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_MANAGE))],
):
    return await AssetService.close_work_order(db, tenant.tenant_id, work_order_id, payload, current_user.id)


@assets_router.post(
    "/maintenance/work-orders/{work_order_id}/verify",
    response_model=MaintenanceWorkOrderResponse,
    summary="Verify completed high-risk work order and finalize closure",
)
async def verify_work_order(
    work_order_id: UUID,
    payload: MaintenanceWorkOrderVerifyRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_MANAGE))],
):
    return await AssetService.verify_work_order(db, tenant.tenant_id, work_order_id, payload.verification_notes, current_user.id)


@assets_router.post(
    "/maintenance/work-orders/{work_order_id}/reopen",
    response_model=MaintenanceWorkOrderResponse,
    summary="Reopen closed work order with authorized reason",
)
async def reopen_work_order(
    work_order_id: UUID,
    payload: MaintenanceWorkOrderReopenRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_MANAGE))],
):
    return await AssetService.reopen_work_order(db, tenant.tenant_id, work_order_id, payload.reopen_reason, current_user.id)


@assets_router.post(
    "/maintenance/work-orders/{work_order_id}/parts/reserve",
    response_model=WorkOrderPartConsumptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reserve spare parts from warehouse for work order",
)
async def reserve_part(
    work_order_id: UUID,
    payload: PartReservationRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_MANAGE))],
):
    return await AssetService.reserve_work_order_part(db, tenant.tenant_id, work_order_id, payload, current_user.id)


@assets_router.post(
    "/maintenance/work-orders/parts/consume",
    response_model=WorkOrderPartConsumptionResponse,
    summary="Record actual spare part consumption with stock ledger entry",
)
async def consume_part(
    payload: PartConsumptionRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_MANAGE))],
):
    return await AssetService.consume_work_order_part(
        db, tenant.tenant_id, payload.part_consumption_id, payload.quantity_to_consume, current_user.id
    )


# =============================================================================
# 6. INSPECTIONS & SAFETY
# =============================================================================


@assets_router.get(
    "/inspections/templates",
    response_model=list[InspectionTemplateResponse],
    summary="List inspection checklist templates",
)
async def list_inspection_templates(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_READ))],
    category_id: UUID | None = Query(None),
):
    return await AssetService.list_inspection_templates(db, tenant.tenant_id, category_id)


@assets_router.post(
    "/inspections/templates",
    response_model=InspectionTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create safety and compliance inspection template",
)
async def create_inspection_template(
    payload: InspectionTemplateCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_INSPECTION_MANAGE))],
):
    return await AssetService.create_inspection_template(db, tenant.tenant_id, payload)


@assets_router.post(
    "/inspections",
    response_model=InspectionRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record physical safety inspection results and enforce safety restrictions",
)
async def record_inspection(
    payload: InspectionRecordCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_INSPECTION_MANAGE))],
):
    return await AssetService.record_inspection(db, tenant.tenant_id, payload, current_user.id)


@assets_router.get(
    "/{asset_id}/inspections",
    response_model=list[InspectionRecordResponse],
    summary="Get inspection and compliance audit history for asset",
)
async def get_asset_inspections(
    asset_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_READ))],
):
    asset = await AssetService.get_asset(db, tenant.tenant_id, asset_id)
    return asset.inspections


# =============================================================================
# 7. WARRANTIES & SERVICE CONTRACTS
# =============================================================================


@assets_router.post(
    "/warranties",
    response_model=AssetWarrantyContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add warranty or service contract (AMC/CMC) for asset",
)
async def create_warranty_contract(
    payload: AssetWarrantyContractCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_MANAGE))],
):
    return await AssetService.create_warranty_contract(db, tenant.tenant_id, payload)


@assets_router.get(
    "/{asset_id}/warranties",
    response_model=list[AssetWarrantyContractResponse],
    summary="Get warranty and AMC contracts for asset",
)
async def get_asset_warranties(
    asset_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_READ))],
):
    asset = await AssetService.get_asset(db, tenant.tenant_id, asset_id)
    return asset.warranty_contracts


@assets_router.post(
    "/warranties/claims",
    response_model=WarrantyClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit formal warranty service claim",
)
async def create_warranty_claim(
    payload: WarrantyClaimCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MAINTENANCE_MANAGE))],
):
    return await AssetService.create_warranty_claim(db, tenant.tenant_id, payload, current_user.id)


# =============================================================================
# 8. DEPRECIATION & FINANCIAL INTEGRATION
# =============================================================================


@assets_router.post(
    "/depreciation/calculate",
    response_model=list[AssetDepreciationScheduleResponse],
    summary="Compute period depreciation schedules without ledger posting",
)
async def calculate_depreciation(
    payload: DepreciationCalculationRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_FINANCIAL_READ))],
):
    return await AssetService.calculate_depreciation_period(
        db=db,
        tenant_id=tenant.tenant_id,
        fiscal_year=payload.fiscal_year,
        period_name=payload.period_name,
        period_start_date=payload.period_start_date,
        period_end_date=payload.period_end_date,
        asset_id=payload.asset_id,
    )


@assets_router.post(
    "/depreciation/post",
    response_model=DepreciationPostResponse,
    summary="Post computed depreciation schedules to finance general ledger",
)
async def post_depreciation(
    payload: DepreciationPostRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_MANAGE))],
):
    count, total, ref = await AssetService.post_depreciation_to_finance(
        db, tenant.tenant_id, payload.schedule_ids, payload.journal_entry_reference, current_user.id
    )
    return DepreciationPostResponse(
        posted_count=count, total_depreciation_posted=total, journal_entry_reference=ref
    )


@assets_router.get(
    "/{asset_id}/depreciation",
    response_model=list[AssetDepreciationScheduleResponse],
    summary="Get depreciation history and book value schedule for asset",
)
async def get_asset_depreciation(
    asset_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(ASSETS_FINANCIAL_READ))],
):
    asset = await AssetService.get_asset(db, tenant.tenant_id, asset_id)
    return asset.depreciation_schedules


# =============================================================================
# 9. PHYSICAL AUDITS & ASSET VERIFICATION
# =============================================================================


@assets_router.post(
    "/audits/campaigns",
    response_model=AssetAuditCampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate institutional physical asset verification audit campaign",
)
async def create_audit_campaign(
    payload: AssetAuditCampaignCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_AUDIT_MANAGE))],
):
    return await AssetService.create_audit_campaign(db, tenant.tenant_id, payload, current_user.id)


@assets_router.post(
    "/audits/campaigns/{campaign_id}/scan",
    response_model=AssetAuditItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record physical tag scan and verify against authoritative records",
)
async def record_audit_scan(
    campaign_id: UUID,
    payload: AssetAuditItemScanRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_AUDIT_MANAGE))],
):
    return await AssetService.record_audit_scan(db, tenant.tenant_id, campaign_id, payload, current_user.id)


# =============================================================================
# 10. ASSET RETIREMENT & DISPOSAL
# =============================================================================


@assets_router.post(
    "/retirement/requests",
    response_model=AssetRetirementRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit formal asset retirement and technical decommissioning request",
)
async def request_retirement(
    payload: AssetRetirementRequestCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_RETIREMENT_REQUEST))],
):
    return await AssetService.request_retirement(db, tenant.tenant_id, payload, current_user.id)


@assets_router.post(
    "/retirement/requests/{request_id}/approve",
    response_model=AssetRetirementRequestResponse,
    summary="Approve or reject asset retirement request",
)
async def approve_retirement(
    request_id: UUID,
    payload: AssetRetirementApprovalRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_RETIREMENT_APPROVE))],
):
    return await AssetService.approve_retirement(
        db, tenant.tenant_id, request_id, payload.action, payload.notes, current_user.id
    )


@assets_router.post(
    "/retirement/requests/{request_id}/execute",
    response_model=AssetRetirementRequestResponse,
    summary="Execute certified asset disposal, data wiping, and terminal decommission",
)
async def execute_disposal(
    request_id: UUID,
    payload: AssetRetirementExecuteRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ASSETS_RETIREMENT_APPROVE))],
):
    return await AssetService.execute_disposal(db, tenant.tenant_id, request_id, payload, current_user.id)

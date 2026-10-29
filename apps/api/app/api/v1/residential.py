"""CampusOS Enterprise Hostel, Residential Life, Room Allocation & Student Accommodation Management API Router (Step 54).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    RESIDENTIAL_ALLOCATION_MANAGE,
    RESIDENTIAL_APPLICATION_REVIEW,
    RESIDENTIAL_APPLICATION_SUBMIT_OWN,
    RESIDENTIAL_CHECKIN_MANAGE,
    RESIDENTIAL_CHECKOUT_MANAGE,
    RESIDENTIAL_FEES_MANAGE,
    RESIDENTIAL_FEES_READ,
    RESIDENTIAL_HOSTEL_MANAGE,
    RESIDENTIAL_HOSTEL_READ,
    RESIDENTIAL_INCIDENT_MANAGE,
    RESIDENTIAL_INCIDENT_READ_AUTHORIZED,
    RESIDENTIAL_MAINTENANCE_SUBMIT,
    RESIDENTIAL_MOVEMENT_MANAGE,
    RESIDENTIAL_REPORT_READ,
    RESIDENTIAL_ROOM_MANAGE,
    RESIDENTIAL_VISITOR_MANAGE,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.models.residential import (
    AccommodationApplicationStatus,
    AllocationStatus,
    BedStatus,
    HostelOperationalStatus,
    HostelType,
    ResidentLifecycleStatus,
    RoomType,
)
from app.schemas.residential import (
    BatchAllocationCommitRequest,
    BatchAllocationPreviewRequest,
    BatchAllocationPreviewResponse,
    BedStatusUpdateRequest,
    HostelAllocationCreate,
    HostelAllocationResponse,
    HostelAllocationTransferRequest,
    HostelApplicationCreate,
    HostelApplicationCycleCreate,
    HostelApplicationCycleResponse,
    HostelApplicationResponse,
    HostelApplicationReviewRequest,
    HostelBedCreate,
    HostelBedResponse,
    HostelBedUpdate,
    HostelBlockCreate,
    HostelBlockResponse,
    HostelCheckInRequest,
    HostelCheckOutRequest,
    HostelComplaintCreate,
    HostelComplaintResponse,
    HostelComplaintUpdate,
    HostelCreate,
    HostelDetailResponse,
    HostelFeePlanCreate,
    HostelFeePlanInvoiceGenerateRequest,
    HostelFeePlanResponse,
    HostelFloorCreate,
    HostelFloorResponse,
    HostelGatePassCreate,
    HostelGatePassResponse,
    HostelGatePassVerifyRequest,
    HostelIncidentCreate,
    HostelIncidentResponse,
    HostelLeavePassCreate,
    HostelLeavePassResponse,
    HostelMealEnrollmentCreate,
    HostelMealEnrollmentResponse,
    HostelMealHeadcountResponse,
    HostelMealPlanCreate,
    HostelMealPlanResponse,
    HostelOccupancyReportResponse,
    HostelResidentResponse,
    HostelResponse,
    HostelRoomCreate,
    HostelRoomDetailResponse,
    HostelRoomResponse,
    HostelRoomUpdate,
    HostelSafetyInspectionCreate,
    HostelSafetyInspectionResponse,
    HostelUpdate,
    HostelVisitorCheckOutRequest,
    HostelVisitorCreate,
    HostelVisitorResponse,
)
from app.services.residential_service import ResidentialService

residential_router = APIRouter(prefix="/residential", tags=["Enterprise Hostel & Residential Life"])


# =============================================================================
# 1. HOSTELS & INFRASTRUCTURE HIERARCHY
# =============================================================================


@residential_router.get(
    "/hostels",
    response_model=list[HostelResponse],
    summary="List hostels and residential facilities",
)
async def list_hostels(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
    campus_id: UUID | None = Query(None),
    hostel_type: HostelType | None = Query(None),
    operational_status: HostelOperationalStatus | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await ResidentialService.list_hostels(
        db,
        tenant.tenant_id,
        campus_id=campus_id,
        hostel_type=hostel_type,
        operational_status=operational_status,
        search=search,
        skip=skip,
        limit=limit,
    )


@residential_router.post(
    "/hostels",
    response_model=HostelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new hostel or residential facility",
)
async def create_hostel(
    payload: HostelCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_MANAGE))],
):
    return await ResidentialService.create_hostel(db, tenant.tenant_id, payload)


@residential_router.get(
    "/hostels/{hostel_id}",
    response_model=HostelDetailResponse,
    summary="Get hostel details including block/floor counts and room inventory",
)
async def get_hostel(
    hostel_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
):
    return await ResidentialService.get_hostel(db, tenant.tenant_id, hostel_id)


@residential_router.put(
    "/hostels/{hostel_id}",
    response_model=HostelResponse,
    summary="Update hostel configuration, policies, and warden assignments",
)
async def update_hostel(
    hostel_id: UUID,
    payload: HostelUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_MANAGE))],
):
    return await ResidentialService.update_hostel(db, tenant.tenant_id, hostel_id, payload)


@residential_router.post(
    "/hostels/{hostel_id}/blocks",
    response_model=HostelBlockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a block or wing within a hostel",
)
async def create_block(
    hostel_id: UUID,
    payload: HostelBlockCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_MANAGE))],
):
    return await ResidentialService.create_block(db, tenant.tenant_id, hostel_id, payload)


@residential_router.post(
    "/blocks/{block_id}/floors",
    response_model=HostelFloorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a floor within a block",
)
async def create_floor(
    block_id: UUID,
    payload: HostelFloorCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_MANAGE))],
):
    return await ResidentialService.create_floor(db, tenant.tenant_id, block_id, payload)


# =============================================================================
# 2. ROOM & BED INVENTORY
# =============================================================================


@residential_router.get(
    "/rooms",
    response_model=list[HostelRoomResponse],
    summary="List rooms with capacity and occupancy details",
)
async def list_rooms(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
    hostel_id: UUID | None = Query(None),
    floor_id: UUID | None = Query(None),
    room_type: RoomType | None = Query(None),
    is_active: bool | None = Query(None),
    has_vacancy: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await ResidentialService.list_rooms(
        db,
        tenant.tenant_id,
        hostel_id=hostel_id,
        floor_id=floor_id,
        room_type=room_type,
        is_active=is_active,
        has_vacancy=has_vacancy,
        skip=skip,
        limit=limit,
    )


@residential_router.post(
    "/rooms",
    response_model=HostelRoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a room and auto-provision its addressable beds",
)
async def create_room(
    payload: HostelRoomCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_ROOM_MANAGE))],
):
    return await ResidentialService.create_room(db, tenant.tenant_id, payload)


@residential_router.get(
    "/rooms/{room_id}",
    response_model=HostelRoomDetailResponse,
    summary="Get room details including all individually addressable beds",
)
async def get_room(
    room_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
):
    return await ResidentialService.get_room(db, tenant.tenant_id, room_id)


@residential_router.put(
    "/rooms/{room_id}",
    response_model=HostelRoomResponse,
    summary="Update room details and validate capacity constraints",
)
async def update_room(
    room_id: UUID,
    payload: HostelRoomUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_ROOM_MANAGE))],
):
    return await ResidentialService.update_room(db, tenant.tenant_id, room_id, payload)


@residential_router.post(
    "/rooms/{room_id}/beds",
    response_model=HostelBedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an addressable bed to a room",
)
async def create_bed(
    room_id: UUID,
    payload: HostelBedCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_ROOM_MANAGE))],
):
    return await ResidentialService.create_bed(db, tenant.tenant_id, room_id, payload)


@residential_router.get(
    "/beds",
    response_model=list[HostelBedResponse],
    summary="List beds across rooms and hostels",
)
async def list_beds(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
    room_id: UUID | None = Query(None),
    hostel_id: UUID | None = Query(None),
    bed_status: BedStatus | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await ResidentialService.list_beds(
        db,
        tenant.tenant_id,
        room_id=room_id,
        hostel_id=hostel_id,
        bed_status=bed_status,
        skip=skip,
        limit=limit,
    )


@residential_router.get(
    "/beds/{bed_id}",
    response_model=HostelBedResponse,
    summary="Get bed details",
)
async def get_bed(
    bed_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
):
    return await ResidentialService.get_bed(db, tenant.tenant_id, bed_id)


@residential_router.put(
    "/beds/{bed_id}",
    response_model=HostelBedResponse,
    summary="Update bed details",
)
async def update_bed(
    bed_id: UUID,
    payload: HostelBedUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_ROOM_MANAGE))],
):
    return await ResidentialService.update_bed(db, tenant.tenant_id, bed_id, payload)


@residential_router.post(
    "/beds/{bed_id}/status",
    response_model=HostelBedResponse,
    summary="Change bed status (available, blocked, under maintenance, retired)",
)
async def update_bed_status(
    bed_id: UUID,
    payload: BedStatusUpdateRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_ROOM_MANAGE))],
):
    return await ResidentialService.update_bed_status(db, tenant.tenant_id, bed_id, payload)


# =============================================================================
# 3. ACCOMMODATION APPLICATION CYCLES & APPLICATIONS
# =============================================================================


@residential_router.get(
    "/application-cycles",
    response_model=list[HostelApplicationCycleResponse],
    summary="List accommodation application cycles",
)
async def list_application_cycles(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
    academic_year: str | None = Query(None),
    is_active: bool | None = Query(None),
):
    return await ResidentialService.list_application_cycles(
        db, tenant.tenant_id, academic_year=academic_year, is_active=is_active
    )


@residential_router.post(
    "/application-cycles",
    response_model=HostelApplicationCycleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an accommodation application cycle",
)
async def create_application_cycle(
    payload: HostelApplicationCycleCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_ALLOCATION_MANAGE))],
):
    return await ResidentialService.create_application_cycle(db, tenant.tenant_id, payload)


@residential_router.get(
    "/applications",
    response_model=list[HostelApplicationResponse],
    summary="List student accommodation applications",
)
async def list_applications(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    cycle_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    app_status: AccommodationApplicationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    # Enforce student object-level access if user is a student
    user_roles = {r.name.upper() if hasattr(r, "name") else str(r).upper() for r in getattr(current_user, "roles", [])}
    if "STUDENT" in user_roles and not ("SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles or "WARDEN" in user_roles):
        # Force student_id to be their own ID
        student_id = current_user.id

    return await ResidentialService.list_applications(
        db,
        tenant.tenant_id,
        cycle_id=cycle_id,
        student_id=student_id,
        status=app_status,
        skip=skip,
        limit=limit,
    )


@residential_router.post(
    "/applications",
    response_model=HostelApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a student accommodation application",
)
async def submit_application(
    payload: HostelApplicationCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_APPLICATION_SUBMIT_OWN))],
):
    return await ResidentialService.submit_application(db, tenant.tenant_id, payload, current_user.id)


@residential_router.get(
    "/applications/{application_id}",
    response_model=HostelApplicationResponse,
    summary="Get accommodation application details",
)
async def get_application(
    application_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await ResidentialService.get_application(db, tenant.tenant_id, application_id)


@residential_router.post(
    "/applications/{application_id}/review",
    response_model=HostelApplicationResponse,
    summary="Review student accommodation application (approve, reject, waitlist)",
)
async def review_application(
    application_id: UUID,
    payload: HostelApplicationReviewRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_APPLICATION_REVIEW))],
):
    return await ResidentialService.review_application(
        db, tenant.tenant_id, application_id, payload, reviewer_id=current_user.id
    )


# =============================================================================
# 4. ROOM & BED ALLOCATION ENGINE
# =============================================================================


@residential_router.get(
    "/allocations",
    response_model=list[HostelAllocationResponse],
    summary="List bed allocations",
)
async def list_allocations(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
    hostel_id: UUID | None = Query(None),
    room_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    alloc_status: AllocationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await ResidentialService.list_allocations(
        db,
        tenant.tenant_id,
        hostel_id=hostel_id,
        room_id=room_id,
        student_id=student_id,
        status=alloc_status,
        skip=skip,
        limit=limit,
    )


@residential_router.post(
    "/allocations",
    response_model=HostelAllocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Allocate a bed to a student with concurrency locks",
)
async def allocate_bed(
    payload: HostelAllocationCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_ALLOCATION_MANAGE))],
):
    return await ResidentialService.allocate_bed(
        db, tenant.tenant_id, payload, allocated_by=current_user.id
    )


@residential_router.post(
    "/allocations/batch-preview",
    response_model=BatchAllocationPreviewResponse,
    summary="Preview batch room and bed allocation before committing",
)
async def preview_batch_allocation(
    payload: BatchAllocationPreviewRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_ALLOCATION_MANAGE))],
):
    return await ResidentialService.preview_batch_allocation(db, tenant.tenant_id, payload)


@residential_router.post(
    "/allocations/batch-commit",
    response_model=list[HostelAllocationResponse],
    summary="Commit validated batch allocations transactionally",
)
async def commit_batch_allocation(
    payload: BatchAllocationCommitRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_ALLOCATION_MANAGE))],
):
    return await ResidentialService.commit_batch_allocation(
        db, tenant.tenant_id, payload, allocated_by=current_user.id
    )


@residential_router.post(
    "/allocations/{allocation_id}/transfer",
    response_model=HostelAllocationResponse,
    summary="Transfer a resident to another room/bed following an authorized request",
)
async def transfer_allocation(
    allocation_id: UUID,
    payload: HostelAllocationTransferRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_ALLOCATION_MANAGE))],
):
    return await ResidentialService.transfer_allocation(
        db, tenant.tenant_id, allocation_id, payload, approved_by=current_user.id
    )


@residential_router.post(
    "/allocations/{allocation_id}/release",
    response_model=HostelAllocationResponse,
    summary="Release or cancel an allocation before check-in",
)
async def release_allocation(
    allocation_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_ALLOCATION_MANAGE))],
    reason: str = Query(..., min_length=3),
):
    return await ResidentialService.release_allocation(
        db, tenant.tenant_id, allocation_id, reason=reason, released_by=current_user.id
    )


# =============================================================================
# 5. RESIDENT LIFECYCLE: CHECK-IN & CHECK-OUT
# =============================================================================


@residential_router.get(
    "/residents",
    response_model=list[HostelResidentResponse],
    summary="List hostel residents with room, bed, and check-in status",
)
async def list_residents(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
    hostel_id: UUID | None = Query(None),
    lifecycle_status: ResidentLifecycleStatus | None = Query(None, alias="status"),
    student_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await ResidentialService.list_residents(
        db,
        tenant.tenant_id,
        hostel_id=hostel_id,
        status=lifecycle_status,
        student_id=student_id,
        skip=skip,
        limit=limit,
    )


@residential_router.get(
    "/residents/{resident_id}",
    response_model=HostelResidentResponse,
    summary="Get resident occupancy and lifecycle details",
)
async def get_resident(
    resident_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
):
    return await ResidentialService.get_resident(db, tenant.tenant_id, resident_id)


@residential_router.post(
    "/residents/{resident_id}/check-in",
    response_model=HostelResidentResponse,
    summary="Process resident check-in, key handover, and inventory verification",
)
async def check_in_resident(
    resident_id: UUID,
    payload: HostelCheckInRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_CHECKIN_MANAGE))],
):
    return await ResidentialService.check_in_resident(
        db, tenant.tenant_id, resident_id, payload, checked_in_by=current_user.id
    )


@residential_router.post(
    "/residents/{resident_id}/check-out",
    response_model=HostelResidentResponse,
    summary="Process resident check-out, damage assessment, Finance charge, and bed release",
)
async def check_out_resident(
    resident_id: UUID,
    payload: HostelCheckOutRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_CHECKOUT_MANAGE))],
):
    return await ResidentialService.check_out_resident(
        db, tenant.tenant_id, resident_id, payload, checked_out_by=current_user.id
    )


# =============================================================================
# 6. RESIDENTIAL FEES & MEAL PLANS
# =============================================================================


@residential_router.get(
    "/fee-plans",
    response_model=list[HostelFeePlanResponse],
    summary="List hostel residential fee plans",
)
async def list_fee_plans(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_FEES_READ))],
    hostel_id: UUID | None = Query(None),
    is_active: bool | None = Query(None),
):
    return await ResidentialService.list_fee_plans(
        db, tenant.tenant_id, hostel_id=hostel_id, is_active=is_active
    )


@residential_router.post(
    "/fee-plans",
    response_model=HostelFeePlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a residential fee plan",
)
async def create_fee_plan(
    payload: HostelFeePlanCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_FEES_MANAGE))],
):
    return await ResidentialService.create_fee_plan(db, tenant.tenant_id, payload)


@residential_router.post(
    "/fee-plans/{fee_plan_id}/generate-invoices",
    summary="Generate residential invoices in the authoritative Finance module",
)
async def generate_fee_invoices(
    fee_plan_id: UUID,
    payload: HostelFeePlanInvoiceGenerateRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_FEES_MANAGE))],
):
    return await ResidentialService.generate_fee_invoices(
        db, tenant.tenant_id, fee_plan_id, payload, generated_by=current_user.id
    )


@residential_router.get(
    "/meal-plans",
    response_model=list[HostelMealPlanResponse],
    summary="List residential meal and mess plans",
)
async def list_meal_plans(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
    hostel_id: UUID | None = Query(None),
    is_active: bool | None = Query(None),
):
    return await ResidentialService.list_meal_plans(
        db, tenant.tenant_id, hostel_id=hostel_id, is_active=is_active
    )


@residential_router.post(
    "/meal-plans",
    response_model=HostelMealPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a meal or mess plan",
)
async def create_meal_plan(
    payload: HostelMealPlanCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_MANAGE))],
):
    return await ResidentialService.create_meal_plan(db, tenant.tenant_id, payload)


@residential_router.post(
    "/meal-plans/enroll",
    response_model=HostelMealEnrollmentResponse,
    summary="Enroll a resident in a meal plan",
)
async def enroll_meal_plan(
    payload: HostelMealEnrollmentCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_MANAGE))],
):
    return await ResidentialService.enroll_meal_plan(db, tenant.tenant_id, payload)


@residential_router.get(
    "/meal-plans/headcount",
    response_model=HostelMealHeadcountResponse,
    summary="Get projected meal headcount for kitchen preparation without procurement duplication",
)
async def get_meal_headcount(
    meal_plan_id: UUID,
    service_date: date,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
):
    return await ResidentialService.get_meal_headcount(
        db, tenant.tenant_id, meal_plan_id, service_date
    )


# =============================================================================
# 7. ATTENDANCE, OUTINGS & CURFEW RECORDS
# =============================================================================


@residential_router.get(
    "/outings",
    response_model=list[HostelLeavePassResponse],
    summary="List residential outings and leave passes",
)
async def list_outings(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    hostel_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    user_roles = {r.name.upper() if hasattr(r, "name") else str(r).upper() for r in getattr(current_user, "roles", [])}
    if "STUDENT" in user_roles and not ("SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles or "WARDEN" in user_roles):
        student_id = current_user.id

    return await ResidentialService.list_outings(
        db,
        tenant.tenant_id,
        hostel_id=hostel_id,
        student_id=student_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@residential_router.post(
    "/outings",
    response_model=HostelLeavePassResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request an outing or overnight leave pass",
)
async def request_outing(
    payload: HostelLeavePassCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await ResidentialService.request_outing(
        db, tenant.tenant_id, payload, requested_by=current_user.id
    )


@residential_router.post(
    "/outings/{outing_id}/depart",
    response_model=HostelLeavePassResponse,
    summary="Record resident physical departure at hostel gate",
)
async def record_departure(
    outing_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_MOVEMENT_MANAGE))],
):
    return await ResidentialService.record_departure(
        db, tenant.tenant_id, outing_id, guard_id=current_user.id
    )


@residential_router.post(
    "/outings/{outing_id}/return",
    response_model=HostelLeavePassResponse,
    summary="Record resident physical return and detect curfew breach",
)
async def record_return(
    outing_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_MOVEMENT_MANAGE))],
):
    return await ResidentialService.record_return(
        db, tenant.tenant_id, outing_id, guard_id=current_user.id
    )


# =============================================================================
# 8. GATE PASSES & VISITOR MANAGEMENT
# =============================================================================


@residential_router.get(
    "/gate-passes",
    response_model=list[HostelGatePassResponse],
    summary="List hostel gate passes",
)
async def list_gate_passes(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_MOVEMENT_MANAGE))],
    hostel_id: UUID | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await ResidentialService.list_gate_passes(
        db, tenant.tenant_id, hostel_id=hostel_id, status=status, skip=skip, limit=limit
    )


@residential_router.post(
    "/gate-passes",
    response_model=HostelGatePassResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a hostel gate pass for materials, equipment, or exit",
)
async def create_gate_pass(
    payload: HostelGatePassCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_MOVEMENT_MANAGE))],
):
    return await ResidentialService.create_gate_pass(
        db, tenant.tenant_id, payload, issued_by=current_user.id
    )


@residential_router.post(
    "/gate-passes/{gate_pass_id}/verify",
    response_model=HostelGatePassResponse,
    summary="Verify gate pass at campus checkpoint",
)
async def verify_gate_pass(
    gate_pass_id: UUID,
    payload: HostelGatePassVerifyRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_MOVEMENT_MANAGE))],
):
    return await ResidentialService.verify_gate_pass(
        db, tenant.tenant_id, gate_pass_id, payload, guard_id=current_user.id
    )


@residential_router.get(
    "/visitors",
    response_model=list[HostelVisitorResponse],
    summary="List residential visitors with privacy-preserving controls",
)
async def list_visitors(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_VISITOR_MANAGE))],
    hostel_id: UUID | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await ResidentialService.list_visitors(
        db, tenant.tenant_id, hostel_id=hostel_id, status=status, skip=skip, limit=limit
    )


@residential_router.post(
    "/visitors",
    response_model=HostelVisitorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a visitor visiting a hostel resident",
)
async def register_visitor(
    payload: HostelVisitorCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_VISITOR_MANAGE))],
):
    return await ResidentialService.register_visitor(
        db, tenant.tenant_id, payload, checked_in_by=current_user.id
    )


@residential_router.post(
    "/visitors/{visitor_id}/checkout",
    response_model=HostelVisitorResponse,
    summary="Check out visitor and log departure",
)
async def checkout_visitor(
    visitor_id: UUID,
    payload: HostelVisitorCheckOutRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_VISITOR_MANAGE))],
):
    return await ResidentialService.checkout_visitor(
        db, tenant.tenant_id, visitor_id, payload, checked_out_by=current_user.id
    )


# =============================================================================
# 9. MAINTENANCE & COMPLAINTS
# =============================================================================


@residential_router.get(
    "/service-requests",
    response_model=list[HostelComplaintResponse],
    summary="List residential maintenance and service complaints",
)
async def list_service_requests(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    hostel_id: UUID | None = Query(None),
    room_id: UUID | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    user_roles = {r.name.upper() if hasattr(r, "name") else str(r).upper() for r in getattr(current_user, "roles", [])}
    student_id = None
    if "STUDENT" in user_roles and not ("SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles or "WARDEN" in user_roles):
        student_id = current_user.id

    return await ResidentialService.list_service_requests(
        db,
        tenant.tenant_id,
        hostel_id=hostel_id,
        room_id=room_id,
        status=status,
        student_id=student_id,
        skip=skip,
        limit=limit,
    )


@residential_router.post(
    "/service-requests",
    response_model=HostelComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit residential maintenance or service complaint with Asset Work Order linkage",
)
async def create_service_request(
    payload: HostelComplaintCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_MAINTENANCE_SUBMIT))],
):
    return await ResidentialService.create_service_request(
        db, tenant.tenant_id, payload, reported_by_user_id=current_user.id
    )


@residential_router.get(
    "/service-requests/{request_id}",
    response_model=HostelComplaintResponse,
    summary="Get service request details and work order status",
)
async def get_service_request(
    request_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return await ResidentialService.get_service_request(db, tenant.tenant_id, request_id)


@residential_router.put(
    "/service-requests/{request_id}",
    response_model=HostelComplaintResponse,
    summary="Update residential service request status and resolution notes",
)
async def update_service_request(
    request_id: UUID,
    payload: HostelComplaintUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_MANAGE))],
):
    return await ResidentialService.update_service_request(
        db, tenant.tenant_id, request_id, payload, resolved_by=current_user.id
    )


# =============================================================================
# 10. RESIDENTIAL SAFETY, INCIDENTS & INSPECTIONS
# =============================================================================


@residential_router.get(
    "/incidents",
    response_model=list[HostelIncidentResponse],
    summary="List residential safety incidents (strictly restricted to authorized roles)",
)
async def list_incidents(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_INCIDENT_READ_AUTHORIZED))],
    hostel_id: UUID | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await ResidentialService.list_incidents(
        db, tenant.tenant_id, hostel_id=hostel_id, status=status, skip=skip, limit=limit
    )


@residential_router.post(
    "/incidents",
    response_model=HostelIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a residential safety or disciplinary incident with restricted access",
)
async def report_incident(
    payload: HostelIncidentCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_INCIDENT_MANAGE))],
):
    return await ResidentialService.report_incident(
        db, tenant.tenant_id, payload, reported_by=current_user.id
    )


@residential_router.get(
    "/inspections",
    response_model=list[HostelSafetyInspectionResponse],
    summary="List hostel safety inspections",
)
async def list_inspections(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_READ))],
    hostel_id: UUID | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await ResidentialService.list_inspections(
        db, tenant.tenant_id, hostel_id=hostel_id, status=status, skip=skip, limit=limit
    )


@residential_router.post(
    "/inspections",
    response_model=HostelSafetyInspectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Conduct and record a hostel safety inspection",
)
async def create_inspection(
    payload: HostelSafetyInspectionCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(RESIDENTIAL_HOSTEL_MANAGE))],
):
    return await ResidentialService.create_inspection(
        db, tenant.tenant_id, payload, inspector_id=current_user.id
    )


# =============================================================================
# 11. REPORTS & OCCUPANCY DASHBOARDS
# =============================================================================


@residential_router.get(
    "/reports/occupancy",
    response_model=HostelOccupancyReportResponse,
    summary="Get comprehensive residential occupancy analytics and vacancy breakdown",
)
async def get_occupancy_report(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(RESIDENTIAL_REPORT_READ))],
    hostel_id: UUID | None = Query(None),
):
    return await ResidentialService.get_occupancy_report(db, tenant.tenant_id, hostel_id=hostel_id)

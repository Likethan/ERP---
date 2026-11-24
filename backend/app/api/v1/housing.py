"""CampusOS Enterprise Student Housing, Off-Campus Accommodation, Landlord Partnerships & Residential Compliance API Router (Step 66).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    HOUSING_AGREEMENT_MANAGE,
    HOUSING_ANALYTICS_READ,
    HOUSING_ASSIGNMENT_MANAGE,
    HOUSING_CHECKIN_MANAGE,
    HOUSING_INSPECTION_MANAGE,
    HOUSING_INSPECTION_READ,
    HOUSING_MAINTENANCE_MANAGE,
    HOUSING_MAINTENANCE_SUBMIT,
    HOUSING_OFFER_MANAGE,
    HOUSING_PROPERTY_APPROVE,
    HOUSING_PROPERTY_MANAGE,
    HOUSING_PROPERTY_READ,
    HOUSING_PROVIDER_MANAGE,
    HOUSING_PROVIDER_READ,
    HOUSING_REQUEST_READ,
    HOUSING_REQUEST_REVIEW,
    HOUSING_REQUEST_SUBMIT_OWN,
)
from app.core.tenant import TenantContext
from app.models.people import StudentProfile, User
from app.schemas.housing import (
    AccommodationBedResponse,
    AccommodationPropertyCreate,
    AccommodationPropertyResponse,
    AccommodationProviderCreate,
    AccommodationProviderResponse,
    AccommodationProviderUpdate,
    AccommodationUnitCreate,
    AccommodationUnitResponse,
    HousingAgreementCreate,
    HousingAgreementResponse,
    HousingAnalyticsSummaryResponse,
    HousingAssignmentCreate,
    HousingAssignmentResponse,
    HousingAssignmentTransferRequest,
    HousingCheckInOutCreate,
    HousingCheckInOutResponse,
    HousingMaintenanceRequestCreate,
    HousingMaintenanceRequestResponse,
    HousingMaintenanceRequestUpdate,
    HousingOfferCreate,
    HousingOfferRespond,
    HousingOfferResponse,
    HousingPropertyInspectionCreate,
    HousingPropertyInspectionResponse,
    PropertyStatusTransitionRequest,
    StudentHousingRequestCreate,
    StudentHousingRequestResponse,
    StudentHousingRequestReview,
)
from app.services.housing_service import HousingService

housing_router = APIRouter(prefix="/housing", tags=["Student Housing & Off-Campus Accommodation"])


async def _resolve_student_id(
    db: AsyncSession, tenant_id: UUID, current_user: User, explicit_student_id: UUID | None = None
) -> UUID:
    """Helper resolving student profile ID from current user or explicit parameter."""
    if explicit_student_id:
        return explicit_student_id
    student = await db.scalar(
        select(StudentProfile).where(
            StudentProfile.tenant_id == tenant_id,
            StudentProfile.user_id == current_user.id,
        )
    )
    if student:
        return student.id
    return current_user.id


# =============================================================================
# 1. ACCOMMODATION PROVIDERS & LANDLORDS
# =============================================================================

@housing_router.post(
    "/providers",
    response_model=AccommodationProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new accommodation provider or landlord",
)
async def create_provider(
    payload: AccommodationProviderCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROVIDER_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.create_provider(payload)


@housing_router.get(
    "/providers",
    response_model=list[AccommodationProviderResponse],
    summary="List registered accommodation providers and landlords",
)
async def list_providers(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROVIDER_READ))],
    status_filter: str | None = Query(None, alias="status"),
    is_active: bool | None = Query(None),
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.list_providers(status=status_filter, is_active=is_active)


@housing_router.get(
    "/providers/{provider_id}",
    response_model=AccommodationProviderResponse,
    summary="Get details of an accommodation provider",
)
async def get_provider(
    provider_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROVIDER_READ))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.get_provider(provider_id)


@housing_router.put(
    "/providers/{provider_id}",
    response_model=AccommodationProviderResponse,
    summary="Update accommodation provider or MoU records",
)
async def update_provider(
    provider_id: UUID,
    payload: AccommodationProviderUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROVIDER_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.update_provider(provider_id, payload)


# =============================================================================
# 2. ACCOMMODATION PROPERTIES
# =============================================================================

@housing_router.post(
    "/properties",
    response_model=AccommodationPropertyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create accommodation property",
)
async def create_property(
    payload: AccommodationPropertyCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROPERTY_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.create_property(payload, current_user.id)


@housing_router.get(
    "/properties",
    response_model=list[AccommodationPropertyResponse],
    summary="List accommodation properties with filters",
)
async def list_properties(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROPERTY_READ))],
    provider_id: UUID | None = Query(None),
    property_type: str | None = Query(None),
    lifecycle_status: str | None = Query(None),
    published_only: bool = Query(False),
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.list_properties(
        provider_id=provider_id,
        property_type=property_type,
        lifecycle_status=lifecycle_status,
        published_only=published_only,
    )


@housing_router.get(
    "/properties/{property_id}",
    response_model=AccommodationPropertyResponse,
    summary="Get property details and capacity status",
)
async def get_property(
    property_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROPERTY_READ))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.get_property(property_id)


@housing_router.post(
    "/properties/{property_id}/transition",
    response_model=AccommodationPropertyResponse,
    summary="Transition property lifecycle status",
)
async def transition_property_status(
    property_id: UUID,
    payload: PropertyStatusTransitionRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROPERTY_APPROVE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.transition_property_status(property_id, payload, current_user.id)


# =============================================================================
# 3. UNITS & BED INVENTORY
# =============================================================================

@housing_router.post(
    "/units",
    response_model=AccommodationUnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create accommodation unit/room with beds",
)
async def create_unit(
    payload: AccommodationUnitCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROPERTY_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.create_unit(payload)


@housing_router.get(
    "/units",
    response_model=list[AccommodationUnitResponse],
    summary="List units and bed inventory for a property",
)
async def list_units(
    property_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROPERTY_READ))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.list_units(property_id)


@housing_router.post(
    "/beds/{bed_id}/block",
    response_model=AccommodationBedResponse,
    summary="Block bed for maintenance or inspection",
)
async def block_bed(
    bed_id: UUID,
    reason: str,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROPERTY_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.block_bed(bed_id, reason)


# =============================================================================
# 4. HOUSING REQUESTS
# =============================================================================

@housing_router.post(
    "/requests",
    response_model=StudentHousingRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit student accommodation request",
)
async def submit_housing_request(
    payload: StudentHousingRequestCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_REQUEST_SUBMIT_OWN))],
    student_id: UUID | None = Query(None),
):
    service = HousingService(db, tenant_ctx.tenant_id)
    target_student_id = await _resolve_student_id(db, tenant_ctx.tenant_id, current_user, student_id)
    return await service.submit_housing_request(target_student_id, payload)


@housing_router.get(
    "/requests",
    response_model=list[StudentHousingRequestResponse],
    summary="List housing requests with filters",
)
async def list_housing_requests(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_REQUEST_READ))],
    student_id: UUID | None = Query(None),
    property_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.list_housing_requests(
        student_id=student_id, property_id=property_id, status=status_filter
    )


@housing_router.get(
    "/requests/{request_id}",
    response_model=StudentHousingRequestResponse,
    summary="Get housing request dossier",
)
async def get_housing_request(
    request_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_REQUEST_READ))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.get_housing_request(request_id)


@housing_router.post(
    "/requests/{request_id}/review",
    response_model=StudentHousingRequestResponse,
    summary="Review housing request (Approve, Waitlist, Reject)",
)
async def review_housing_request(
    request_id: UUID,
    payload: StudentHousingRequestReview,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_REQUEST_REVIEW))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.review_housing_request(request_id, payload, current_user.id)


# =============================================================================
# 5. OFFERS & ALLOCATIONS
# =============================================================================

@housing_router.post(
    "/offers",
    response_model=HousingOfferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue formal accommodation offer to student",
)
async def create_offer(
    payload: HousingOfferCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_OFFER_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.create_offer(payload)


@housing_router.post(
    "/offers/{offer_id}/respond",
    response_model=HousingOfferResponse,
    summary="Accept or decline housing offer",
)
async def respond_to_offer(
    offer_id: UUID,
    payload: HousingOfferRespond,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_REQUEST_SUBMIT_OWN))],
    student_id: UUID | None = Query(None),
):
    service = HousingService(db, tenant_ctx.tenant_id)
    target_student_id = await _resolve_student_id(db, tenant_ctx.tenant_id, current_user, student_id)
    return await service.respond_to_offer(offer_id, payload, target_student_id)


@housing_router.post(
    "/assignments",
    response_model=HousingAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Directly allocate student to room/bed",
)
async def allocate_student(
    payload: HousingAssignmentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_ASSIGNMENT_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.allocate_student(payload)


@housing_router.post(
    "/assignments/{assignment_id}/transfer",
    response_model=HousingAssignmentResponse,
    summary="Transfer student to another room or bed",
)
async def transfer_assignment(
    assignment_id: UUID,
    payload: HousingAssignmentTransferRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_ASSIGNMENT_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.transfer_assignment(assignment_id, payload)


# =============================================================================
# 6. AGREEMENTS & CHECK-IN/OUT
# =============================================================================

@housing_router.post(
    "/agreements",
    response_model=HousingAgreementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create accommodation lease agreement",
)
async def create_agreement(
    payload: HousingAgreementCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_AGREEMENT_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.create_agreement(payload)


@housing_router.post(
    "/check-in-out",
    response_model=HousingCheckInOutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record check-in or check-out with damage inspection",
)
async def record_check_in_out(
    payload: HousingCheckInOutCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_CHECKIN_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.record_check_in_out(payload, current_user.id)


# =============================================================================
# 7. INSPECTIONS & COMPLIANCE
# =============================================================================

@housing_router.post(
    "/inspections",
    response_model=HousingPropertyInspectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record property compliance, fire or safety inspection",
)
async def record_inspection(
    payload: HousingPropertyInspectionCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_INSPECTION_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.record_inspection(payload, current_user.id)


@housing_router.get(
    "/inspections",
    response_model=list[HousingPropertyInspectionResponse],
    summary="List property inspections",
)
async def list_inspections(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_INSPECTION_READ))],
    property_id: UUID | None = Query(None),
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.list_inspections(property_id)


# =============================================================================
# 8. MAINTENANCE & SERVICE REQUESTS
# =============================================================================

@housing_router.post(
    "/maintenance",
    response_model=HousingMaintenanceRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit housing maintenance request",
)
async def submit_maintenance(
    payload: HousingMaintenanceRequestCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_MAINTENANCE_SUBMIT))],
    student_id: UUID | None = Query(None),
):
    service = HousingService(db, tenant_ctx.tenant_id)
    target_student_id = await _resolve_student_id(db, tenant_ctx.tenant_id, current_user, student_id)
    return await service.submit_maintenance_request(payload, current_user.id, target_student_id)


@housing_router.get(
    "/maintenance",
    response_model=list[HousingMaintenanceRequestResponse],
    summary="List housing maintenance requests",
)
async def list_maintenance(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_PROPERTY_READ))],
    property_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.list_maintenance_requests(property_id=property_id, status=status_filter)


@housing_router.put(
    "/maintenance/{request_id}",
    response_model=HousingMaintenanceRequestResponse,
    summary="Update maintenance ticket status, resolution, and feedback",
)
async def update_maintenance(
    request_id: UUID,
    payload: HousingMaintenanceRequestUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_MAINTENANCE_MANAGE))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.update_maintenance_request(request_id, payload)


# =============================================================================
# 9. HOUSING ANALYTICS & OCCUPANCY
# =============================================================================

@housing_router.get(
    "/analytics",
    response_model=HousingAnalyticsSummaryResponse,
    summary="Get real-time housing capacity, occupancy, and compliance metrics",
)
async def get_housing_analytics(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(HOUSING_ANALYTICS_READ))],
):
    service = HousingService(db, tenant_ctx.tenant_id)
    return await service.get_housing_analytics()

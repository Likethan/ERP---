"""CampusOS Enterprise Transport, Fleet, Routes & Student Mobility API Router (Step 55).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    TRANSPORT_ALLOCATION_MANAGE,
    TRANSPORT_APPLICATION_REVIEW,
    TRANSPORT_APPLICATION_SUBMIT_OWN,
    TRANSPORT_BOARDING_RECORD,
    TRANSPORT_DRIVER_MANAGE,
    TRANSPORT_FINANCE_READ_AUTHORIZED,
    TRANSPORT_INCIDENT_MANAGE,
    TRANSPORT_REPORT_READ,
    TRANSPORT_ROUTE_MANAGE,
    TRANSPORT_ROUTE_READ,
    TRANSPORT_SERVICE_MANAGE,
    TRANSPORT_SERVICE_READ,
    TRANSPORT_TRACKING_READ_AUTHORIZED,
    TRANSPORT_TRIP_DISPATCH,
    TRANSPORT_TRIP_READ,
    TRANSPORT_VEHICLE_MANAGE,
    TRANSPORT_VEHICLE_READ,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.transport import (
    DriverComplianceStatusResponse,
    GenerateTransportInvoiceRequest,
    GenerateTransportInvoiceResponse,
    RouteUtilizationReportItem,
    TransportAllocationCreate,
    TransportAllocationResponse,
    TransportAllocationTransferRequest,
    TransportApplicationCreate,
    TransportApplicationResponse,
    TransportApplicationReviewRequest,
    TransportBoardingRecordResponse,
    TransportBoardingVerifyRequest,
    TransportDashboardResponse,
    TransportDriverCreate,
    TransportDriverResponse,
    TransportDriverUpdate,
    TransportFeePlanCreate,
    TransportFeePlanResponse,
    TransportFuelLogCreate,
    TransportFuelLogResponse,
    TransportIncidentCreate,
    TransportIncidentResponse,
    TransportIncidentUpdate,
    TransportLiveTrackingResponse,
    TransportLocationPingRequest,
    TransportRouteCreate,
    TransportRouteDetailResponse,
    TransportRouteResponse,
    TransportRouteUpdate,
    TransportServiceConfigCreate,
    TransportServiceConfigResponse,
    TransportServiceConfigUpdate,
    TransportStopCreate,
    TransportStopResponse,
    TransportStopUpdate,
    TransportTrackingSourceConfig,
    TransportTripCreate,
    TransportTripDispatch,
    TransportTripResponse,
    TransportVehicleCreate,
    TransportVehicleResponse,
    TransportVehicleUpdate,
    TripManifestResponse,
    VehicleComplianceStatusResponse,
)
from app.services.transport_service import TransportService

transport_router = APIRouter(prefix="/transport", tags=["Transport & Fleet Management"])


# =============================================================================
# 1. TRANSPORT OPERATIONS DASHBOARD
# =============================================================================


@transport_router.get(
    "/dashboard",
    response_model=TransportDashboardResponse,
    summary="Get centralized transport operations metrics",
)
async def get_transport_dashboard(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_SERVICE_READ))],
    campus_id: UUID | None = Query(None),
):
    return await TransportService.get_transport_dashboard(
        db, tenant.tenant_id, campus_id=campus_id
    )


# =============================================================================
# 2. SERVICE CONFIGURATION
# =============================================================================


@transport_router.get(
    "/services",
    response_model=list[TransportServiceConfigResponse],
    summary="List transport service configurations",
)
async def list_services(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_SERVICE_READ))],
    campus_id: UUID | None = Query(None),
    is_active: bool | None = Query(None),
):
    return await TransportService.list_service_configs(
        db, tenant.tenant_id, campus_id=campus_id, is_active=is_active
    )


@transport_router.post(
    "/services",
    response_model=TransportServiceConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transport service configuration",
)
async def create_service(
    payload: TransportServiceConfigCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_SERVICE_MANAGE))],
):
    return await TransportService.create_service_config(db, tenant.tenant_id, payload)


@transport_router.get(
    "/services/{config_id}",
    response_model=TransportServiceConfigResponse,
    summary="Get transport service configuration detail",
)
async def get_service(
    config_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_SERVICE_READ))],
):
    return await TransportService.get_service_config(db, tenant.tenant_id, config_id)


@transport_router.put(
    "/services/{config_id}",
    response_model=TransportServiceConfigResponse,
    summary="Update transport service configuration",
)
async def update_service(
    config_id: UUID,
    payload: TransportServiceConfigUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_SERVICE_MANAGE))],
):
    return await TransportService.update_service_config(
        db, tenant.tenant_id, config_id, payload
    )


# =============================================================================
# 3. VEHICLES & FLEET REGISTRY
# =============================================================================


@transport_router.get(
    "/vehicles",
    response_model=list[TransportVehicleResponse],
    summary="List institutional transport vehicles",
)
async def list_vehicles(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_VEHICLE_READ))],
    campus_id: UUID | None = Query(None),
    status: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
):
    return await TransportService.list_vehicles(
        db,
        tenant.tenant_id,
        campus_id=campus_id,
        status=status,
        category=category,
        search=search,
    )


@transport_router.post(
    "/vehicles",
    response_model=TransportVehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a vehicle into institutional fleet",
)
async def create_vehicle(
    payload: TransportVehicleCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_VEHICLE_MANAGE))],
):
    return await TransportService.create_vehicle(db, tenant.tenant_id, payload)


@transport_router.get(
    "/vehicles/{vehicle_id}",
    response_model=TransportVehicleResponse,
    summary="Get vehicle details",
)
async def get_vehicle(
    vehicle_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_VEHICLE_READ))],
):
    return await TransportService.get_vehicle(db, tenant.tenant_id, vehicle_id)


@transport_router.put(
    "/vehicles/{vehicle_id}",
    response_model=TransportVehicleResponse,
    summary="Update vehicle details or status",
)
async def update_vehicle(
    vehicle_id: UUID,
    payload: TransportVehicleUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_VEHICLE_MANAGE))],
):
    return await TransportService.update_vehicle(
        db, tenant.tenant_id, vehicle_id, payload
    )


@transport_router.get(
    "/vehicles/{vehicle_id}/compliance",
    response_model=VehicleComplianceStatusResponse,
    summary="Check vehicle safety, fitness, and insurance compliance",
)
async def get_vehicle_compliance(
    vehicle_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_VEHICLE_READ))],
):
    return await TransportService.get_vehicle_compliance(
        db, tenant.tenant_id, vehicle_id
    )


@transport_router.post(
    "/vehicles/{vehicle_id}/defect",
    summary="Report vehicle defect and trigger Asset Maintenance work order",
)
async def report_vehicle_defect(
    vehicle_id: UUID,
    defect_notes: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(TRANSPORT_VEHICLE_MANAGE))],
):
    wo = await TransportService.report_vehicle_defect(
        db, tenant.tenant_id, vehicle_id, defect_notes, current_user.id
    )
    return {
        "success": True,
        "work_order_id": str(wo.id),
        "work_order_number": wo.work_order_number,
        "status": wo.status,
    }


# =============================================================================
# 4. DRIVERS & PERSONNEL
# =============================================================================


@transport_router.get(
    "/drivers",
    response_model=list[TransportDriverResponse],
    summary="List institutional vehicle drivers",
)
async def list_drivers(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_DRIVER_MANAGE))],
    status: str | None = Query(None),
    search: str | None = Query(None),
):
    return await TransportService.list_drivers(
        db, tenant.tenant_id, status=status, search=search
    )


@transport_router.post(
    "/drivers",
    response_model=TransportDriverResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a driver profile",
)
async def create_driver(
    payload: TransportDriverCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_DRIVER_MANAGE))],
):
    return await TransportService.create_driver(db, tenant.tenant_id, payload)


@transport_router.get(
    "/drivers/{driver_id}",
    response_model=TransportDriverResponse,
    summary="Get driver profile",
)
async def get_driver(
    driver_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_DRIVER_MANAGE))],
):
    return await TransportService.get_driver(db, tenant.tenant_id, driver_id)


@transport_router.put(
    "/drivers/{driver_id}",
    response_model=TransportDriverResponse,
    summary="Update driver profile or credentials",
)
async def update_driver(
    driver_id: UUID,
    payload: TransportDriverUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_DRIVER_MANAGE))],
):
    return await TransportService.update_driver(
        db, tenant.tenant_id, driver_id, payload
    )


@transport_router.get(
    "/drivers/{driver_id}/compliance",
    response_model=DriverComplianceStatusResponse,
    summary="Check driving license and background verification compliance",
)
async def get_driver_compliance(
    driver_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_DRIVER_MANAGE))],
):
    return await TransportService.get_driver_compliance(
        db, tenant.tenant_id, driver_id
    )


# =============================================================================
# 5. ROUTES & STOPS
# =============================================================================


@transport_router.get(
    "/routes",
    response_model=list[TransportRouteResponse],
    summary="List transit routes",
)
async def list_routes(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ROUTE_READ))],
    campus_id: UUID | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
):
    return await TransportService.list_routes(
        db, tenant.tenant_id, campus_id=campus_id, status=status, search=search
    )


@transport_router.post(
    "/routes",
    response_model=TransportRouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transport route",
)
async def create_route(
    payload: TransportRouteCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ROUTE_MANAGE))],
):
    return await TransportService.create_route(db, tenant.tenant_id, payload)


@transport_router.get(
    "/routes/{route_id}",
    response_model=TransportRouteDetailResponse,
    summary="Get route details with ordered stops",
)
async def get_route(
    route_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ROUTE_READ))],
):
    return await TransportService.get_route(db, tenant.tenant_id, route_id)


@transport_router.put(
    "/routes/{route_id}",
    response_model=TransportRouteResponse,
    summary="Update route details",
)
async def update_route(
    route_id: UUID,
    payload: TransportRouteUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ROUTE_MANAGE))],
):
    return await TransportService.update_route(db, tenant.tenant_id, route_id, payload)


@transport_router.get(
    "/routes/{route_id}/stops",
    response_model=list[TransportStopResponse],
    summary="List ordered stops along a transit route",
)
async def list_stops(
    route_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ROUTE_READ))],
):
    return await TransportService.list_stops(db, tenant.tenant_id, route_id)


@transport_router.post(
    "/routes/{route_id}/stops",
    response_model=TransportStopResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a stop to a route",
)
async def create_stop(
    route_id: UUID,
    payload: TransportStopCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ROUTE_MANAGE))],
):
    return await TransportService.create_stop(db, tenant.tenant_id, route_id, payload)


@transport_router.put(
    "/routes/{route_id}/stops/{stop_id}",
    response_model=TransportStopResponse,
    summary="Update a stop",
)
async def update_stop(
    route_id: UUID,
    stop_id: UUID,
    payload: TransportStopUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ROUTE_MANAGE))],
):
    return await TransportService.update_stop(
        db, tenant.tenant_id, route_id, stop_id, payload
    )


# =============================================================================
# 6. APPLICATIONS & SUBSCRIPTIONS
# =============================================================================


@transport_router.get(
    "/applications",
    response_model=list[TransportApplicationResponse],
    summary="List transport pass applications",
)
async def list_applications(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_APPLICATION_REVIEW))],
    student_id: UUID | None = Query(None),
    route_id: UUID | None = Query(None),
    status: str | None = Query(None),
):
    return await TransportService.list_applications(
        db, tenant.tenant_id, student_id=student_id, route_id=route_id, status=status
    )


@transport_router.post(
    "/applications",
    response_model=TransportApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit student transport application",
)
async def submit_application(
    payload: TransportApplicationCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_APPLICATION_SUBMIT_OWN))],
):
    return await TransportService.submit_application(db, tenant.tenant_id, payload)


@transport_router.put(
    "/applications/{application_id}/review",
    response_model=TransportApplicationResponse,
    summary="Review, score, approve, or reject student transport application",
)
async def review_application(
    application_id: UUID,
    payload: TransportApplicationReviewRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(TRANSPORT_APPLICATION_REVIEW))],
):
    return await TransportService.review_application(
        db, tenant.tenant_id, application_id, payload, reviewer_id=current_user.id
    )


# =============================================================================
# 7. SEAT ALLOCATIONS & PASSES
# =============================================================================


@transport_router.get(
    "/allocations",
    response_model=list[TransportAllocationResponse],
    summary="List confirmed transport seat allocations",
)
async def list_allocations(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ALLOCATION_MANAGE))],
    route_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    status: str | None = Query(None),
):
    return await TransportService.list_allocations(
        db, tenant.tenant_id, route_id=route_id, student_id=student_id, status=status
    )


@transport_router.post(
    "/allocations",
    response_model=TransportAllocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Allocate a passenger seat and issue transport pass",
)
async def allocate_passenger(
    payload: TransportAllocationCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ALLOCATION_MANAGE))],
):
    return await TransportService.allocate_passenger(db, tenant.tenant_id, payload)


@transport_router.post(
    "/allocations/{allocation_id}/transfer",
    response_model=TransportAllocationResponse,
    summary="Transfer passenger to another route or stop",
)
async def transfer_allocation(
    allocation_id: UUID,
    payload: TransportAllocationTransferRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ALLOCATION_MANAGE))],
):
    return await TransportService.transfer_allocation(
        db, tenant.tenant_id, allocation_id, payload
    )


@transport_router.post(
    "/allocations/{allocation_id}/cancel",
    response_model=TransportAllocationResponse,
    summary="Cancel passenger transport pass and release capacity",
)
async def cancel_allocation(
    allocation_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_ALLOCATION_MANAGE))],
    reason: str | None = Query(None),
):
    return await TransportService.cancel_allocation(
        db, tenant.tenant_id, allocation_id, cancellation_reason=reason
    )


# =============================================================================
# 8. TRIP SCHEDULING & DISPATCH
# =============================================================================


@transport_router.get(
    "/trips",
    response_model=list[TransportTripResponse],
    summary="List scheduled and operational transport trips",
)
async def list_trips(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_TRIP_READ))],
    trip_date: date | None = Query(None),
    route_id: UUID | None = Query(None),
    status: str | None = Query(None),
):
    return await TransportService.list_trips(
        db, tenant.tenant_id, trip_date=trip_date, route_id=route_id, status=status
    )


@transport_router.post(
    "/trips",
    response_model=TransportTripResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a transport trip and generate passenger manifest",
)
async def schedule_trip(
    payload: TransportTripCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_TRIP_DISPATCH))],
):
    return await TransportService.schedule_trip(db, tenant.tenant_id, payload)


@transport_router.get(
    "/trips/{trip_id}",
    response_model=TransportTripResponse,
    summary="Get trip operational details",
)
async def get_trip(
    trip_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_TRIP_READ))],
):
    return await TransportService.get_trip(db, tenant.tenant_id, trip_id)


@transport_router.post(
    "/trips/{trip_id}/dispatch",
    response_model=TransportTripResponse,
    summary="Dispatch a transport trip with pre-trip checklist verification",
)
async def dispatch_trip(
    trip_id: UUID,
    payload: TransportTripDispatch,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(TRANSPORT_TRIP_DISPATCH))],
):
    return await TransportService.dispatch_trip(
        db, tenant.tenant_id, trip_id, payload, dispatcher_id=current_user.id
    )


@transport_router.post(
    "/trips/{trip_id}/complete",
    response_model=TransportTripResponse,
    summary="Complete a transport trip and record final odometer reading",
)
async def complete_trip(
    trip_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_TRIP_DISPATCH))],
    end_odometer_km: float | None = Query(None),
):
    return await TransportService.complete_trip(
        db,
        tenant.tenant_id,
        trip_id,
        end_odometer_km=None if end_odometer_km is None else Decimal(str(end_odometer_km)),
    )


@transport_router.get(
    "/trips/{trip_id}/manifest",
    response_model=TripManifestResponse,
    summary="Get trip passenger manifest and boarding statistics",
)
async def get_trip_manifest(
    trip_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_TRIP_READ))],
):
    return await TransportService.get_trip_manifest(db, tenant.tenant_id, trip_id)


@transport_router.post(
    "/trips/{trip_id}/boarding",
    response_model=TransportBoardingRecordResponse,
    summary="Verify student boarding or drop-off",
)
async def record_boarding(
    trip_id: UUID,
    payload: TransportBoardingVerifyRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(TRANSPORT_BOARDING_RECORD))],
):
    return await TransportService.record_boarding(
        db, tenant.tenant_id, trip_id, payload, verifier_id=current_user.id
    )


# =============================================================================
# 9. TELEMATICS & LIVE TRACKING
# =============================================================================


@transport_router.get(
    "/tracking/{vehicle_id}",
    response_model=TransportLiveTrackingResponse,
    summary="Get vehicle telemetry status with truthful location freshness",
)
async def get_vehicle_tracking(
    vehicle_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_TRACKING_READ_AUTHORIZED))],
):
    return await TransportService.get_live_tracking(db, tenant.tenant_id, vehicle_id)


@transport_router.post(
    "/tracking/ping",
    summary="Ingest GPS location fix from authorized tracking provider",
)
async def record_tracking_ping(
    payload: TransportLocationPingRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_SERVICE_MANAGE))],
):
    snap = await TransportService.record_location_ping(db, tenant.tenant_id, payload)
    return {
        "success": True,
        "snapshot_id": str(snap.id),
        "recorded_at": snap.recorded_at.isoformat(),
    }


@transport_router.post(
    "/tracking/{vehicle_id}/config",
    summary="Configure telematics provider integration boundary for a vehicle",
)
async def configure_tracking_source(
    vehicle_id: UUID,
    payload: TransportTrackingSourceConfig,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_SERVICE_MANAGE))],
):
    source = await TransportService.configure_tracking_source(
        db, tenant.tenant_id, vehicle_id, payload
    )
    return {
        "success": True,
        "vehicle_id": str(source.vehicle_id),
        "provider_name": source.provider_name,
        "is_enabled": source.is_enabled,
        "status": source.status,
    }


# =============================================================================
# 10. TRANSPORT FEES & FINANCE
# =============================================================================


@transport_router.get(
    "/fee-plans",
    response_model=list[TransportFeePlanResponse],
    summary="List transport fee schedules",
)
async def list_fee_plans(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_FINANCE_READ_AUTHORIZED))],
    is_active: bool | None = Query(None),
):
    return await TransportService.list_fee_plans(
        db, tenant.tenant_id, is_active=is_active
    )


@transport_router.post(
    "/fee-plans",
    response_model=TransportFeePlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transport fee schedule",
)
async def create_fee_plan(
    payload: TransportFeePlanCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_FINANCE_READ_AUTHORIZED))],
):
    return await TransportService.create_fee_plan(db, tenant.tenant_id, payload)


@transport_router.post(
    "/generate-invoices",
    response_model=GenerateTransportInvoiceResponse,
    summary="Generate authoritative Finance module invoices for transport allocations",
)
async def generate_transport_invoices(
    payload: GenerateTransportInvoiceRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(TRANSPORT_FINANCE_READ_AUTHORIZED))],
):
    return await TransportService.generate_transport_invoices(
        db, tenant.tenant_id, payload, generated_by=current_user.id
    )


# =============================================================================
# 11. FUEL & OPERATING EXPENSES
# =============================================================================


@transport_router.get(
    "/fuel-logs",
    response_model=list[TransportFuelLogResponse],
    summary="List vehicle fueling logs and operating expenses",
)
async def list_fuel_logs(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_SERVICE_READ))],
    vehicle_id: UUID | None = Query(None),
    driver_id: UUID | None = Query(None),
):
    return await TransportService.list_fuel_logs(
        db, tenant.tenant_id, vehicle_id=vehicle_id, driver_id=driver_id
    )


@transport_router.post(
    "/fuel-logs",
    response_model=TransportFuelLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record vehicle fuel transaction with odometer validation",
)
async def create_fuel_log(
    payload: TransportFuelLogCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(TRANSPORT_SERVICE_MANAGE))],
):
    return await TransportService.create_fuel_log(
        db, tenant.tenant_id, payload, logged_by_id=current_user.id
    )


# =============================================================================
# 12. INCIDENTS & SAFETY
# =============================================================================


@transport_router.get(
    "/incidents",
    response_model=list[TransportIncidentResponse],
    summary="List transport safety and breakdown incidents",
)
async def list_incidents(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_INCIDENT_MANAGE))],
    severity: str | None = Query(None),
    status: str | None = Query(None),
):
    return await TransportService.list_incidents(
        db, tenant.tenant_id, severity=severity, status=status
    )


@transport_router.post(
    "/incidents",
    response_model=TransportIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a transport safety incident or vehicle breakdown",
)
async def report_incident(
    payload: TransportIncidentCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(TRANSPORT_INCIDENT_MANAGE))],
):
    return await TransportService.report_incident(
        db, tenant.tenant_id, payload, reporter_id=current_user.id
    )


@transport_router.put(
    "/incidents/{incident_id}",
    response_model=TransportIncidentResponse,
    summary="Update or resolve transport incident",
)
async def update_incident(
    incident_id: UUID,
    payload: TransportIncidentUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_INCIDENT_MANAGE))],
):
    return await TransportService.update_incident(
        db, tenant.tenant_id, incident_id, payload
    )


# =============================================================================
# 13. OPERATIONAL REPORTS & ANALYTICS
# =============================================================================


@transport_router.get(
    "/reports/route-utilization",
    response_model=list[RouteUtilizationReportItem],
    summary="Route passenger capacity utilization report",
)
async def get_route_utilization_report(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(TRANSPORT_REPORT_READ))],
):
    return await TransportService.get_route_utilization_report(db, tenant.tenant_id)

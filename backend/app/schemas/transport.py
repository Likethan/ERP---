"""CampusOS Enterprise Transport, Fleet, Routes & Student Mobility Schemas (Step 55).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.transport import (
    BoardingStatus,
    DriverStatus,
    FeePlanBillingCycle,
    FuelType,
    IncidentStatus,
    RouteDirection,
    RouteStatus,
    ServiceWindow,
    TrackingProviderStatus,
    TransportAllocationStatus,
    TransportApplicationStatus,
    TransportFeeStatus,
    TransportIncidentSeverity,
    TransportIncidentType,
    TransportServiceType,
    TripStatus,
    VehicleCategory,
    VehicleStatus,
    VerificationMethod,
    VerificationStatus,
    WaitlistStatus,
)

# =============================================================================
# 1. SERVICE CONFIGURATION SCHEMAS
# =============================================================================


class TransportServiceConfigBase(BaseModel):
    service_code: str = Field(..., max_length=32)
    service_name: str = Field(..., max_length=128)
    campus_id: UUID | None = None
    academic_year_id: UUID | None = None
    zone_code: str | None = None
    operating_period_start: date | None = None
    operating_period_end: date | None = None
    eligibility_criteria: dict[str, Any] | None = None
    capacity_policy: dict[str, Any] | None = None
    is_active: bool = True


class TransportServiceConfigCreate(TransportServiceConfigBase):
    pass


class TransportServiceConfigUpdate(BaseModel):
    service_name: str | None = None
    campus_id: UUID | None = None
    academic_year_id: UUID | None = None
    zone_code: str | None = None
    operating_period_start: date | None = None
    operating_period_end: date | None = None
    eligibility_criteria: dict[str, Any] | None = None
    capacity_policy: dict[str, Any] | None = None
    is_active: bool | None = None


class TransportServiceConfigResponse(TransportServiceConfigBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. VEHICLE & FLEET SCHEMAS
# =============================================================================


class TransportVehicleBase(BaseModel):
    registration_number: str = Field(..., max_length=32)
    fleet_identifier: str | None = Field(None, max_length=64)
    asset_id: UUID | None = None
    campus_id: UUID | None = None
    vehicle_category: VehicleCategory = VehicleCategory.BUS
    make: str | None = None
    model: str | None = None
    manufacturing_year: int | None = None
    capacity: int = Field(..., gt=0, description="Total seating capacity")
    accessible_seating_capacity: int = Field(0, ge=0)
    permitted_passenger_capacity: int | None = None
    insurance_policy_number: str | None = None
    insurance_expiry: date
    fitness_certificate_number: str | None = None
    fitness_certificate_expiry: date
    permit_number: str | None = None
    permit_expiry: date | None = None
    pollution_certificate_expiry: date | None = None
    fuel_type: FuelType = FuelType.DIESEL
    operational_depot: str | None = None
    status: VehicleStatus = VehicleStatus.ACTIVE
    current_odometer_km: Decimal = Decimal("0.00")
    safety_equipment_details: dict[str, Any] | None = None
    is_active: bool = True


class TransportVehicleCreate(TransportVehicleBase):
    pass


class TransportVehicleUpdate(BaseModel):
    fleet_identifier: str | None = None
    asset_id: UUID | None = None
    campus_id: UUID | None = None
    vehicle_category: VehicleCategory | None = None
    make: str | None = None
    model: str | None = None
    manufacturing_year: int | None = None
    capacity: int | None = Field(None, gt=0)
    accessible_seating_capacity: int | None = Field(None, ge=0)
    permitted_passenger_capacity: int | None = None
    insurance_policy_number: str | None = None
    insurance_expiry: date | None = None
    fitness_certificate_number: str | None = None
    fitness_certificate_expiry: date | None = None
    permit_number: str | None = None
    permit_expiry: date | None = None
    pollution_certificate_expiry: date | None = None
    fuel_type: FuelType | None = None
    operational_depot: str | None = None
    status: VehicleStatus | None = None
    current_odometer_km: Decimal | None = None
    safety_equipment_details: dict[str, Any] | None = None
    is_active: bool | None = None


class TransportVehicleResponse(TransportVehicleBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleComplianceStatusResponse(BaseModel):
    vehicle_id: UUID
    registration_number: str
    status: VehicleStatus
    insurance_expiry: date
    is_insurance_expired: bool
    fitness_certificate_expiry: date
    is_fitness_expired: bool
    permit_expiry: date | None = None
    is_permit_expired: bool = False
    is_compliant_for_dispatch: bool
    compliance_remarks: list[str]


# =============================================================================
# 3. DRIVER & PERSONNEL SCHEMAS
# =============================================================================


class TransportDriverBase(BaseModel):
    license_number: str = Field(..., max_length=64)
    full_name: str = Field(..., max_length=128)
    user_id: UUID | None = None
    employee_id: UUID | None = None
    license_categories: list[str] | None = None
    license_expiry: date
    phone_number: str = Field(..., max_length=32)
    email: str | None = None
    badge_number: str | None = None
    badge_expiry: date | None = None
    certifications: dict[str, Any] | None = None
    background_verification_status: VerificationStatus = VerificationStatus.VERIFIED
    shift_preference: str | None = None
    status: DriverStatus = DriverStatus.ACTIVE
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    is_active: bool = True


class TransportDriverCreate(TransportDriverBase):
    pass


class TransportDriverUpdate(BaseModel):
    full_name: str | None = None
    user_id: UUID | None = None
    employee_id: UUID | None = None
    license_number: str | None = None
    license_categories: list[str] | None = None
    license_expiry: date | None = None
    phone_number: str | None = None
    email: str | None = None
    badge_number: str | None = None
    badge_expiry: date | None = None
    certifications: dict[str, Any] | None = None
    background_verification_status: VerificationStatus | None = None
    shift_preference: str | None = None
    status: DriverStatus | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    is_active: bool | None = None


class TransportDriverResponse(TransportDriverBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DriverComplianceStatusResponse(BaseModel):
    driver_id: UUID
    full_name: str
    license_number: str
    status: DriverStatus
    license_expiry: date
    is_license_expired: bool
    background_verification_status: VerificationStatus
    is_compliant_for_dispatch: bool
    compliance_remarks: list[str]


# =============================================================================
# 4. ROUTE & STOP SCHEMAS
# =============================================================================


class TransportStopBase(BaseModel):
    stop_name: str = Field(..., max_length=128)
    stop_sequence: int = Field(..., ge=1)
    pickup_time: time
    stop_code: str | None = None
    drop_time: time | None = None
    address: str | None = None
    landmark: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    fare_annual: Decimal = Decimal("0.00")
    fare_term: Decimal = Decimal("0.00")
    fare_monthly: Decimal = Decimal("0.00")
    max_boarding_capacity: int | None = None
    is_active: bool = True


class TransportStopCreate(TransportStopBase):
    pass


class TransportStopUpdate(BaseModel):
    stop_name: str | None = None
    stop_sequence: int | None = Field(None, ge=1)
    pickup_time: time | None = None
    drop_time: time | None = None
    stop_code: str | None = None
    address: str | None = None
    landmark: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    fare_annual: Decimal | None = None
    fare_term: Decimal | None = None
    fare_monthly: Decimal | None = None
    max_boarding_capacity: int | None = None
    is_active: bool | None = None


class TransportStopResponse(TransportStopBase):
    id: UUID
    route_id: UUID
    tenant_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class TransportRouteBase(BaseModel):
    route_code: str = Field(..., max_length=32)
    route_name: str = Field(..., max_length=128)
    campus_id: UUID | None = None
    description: str | None = None
    start_point: str = "Campus Depot"
    end_point: str = "Terminal"
    distance_km: Decimal = Decimal("0.00")
    estimated_duration_minutes: int = 60
    morning_departure_time: time | None = None
    evening_return_time: time | None = None
    vehicle_id: UUID | None = None
    driver_id: UUID | None = None
    capacity: int = Field(52, gt=0)
    direction: RouteDirection = RouteDirection.ROUND_TRIP
    status: RouteStatus = RouteStatus.ACTIVE
    is_active: bool = True


class TransportRouteCreate(TransportRouteBase):
    stops: list[TransportStopCreate] | None = None


class TransportRouteUpdate(BaseModel):
    route_name: str | None = None
    campus_id: UUID | None = None
    description: str | None = None
    start_point: str | None = None
    end_point: str | None = None
    distance_km: Decimal | None = None
    estimated_duration_minutes: int | None = None
    morning_departure_time: time | None = None
    evening_return_time: time | None = None
    vehicle_id: UUID | None = None
    driver_id: UUID | None = None
    capacity: int | None = Field(None, gt=0)
    direction: RouteDirection | None = None
    status: RouteStatus | None = None
    is_active: bool | None = None


class TransportRouteResponse(TransportRouteBase):
    id: UUID
    tenant_id: UUID
    allocated_students: int = 0
    stops_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransportRouteDetailResponse(TransportRouteResponse):
    stops: list[TransportStopResponse] = []
    vehicle: TransportVehicleResponse | None = None
    driver: TransportDriverResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. APPLICATION & SUBSCRIPTION SCHEMAS
# =============================================================================


class TransportApplicationCreate(BaseModel):
    student_id: UUID
    academic_year_id: UUID
    preferred_route_id: UUID
    preferred_stop_id: UUID
    service_type: TransportServiceType = TransportServiceType.ROUND_TRIP
    accessibility_needed: bool = False
    special_requests: str | None = None
    priority_score: Decimal = Decimal("0.00")


class TransportApplicationReviewRequest(BaseModel):
    status: TransportApplicationStatus
    rejection_reason: str | None = None
    assigned_seat_number: str | None = None


class TransportApplicationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    application_number: str
    student_id: UUID
    academic_year_id: UUID
    preferred_route_id: UUID
    preferred_stop_id: UUID
    service_type: TransportServiceType
    status: TransportApplicationStatus
    priority_score: Decimal
    accessibility_needed: bool
    special_requests: str | None = None
    reviewer_user_id: UUID | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransportAllocationCreate(BaseModel):
    student_id: UUID
    academic_year_id: UUID
    route_id: UUID
    stop_id: UUID
    vehicle_id: UUID | None = None
    service_type: TransportServiceType = TransportServiceType.ROUND_TRIP
    seat_number: str | None = None
    valid_from: date = Field(default_factory=date.today)
    valid_until: date | None = None


class TransportAllocationTransferRequest(BaseModel):
    new_route_id: UUID
    new_stop_id: UUID
    new_seat_number: str | None = None
    reason: str | None = None


class TransportAllocationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    pass_number: str
    student_id: UUID
    academic_year_id: UUID
    route_id: UUID
    stop_id: UUID
    vehicle_id: UUID | None = None
    service_type: TransportServiceType
    seat_number: str | None = None
    status: TransportAllocationStatus
    valid_from: date
    valid_until: date | None = None
    finance_invoice_id: UUID | None = None
    fee_status: TransportFeeStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 6. BATCH ALLOCATION & WAITLIST
# =============================================================================


class BatchAllocationPreviewRequest(BaseModel):
    academic_year_id: UUID
    route_id: UUID | None = None


class BatchAllocationCandidate(BaseModel):
    application_id: UUID
    student_id: UUID
    preferred_route_id: UUID
    preferred_stop_id: UUID
    priority_score: Decimal
    can_allocate: bool
    reason: str | None = None


class BatchAllocationPreviewResponse(BaseModel):
    route_id: UUID | None = None
    total_applications: int
    eligible_count: int
    allocatable_count: int
    waitlist_count: int
    candidates: list[BatchAllocationCandidate]


class BatchAllocationCommitRequest(BaseModel):
    academic_year_id: UUID
    application_ids: list[UUID] | None = None
    route_id: UUID | None = None


class BatchAllocationCommitResponse(BaseModel):
    success: bool
    allocated_count: int
    waitlisted_count: int
    allocations: list[TransportAllocationResponse]


class TransportWaitlistResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    route_id: UUID
    stop_id: UUID
    student_id: UUID
    application_id: UUID | None = None
    priority_score: Decimal
    queue_position: int
    status: WaitlistStatus
    offered_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 7. TRIP SCHEDULING, DISPATCH & BOARDING
# =============================================================================


class TransportTripCreate(BaseModel):
    route_id: UUID
    vehicle_id: UUID
    driver_id: UUID
    trip_date: date
    service_window: ServiceWindow = ServiceWindow.MORNING_PICKUP
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    pre_trip_checklist_completed: bool = False
    checklist_notes: dict[str, Any] | None = None


class TransportTripDispatch(BaseModel):
    substitute_vehicle_id: UUID | None = None
    substitute_driver_id: UUID | None = None
    actual_start_time: datetime | None = None
    start_odometer_km: Decimal | None = None
    pre_trip_checklist_completed: bool = True
    checklist_notes: dict[str, Any] | None = None
    dispatch_notes: str | None = None


class TransportTripChecklist(BaseModel):
    brakes_ok: bool = True
    tires_ok: bool = True
    lights_ok: bool = True
    emergency_exit_clear: bool = True
    first_aid_kit_present: bool = True
    fire_extinguisher_present: bool = True
    cleanliness_acceptable: bool = True
    defects_reported: str | None = None


class TransportTripUpdate(BaseModel):
    status: TripStatus | None = None
    actual_start_time: datetime | None = None
    actual_end_time: datetime | None = None
    start_odometer_km: Decimal | None = None
    end_odometer_km: Decimal | None = None
    cancellation_reason: str | None = None
    disruption_notes: str | None = None


class TransportTripResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    trip_number: str
    route_id: UUID
    vehicle_id: UUID
    driver_id: UUID
    trip_date: date
    service_window: ServiceWindow
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    actual_start_time: datetime | None = None
    actual_end_time: datetime | None = None
    start_odometer_km: Decimal | None = None
    end_odometer_km: Decimal | None = None
    status: TripStatus
    pre_trip_checklist_completed: bool
    checklist_notes: dict[str, Any] | None = None
    cancellation_reason: str | None = None
    disruption_notes: str | None = None
    dispatched_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransportBoardingRecordCreate(BaseModel):
    student_id: UUID
    stop_id: UUID
    allocation_id: UUID | None = None
    boarding_status: BoardingStatus = BoardingStatus.BOARDED
    boarding_time: datetime | None = None
    verification_method: VerificationMethod = VerificationMethod.MANUAL
    remarks: str | None = None


class TransportBoardingVerifyRequest(BaseModel):
    student_id: UUID
    stop_id: UUID
    verification_method: VerificationMethod = VerificationMethod.QR_CODE
    boarding_status: BoardingStatus = BoardingStatus.BOARDED


class TransportBoardingRecordResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    trip_id: UUID
    student_id: UUID
    allocation_id: UUID | None = None
    stop_id: UUID
    boarding_status: BoardingStatus
    boarding_time: datetime | None = None
    drop_off_time: datetime | None = None
    verification_method: VerificationMethod
    verified_by_user_id: UUID | None = None
    remarks: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TripManifestResponse(BaseModel):
    trip: TransportTripResponse
    total_manifest_count: int
    boarded_count: int
    absent_count: int
    pending_count: int
    passengers: list[TransportBoardingRecordResponse]


# =============================================================================
# 8. LIVE TRACKING BOUNDARY & LOCATION SNAPSHOTS
# =============================================================================


class TransportTrackingSourceConfig(BaseModel):
    provider_name: str
    device_identifier: str | None = None
    is_enabled: bool = True


class TransportLocationPingRequest(BaseModel):
    vehicle_id: UUID
    trip_id: UUID | None = None
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    speed_kmh: Decimal = Decimal("0.00")
    heading_degrees: Decimal | None = None
    odometer_reading: Decimal | None = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    data_source: str = "TELEMATICS"


class TransportLiveTrackingResponse(BaseModel):
    vehicle_id: UUID
    registration_number: str
    tracking_enabled: bool
    status: TrackingProviderStatus
    last_known_location: dict[str, Any] | None = None
    is_data_stale: bool = True
    freshness_seconds: int | None = None
    telemetry_message: str


# =============================================================================
# 9. TRANSPORT FEES & FINANCE SCHEMAS
# =============================================================================


class TransportFeePlanBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    academic_year_id: UUID | None = None
    campus_id: UUID | None = None
    route_id: UUID | None = None
    stop_id: UUID | None = None
    service_type: TransportServiceType = TransportServiceType.ROUND_TRIP
    amount: Decimal = Field(..., gt=0)
    currency: str = "INR"
    billing_cycle: FeePlanBillingCycle = FeePlanBillingCycle.ANNUAL
    is_active: bool = True


class TransportFeePlanCreate(TransportFeePlanBase):
    pass


class TransportFeePlanResponse(TransportFeePlanBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateTransportInvoiceRequest(BaseModel):
    allocation_ids: list[UUID] | None = None
    route_id: UUID | None = None
    due_days: int = 15


class GenerateTransportInvoiceResponse(BaseModel):
    invoices_created: int
    invoice_ids: list[UUID]
    skipped_count: int
    total_billed_amount: Decimal


# =============================================================================
# 10. FUEL & OPERATING EXPENSES
# =============================================================================


class TransportFuelLogCreate(BaseModel):
    vehicle_id: UUID
    fuel_date: date = Field(default_factory=date.today)
    odometer_reading: Decimal = Field(..., gt=0)
    fuel_quantity_liters: Decimal = Field(..., gt=0)
    fuel_cost_total: Decimal = Field(..., gt=0)
    driver_id: UUID | None = None
    trip_id: UUID | None = None
    fuel_station_name: str | None = None
    receipt_number: str | None = None
    notes: str | None = None


class TransportFuelLogResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    vehicle_id: UUID
    driver_id: UUID | None = None
    trip_id: UUID | None = None
    fuel_date: date
    odometer_reading: Decimal
    fuel_quantity_liters: Decimal
    fuel_cost_total: Decimal
    fuel_station_name: str | None = None
    receipt_number: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 11. TRANSPORT INCIDENTS & SAFETY
# =============================================================================


class TransportIncidentCreate(BaseModel):
    trip_id: UUID | None = None
    vehicle_id: UUID | None = None
    driver_id: UUID | None = None
    route_id: UUID | None = None
    incident_type: TransportIncidentType = TransportIncidentType.BREAKDOWN
    severity: TransportIncidentSeverity = TransportIncidentSeverity.MEDIUM
    incident_time: datetime = Field(default_factory=datetime.utcnow)
    location_description: str
    description: str
    action_taken: str | None = None
    involved_student_ids: list[str] | None = None
    emergency_services_contacted: bool = False


class TransportIncidentUpdate(BaseModel):
    severity: TransportIncidentSeverity | None = None
    status: IncidentStatus | None = None
    action_taken: str | None = None
    resolution_notes: str | None = None


class TransportIncidentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    incident_number: str
    trip_id: UUID | None = None
    vehicle_id: UUID | None = None
    driver_id: UUID | None = None
    route_id: UUID | None = None
    incident_type: TransportIncidentType
    severity: TransportIncidentSeverity
    incident_time: datetime
    location_description: str
    reporter_user_id: UUID | None = None
    description: str
    action_taken: str | None = None
    involved_student_ids: list[str] | None = None
    emergency_services_contacted: bool
    status: IncidentStatus
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 12. DASHBOARD & OPERATIONAL REPORTING
# =============================================================================


class TransportDashboardResponse(BaseModel):
    active_routes_count: int
    total_stops_count: int
    active_vehicles_count: int
    vehicles_under_maintenance_count: int
    active_drivers_count: int
    students_allocated_count: int
    route_capacity_utilization: float
    unassigned_students_count: int
    upcoming_vehicle_maintenance_count: int
    active_trips_today: int = 0
    completed_trips_today: int = 0
    incidents_reported_count: int = 0


class RouteUtilizationReportItem(BaseModel):
    route_id: UUID
    route_code: str
    route_name: str
    capacity: int
    allocated_students: int
    utilization_percentage: float
    stops_count: int
    vehicle_registration: str | None = None
    driver_name: str | None = None

"""Pydantic v2 schemas for Enterprise Hostel, Residential Life & Accommodation Management (Step 54).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.residential import (
    AccommodationApplicationStatus,
    ApplicationCycleStatus,
    BedStatus,
    CheckoutReason,
    FeePlanBillingCycle,
    HostelGender,
    HostelOperationalStatus,
    HostelType,
    MealType,
    NightAttendanceStatus,
    OutingStatus,
    OutingType,
    ResidentialIncidentSeverity,
    ResidentialIncidentStatus,
    ResidentialIncidentType,
    ResidentialServiceCategory,
    ResidentialServicePriority,
    ResidentialServiceStatus,
    RoomType,
    SafetyInspectionStatus,
)

# =============================================================================
# 1. HOSTEL & FACILITY INVENTORY SCHEMAS
# =============================================================================


class HostelBase(BaseModel):
    name: str = Field(..., max_length=128)
    code: str = Field(..., max_length=32)
    campus_id: UUID
    gender: HostelGender = HostelGender.MALE
    hostel_type: HostelType = HostelType.BOYS
    description: str | None = None
    address: str | None = None
    curfew_time: time | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    rules_summary: str | None = None
    amenities: list[str] | None = None
    visitor_policy: dict[str, Any] | None = None
    emergency_contacts: list[dict[str, Any]] | None = None
    warden_user_id: UUID | None = None
    assistant_warden_user_id: UUID | None = None


class HostelCreate(HostelBase):
    pass


class HostelUpdate(BaseModel):
    name: str | None = None
    gender: HostelGender | None = None
    hostel_type: HostelType | None = None
    status: HostelOperationalStatus | None = None
    description: str | None = None
    address: str | None = None
    curfew_time: time | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    rules_summary: str | None = None
    amenities: list[str] | None = None
    visitor_policy: dict[str, Any] | None = None
    emergency_contacts: list[dict[str, Any]] | None = None
    warden_user_id: UUID | None = None
    assistant_warden_user_id: UUID | None = None


class HostelResponse(HostelBase):
    id: UUID
    tenant_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    total_blocks: int = 0
    total_rooms: int = 0
    total_beds: int = 0
    occupied_beds: int = 0
    available_beds: int = 0
    occupancy_percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class HostelBlockCreate(BaseModel):
    name: str = Field(..., max_length=64)
    code: str | None = None
    description: str | None = None


class HostelBlockResponse(BaseModel):
    id: UUID
    hostel_id: UUID
    name: str
    code: str | None = None
    description: str | None = None
    floors_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class HostelFloorCreate(BaseModel):
    floor_number: int
    name: str | None = None
    is_accessible: bool = False


class HostelFloorResponse(BaseModel):
    id: UUID
    block_id: UUID
    floor_number: int
    name: str | None = None
    is_accessible: bool
    rooms_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class HostelRoomCreate(BaseModel):
    floor_id: UUID
    room_number: str = Field(..., max_length=32)
    room_type: RoomType = RoomType.DOUBLE
    capacity: int = 2
    is_accessible: bool = False
    is_air_conditioned: bool = False
    has_attached_bathroom: bool = False
    amenities: list[str] | None = None
    restrictions: dict[str, Any] | None = None


class HostelRoomUpdate(BaseModel):
    room_number: str | None = None
    room_type: RoomType | None = None
    capacity: int | None = None
    is_accessible: bool | None = None
    is_air_conditioned: bool | None = None
    has_attached_bathroom: bool | None = None
    status: HostelOperationalStatus | None = None
    amenities: list[str] | None = None
    restrictions: dict[str, Any] | None = None


class HostelRoomResponse(BaseModel):
    id: UUID
    floor_id: UUID
    room_number: str
    room_type: str
    capacity: int
    is_accessible: bool
    is_air_conditioned: bool
    has_attached_bathroom: bool
    status: str
    amenities: list[str] | None = None
    restrictions: dict[str, Any] | None = None
    beds_count: int = 0
    available_beds_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class HostelBedCreate(BaseModel):
    room_id: UUID
    bed_code: str = Field(..., max_length=16)


class HostelBedUpdate(BaseModel):
    status: BedStatus | None = None
    blocked_reason: str | None = None
    blocked_until: date | None = None


class HostelBedBlockRequest(BaseModel):
    blocked_reason: str
    blocked_until: date | None = None


class HostelBedResponse(BaseModel):
    id: UUID
    room_id: UUID
    bed_code: str
    is_available: bool
    status: str
    blocked_reason: str | None = None
    blocked_until: date | None = None
    reserved_until: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. ACCOMMODATION APPLICATION SCHEMAS
# =============================================================================


class ApplicationCycleCreate(BaseModel):
    academic_year_id: UUID
    cycle_name: str = Field(..., max_length=128)
    code: str = Field(..., max_length=32)
    start_date: date
    end_date: date
    max_applications: int | None = None
    eligibility_criteria: dict[str, Any] | None = None
    priority_rules: dict[str, Any] | None = None


class ApplicationCycleUpdate(BaseModel):
    cycle_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: ApplicationCycleStatus | None = None
    max_applications: int | None = None
    eligibility_criteria: dict[str, Any] | None = None
    priority_rules: dict[str, Any] | None = None


class ApplicationCycleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    cycle_name: str
    code: str
    start_date: date
    end_date: date
    status: str
    max_applications: int | None = None
    eligibility_criteria: dict[str, Any] | None = None
    priority_rules: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccommodationApplicationCreate(BaseModel):
    cycle_id: UUID
    student_id: UUID
    preferred_hostel_id: UUID | None = None
    preferred_room_type: RoomType = RoomType.DOUBLE
    special_requests: str | None = None
    accessibility_needed: bool = False
    disability_notes: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class AccommodationApplicationReview(BaseModel):
    status: AccommodationApplicationStatus  # APPROVED, WAITLISTED, REJECTED
    review_notes: str | None = None
    priority_score_override: Decimal | None = None


class AccommodationApplicationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    cycle_id: UUID
    student_id: UUID
    application_number: str
    preferred_hostel_id: UUID | None = None
    preferred_room_type: str
    special_requests: str | None = None
    accessibility_needed: bool
    disability_notes: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    priority_score: Decimal
    status: str
    reviewer_user_id: UUID | None = None
    review_notes: str | None = None
    reviewed_at: datetime | None = None
    allocated_bed_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. ALLOCATION SCHEMAS
# =============================================================================


class AllocationCreate(BaseModel):
    bed_id: UUID
    student_id: UUID
    academic_year_id: UUID
    application_id: UUID | None = None
    check_in_date: date
    check_out_date: date | None = None
    reserved_until: datetime | None = None
    notes: str | None = None


class AllocationTransferRequest(BaseModel):
    target_bed_id: UUID
    reallocation_reason: str = Field(..., min_length=3, max_length=255)
    notes: str | None = None


class BatchAllocationPreviewRequest(BaseModel):
    cycle_id: UUID
    hostel_id: UUID | None = None
    max_allocations: int = 50


class BatchAllocationPreviewItem(BaseModel):
    application_id: UUID
    student_id: UUID
    preferred_room_type: str
    priority_score: Decimal
    proposed_bed_id: UUID | None = None
    proposed_bed_code: str | None = None
    proposed_room_number: str | None = None
    is_eligible: bool
    rejection_reason: str | None = None


class BatchAllocationPreviewResponse(BaseModel):
    total_reviewed: int
    eligible_count: int
    ineligible_count: int
    items: list[BatchAllocationPreviewItem]


class BatchAllocationCommitRequest(BaseModel):
    allocations: list[AllocationCreate]


class BatchAllocationResultResponse(BaseModel):
    successful_count: int
    failed_count: int
    allocated_ids: list[UUID]
    errors: list[str]


class AllocationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    bed_id: UUID
    student_id: UUID
    academic_year_id: UUID
    application_id: UUID | None = None
    check_in_date: date
    check_out_date: date | None = None
    reserved_until: datetime | None = None
    status: str
    allocated_by_user_id: UUID | None = None
    reallocation_reason: str | None = None
    previous_bed_id: UUID | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. RESIDENT LIFECYCLE SCHEMAS
# =============================================================================


class ResidentCheckInRequest(BaseModel):
    allocation_id: UUID
    key_number: str | None = None
    facilities_condition_note: str | None = None
    inventory_handover: dict[str, Any] | None = None  # e.g. {"table": True, "chair": True, "mattress": True}
    expected_departure_date: date | None = None


class ResidentCheckOutRequest(BaseModel):
    checkout_reason: CheckoutReason = CheckoutReason.END_OF_TERM
    room_condition_on_checkout: str | None = None
    key_returned: bool = True
    damage_assessment_notes: str | None = None
    damage_charges_amount: Decimal = Decimal("0.00")
    create_damage_invoice: bool = False


class ResidentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    allocation_id: UUID
    student_id: UUID
    bed_id: UUID
    hostel_id: UUID
    academic_year_id: UUID
    status: str
    check_in_time: datetime
    checked_in_by_user_id: UUID | None = None
    key_card_issued: bool
    key_number: str | None = None
    facilities_condition_note: str | None = None
    inventory_handover: dict[str, Any] | None = None
    expected_departure_date: date | None = None
    check_out_time: datetime | None = None
    checked_out_by_user_id: UUID | None = None
    checkout_reason: str | None = None
    room_condition_on_checkout: str | None = None
    key_returned: bool
    damage_assessment_notes: str | None = None
    damage_charges_amount: Decimal
    damage_invoice_id: UUID | None = None
    cleared_by_finance: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. RESIDENTIAL FEES SCHEMAS
# =============================================================================


class HostelFeePlanCreate(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    hostel_id: UUID | None = None
    room_type: RoomType = RoomType.DOUBLE
    billing_cycle: FeePlanBillingCycle = FeePlanBillingCycle.SEMESTER
    rent_amount: Decimal
    mess_amount: Decimal = Decimal("0.00")
    deposit_amount: Decimal = Decimal("0.00")
    utility_amount: Decimal = Decimal("0.00")
    amenities_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    proration_rule: dict[str, Any] | None = None


class HostelFeePlanUpdate(BaseModel):
    name: str | None = None
    room_type: RoomType | None = None
    billing_cycle: FeePlanBillingCycle | None = None
    rent_amount: Decimal | None = None
    mess_amount: Decimal | None = None
    deposit_amount: Decimal | None = None
    utility_amount: Decimal | None = None
    amenities_amount: Decimal | None = None
    total_amount: Decimal | None = None
    is_active: bool | None = None
    proration_rule: dict[str, Any] | None = None


class HostelFeePlanResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    hostel_id: UUID | None = None
    room_type: str
    billing_cycle: str
    rent_amount: Decimal
    mess_amount: Decimal
    deposit_amount: Decimal
    utility_amount: Decimal
    amenities_amount: Decimal
    total_amount: Decimal
    is_active: bool
    proration_rule: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateHostelInvoiceRequest(BaseModel):
    student_id: UUID
    fee_plan_id: UUID
    academic_year_id: UUID
    due_days: int = 15
    apply_proration: bool = False
    proration_days: int | None = None


class HostelInvoiceResponse(BaseModel):
    invoice_id: UUID
    invoice_number: str
    student_id: UUID
    gross_amount: Decimal
    net_payable: Decimal
    due_date: date
    status: str


# =============================================================================
# 6. MESS & MEAL-PLAN SCHEMAS
# =============================================================================


class MealPlanCreate(BaseModel):
    hostel_id: UUID | None = None
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    meal_type: MealType = MealType.VEG
    description: str | None = None
    monthly_rate: Decimal
    daily_rate: Decimal = Decimal("0.00")
    serves_breakfast: bool = True
    serves_lunch: bool = True
    serves_snacks: bool = True
    serves_dinner: bool = True


class MealPlanUpdate(BaseModel):
    name: str | None = None
    meal_type: MealType | None = None
    description: str | None = None
    monthly_rate: Decimal | None = None
    daily_rate: Decimal | None = None
    serves_breakfast: bool | None = None
    serves_lunch: bool | None = None
    serves_snacks: bool | None = None
    serves_dinner: bool | None = None
    is_active: bool | None = None


class MealPlanResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    hostel_id: UUID | None = None
    code: str
    name: str
    meal_type: str
    description: str | None = None
    monthly_rate: Decimal
    daily_rate: Decimal
    serves_breakfast: bool
    serves_lunch: bool
    serves_snacks: bool
    serves_dinner: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealEnrollmentCreate(BaseModel):
    student_id: UUID
    meal_plan_id: UUID
    resident_id: UUID | None = None
    start_date: date
    end_date: date | None = None
    dietary_requirements: str | None = None


class MealEnrollmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    meal_plan_id: UUID
    resident_id: UUID | None = None
    start_date: date
    end_date: date | None = None
    dietary_requirements: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealHeadcountResponse(BaseModel):
    date: date
    hostel_id: UUID | None = None
    breakfast_count: int
    lunch_count: int
    snacks_count: int
    dinner_count: int
    vegetarian_count: int
    non_vegetarian_count: int


# =============================================================================
# 7. OUTINGS & LEAVES SCHEMAS
# =============================================================================


class OutingRequestCreate(BaseModel):
    student_id: UUID
    hostel_id: UUID | None = None
    outing_type: OutingType = OutingType.DAY_OUTING
    departure_time: datetime
    expected_return_time: datetime
    destination: str | None = None
    reason: str = Field(..., min_length=3)
    parent_consent_verified: bool = False
    parent_contact_phone: str | None = None


class OutingApprovalRequest(BaseModel):
    status: OutingStatus  # APPROVED or REJECTED


class OutingDepartureRequest(BaseModel):
    actual_departure_time: datetime | None = None


class OutingReturnRequest(BaseModel):
    actual_return_time: datetime | None = None


class OutingResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    hostel_id: UUID | None = None
    outing_type: str
    pass_code: str | None = None
    departure_time: datetime
    expected_return_time: datetime
    actual_departure_time: datetime | None = None
    actual_return_time: datetime | None = None
    destination: str | None = None
    reason: str
    parent_consent_verified: bool
    parent_contact_phone: str | None = None
    approved_by_user_id: UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NightAttendanceRecord(BaseModel):
    resident_id: UUID
    status: NightAttendanceStatus = NightAttendanceStatus.PRESENT
    remarks: str | None = None


class NightAttendanceBatchRequest(BaseModel):
    hostel_id: UUID
    attendance_date: date
    records: list[NightAttendanceRecord]


class NightAttendanceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    hostel_id: UUID
    resident_id: UUID
    attendance_date: date
    status: str
    checked_by_user_id: UUID | None = None
    remarks: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 8. VISITOR & GATE-PASS SCHEMAS
# =============================================================================


class VisitorRegisterRequest(BaseModel):
    hostel_id: UUID
    host_student_id: UUID
    visitor_name: str = Field(..., max_length=128)
    visitor_phone: str = Field(..., max_length=32)
    visitor_id_proof_type: str = "GOVT_ID"
    visitor_id_proof_number: str = Field(..., max_length=64)
    visitor_relation: str = "PARENT"
    purpose: str = Field(..., max_length=255)
    expected_check_in: datetime
    expected_check_out: datetime
    remarks: str | None = None


class VisitorCheckInRequest(BaseModel):
    actual_check_in: datetime | None = None


class VisitorCheckOutRequest(BaseModel):
    actual_check_out: datetime | None = None


class VisitorResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    hostel_id: UUID
    host_student_id: UUID
    visitor_name: str
    visitor_phone: str
    visitor_id_proof_type: str
    visitor_id_proof_number: str
    visitor_relation: str
    purpose: str
    pass_code: str
    expected_check_in: datetime
    expected_check_out: datetime
    actual_check_in: datetime | None = None
    actual_check_out: datetime | None = None
    approved_by_user_id: UUID | None = None
    status: str
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GatePassCreateRequest(BaseModel):
    resident_id: UUID
    purpose: str = Field(..., max_length=255)
    destination: str | None = None
    valid_from: datetime
    valid_until: datetime


class GatePassVerifyRequest(BaseModel):
    pass_code: str
    action: str = "EXIT"  # "EXIT" or "ENTRY"


class GatePassResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    resident_id: UUID
    student_id: UUID
    hostel_id: UUID
    pass_code: str
    purpose: str
    destination: str | None = None
    valid_from: datetime
    valid_until: datetime
    status: str
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    actual_exit_time: datetime | None = None
    actual_entry_time: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 9. SERVICE REQUESTS & COMPLAINTS SCHEMAS
# =============================================================================


class ServiceRequestCreate(BaseModel):
    student_id: UUID
    hostel_id: UUID | None = None
    room_id: UUID
    category: ResidentialServiceCategory = ResidentialServiceCategory.ELECTRICAL
    priority: ResidentialServicePriority = ResidentialServicePriority.MEDIUM
    title: str | None = None
    description: str = Field(..., min_length=5)


class ServiceRequestUpdate(BaseModel):
    status: ResidentialServiceStatus | None = None
    assigned_to_user_id: UUID | None = None
    work_order_id: UUID | None = None
    sla_deadline: datetime | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None


class ServiceRequestFeedback(BaseModel):
    student_rating: int = Field(..., ge=1, le=5)
    student_feedback: str | None = None


class ServiceRequestResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    ticket_number: str | None = None
    student_id: UUID
    hostel_id: UUID | None = None
    room_id: UUID
    category: str
    priority: str
    title: str | None = None
    description: str
    status: str
    assigned_to_user_id: UUID | None = None
    work_order_id: UUID | None = None
    sla_deadline: datetime | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    student_rating: int | None = None
    student_feedback: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 10. SAFETY & INCIDENT SCHEMAS
# =============================================================================


class IncidentCreate(BaseModel):
    hostel_id: UUID
    incident_type: ResidentialIncidentType = ResidentialIncidentType.OTHER
    severity: ResidentialIncidentSeverity = ResidentialIncidentSeverity.MEDIUM
    incident_time: datetime
    location_description: str = Field(..., max_length=255)
    reporter_user_id: UUID
    involved_student_ids: list[str] | None = None
    description: str = Field(..., min_length=10)
    action_taken: str | None = None
    is_disciplinary_referral: bool = False
    assigned_warden_user_id: UUID | None = None


class IncidentUpdate(BaseModel):
    severity: ResidentialIncidentSeverity | None = None
    status: ResidentialIncidentStatus | None = None
    action_taken: str | None = None
    is_disciplinary_referral: bool | None = None
    assigned_warden_user_id: UUID | None = None
    resolved_at: datetime | None = None


class IncidentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    incident_number: str
    hostel_id: UUID
    incident_type: str
    severity: str
    incident_time: datetime
    location_description: str
    reporter_user_id: UUID
    involved_student_ids: list[str] | None = None
    description: str
    action_taken: str | None = None
    is_disciplinary_referral: bool
    status: str
    assigned_warden_user_id: UUID | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SafetyInspectionCreate(BaseModel):
    hostel_id: UUID
    inspection_date: date
    inspector_user_id: UUID
    fire_safety_passed: bool = True
    electrical_safety_passed: bool = True
    hygiene_passed: bool = True
    structural_passed: bool = True
    checklist_results: dict[str, Any] | None = None
    critical_findings: str | None = None
    action_items: list[dict[str, Any]] | None = None
    status: SafetyInspectionStatus = SafetyInspectionStatus.COMPLETED


class SafetyInspectionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    hostel_id: UUID
    inspection_date: date
    inspector_user_id: UUID
    fire_safety_passed: bool
    electrical_safety_passed: bool
    hygiene_passed: bool
    structural_passed: bool
    checklist_results: dict[str, Any] | None = None
    critical_findings: str | None = None
    action_items: list[dict[str, Any]] | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 11. DASHBOARD & REPORT SCHEMAS
# =============================================================================


class HostelOccupancyStat(BaseModel):
    hostel_id: UUID
    hostel_name: str
    hostel_code: str
    total_beds: int
    occupied_beds: int
    reserved_beds: int
    available_beds: int
    blocked_beds: int
    occupancy_percentage: float


class OccupancyDashboardResponse(BaseModel):
    overall_total_beds: int
    overall_occupied_beds: int
    overall_reserved_beds: int
    overall_available_beds: int
    overall_blocked_beds: int
    overall_occupancy_percentage: float
    hostel_stats: list[HostelOccupancyStat]


class ResidentialDashboardSummaryResponse(BaseModel):
    total_hostels: int
    total_rooms: int
    total_beds: int
    occupied_beds: int
    available_beds: int
    occupancy_percentage: float
    pending_applications: int
    active_residents: int
    active_outings: int
    overdue_outings: int
    open_service_requests: int
    active_visitors: int


# Backward-compatible and convenience aliases
BedStatusUpdateRequest = HostelBedUpdate
HostelApplicationCycleCreate = ApplicationCycleCreate
HostelApplicationCycleResponse = ApplicationCycleResponse
HostelApplicationCreate = AccommodationApplicationCreate
HostelApplicationReviewRequest = AccommodationApplicationReview
HostelApplicationResponse = AccommodationApplicationResponse
HostelAllocationCreate = AllocationCreate
HostelAllocationTransferRequest = AllocationTransferRequest
HostelAllocationResponse = AllocationResponse
HostelCheckInRequest = ResidentCheckInRequest
HostelCheckOutRequest = ResidentCheckOutRequest
HostelResidentResponse = ResidentResponse
HostelFeePlanInvoiceGenerateRequest = GenerateHostelInvoiceRequest
HostelMealPlanCreate = MealPlanCreate
HostelMealPlanResponse = MealPlanResponse
HostelMealEnrollmentCreate = MealEnrollmentCreate
HostelMealEnrollmentResponse = MealEnrollmentResponse
HostelMealHeadcountResponse = MealHeadcountResponse
HostelLeavePassCreate = OutingRequestCreate
HostelLeavePassResponse = OutingResponse
HostelVisitorCreate = VisitorRegisterRequest
HostelVisitorCheckOutRequest = VisitorCheckOutRequest
HostelVisitorResponse = VisitorResponse
HostelGatePassCreate = GatePassCreateRequest
HostelGatePassVerifyRequest = GatePassVerifyRequest
HostelGatePassResponse = GatePassResponse
HostelComplaintCreate = ServiceRequestCreate
HostelComplaintUpdate = ServiceRequestUpdate
HostelComplaintResponse = ServiceRequestResponse
HostelIncidentCreate = IncidentCreate
HostelIncidentResponse = IncidentResponse
HostelSafetyInspectionCreate = SafetyInspectionCreate
HostelSafetyInspectionResponse = SafetyInspectionResponse
HostelOccupancyReportResponse = OccupancyDashboardResponse
HostelRoomDetailResponse = HostelRoomResponse
HostelDetailResponse = HostelResponse


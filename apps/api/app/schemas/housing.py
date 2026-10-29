"""Pydantic validation schemas for Student Housing, Off-Campus Accommodation & Landlord Partnerships (Step 66)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.housing import (
    AgreementStatus,
    HousingAssignmentStatus,
    HousingOfferStatus,
    HousingRequestStatus,
    InspectionOutcome,
    InspectionType,
    MaintenanceCategory,
    MaintenancePriority,
    MaintenanceStatus,
    PropertyLifecycleStatus,
    PropertyType,
    ProviderType,
    ProviderVerificationStatus,
    UnitStatus,
    UnitType,
)

# =============================================================================
# 1. ACCOMMODATION PROVIDERS & LANDLORDS
# =============================================================================

class AccommodationProviderBase(BaseModel):
    name: str = Field(..., max_length=128)
    slug: str = Field(..., max_length=128)
    provider_type: ProviderType = ProviderType.PRIVATE_LANDLORD
    registration_number: str | None = None
    contact_name: str = Field(..., max_length=128)
    contact_email: str = Field(..., max_length=128)
    contact_phone: str = Field(..., max_length=32)
    emergency_phone: str | None = None
    tax_id: str | None = None
    address: str | None = None
    city: str = "Chennai"
    state: str = "Tamil Nadu"
    mou_reference: str | None = None
    mou_valid_from: date | None = None
    mou_valid_to: date | None = None
    is_active: bool = True


class AccommodationProviderCreate(AccommodationProviderBase):
    pass


class AccommodationProviderUpdate(BaseModel):
    name: str | None = None
    provider_type: ProviderType | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    emergency_phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    verification_status: ProviderVerificationStatus | None = None
    verification_notes: str | None = None
    mou_reference: str | None = None
    mou_valid_from: date | None = None
    mou_valid_to: date | None = None
    rating: Decimal | None = None
    is_active: bool | None = None


class AccommodationProviderResponse(AccommodationProviderBase):
    id: UUID
    tenant_id: UUID
    verification_status: ProviderVerificationStatus
    verification_notes: str | None = None
    verified_at: datetime | None = None
    verified_by_id: UUID | None = None
    rating: Decimal
    total_properties_managed: int
    total_beds_provided: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. ACCOMMODATION PROPERTIES
# =============================================================================

class AccommodationPropertyBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    slug: str = Field(..., max_length=128)
    provider_id: UUID | None = None
    hostel_id: UUID | None = None
    campus_id: UUID | None = None
    property_type: PropertyType = PropertyType.OFF_CAMPUS_HOSTEL
    description: str | None = None
    address: str = Field(..., max_length=255)
    city: str = "Chennai"
    state: str = "Tamil Nadu"
    postal_code: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    distance_to_campus_km: Decimal = Decimal("1.50")
    monthly_rent_min: Decimal = Decimal("6000.00")
    monthly_rent_max: Decimal = Decimal("12000.00")
    security_deposit_amount: Decimal = Decimal("15000.00")
    currency: str = "INR"
    amenities: list[str] = Field(default_factory=list)
    utilities_included: list[str] = Field(default_factory=list)
    accessibility_features: list[str] = Field(default_factory=list)
    safety_features: list[str] = Field(default_factory=list)
    house_rules: str | None = None
    manager_name: str | None = None
    manager_phone: str | None = None
    manager_email: str | None = None


class AccommodationPropertyCreate(AccommodationPropertyBase):
    pass


class AccommodationPropertyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    distance_to_campus_km: Decimal | None = None
    monthly_rent_min: Decimal | None = None
    monthly_rent_max: Decimal | None = None
    security_deposit_amount: Decimal | None = None
    amenities: list[str] | None = None
    utilities_included: list[str] | None = None
    accessibility_features: list[str] | None = None
    safety_features: list[str] | None = None
    house_rules: str | None = None
    manager_name: str | None = None
    manager_phone: str | None = None
    manager_email: str | None = None


class PropertyStatusTransitionRequest(BaseModel):
    target_status: PropertyLifecycleStatus
    approval_valid_until: date | None = None
    notes: str | None = None


class AccommodationPropertyResponse(AccommodationPropertyBase):
    id: UUID
    tenant_id: UUID
    lifecycle_status: PropertyLifecycleStatus
    total_rooms: int
    total_bed_capacity: int
    occupied_beds: int
    available_beds: int
    approval_valid_until: date | None = None
    approved_by_id: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. UNITS & BEDS
# =============================================================================

class AccommodationUnitBase(BaseModel):
    property_id: UUID
    hostel_room_id: UUID | None = None
    unit_number: str = Field(..., max_length=32)
    unit_type: UnitType = UnitType.DOUBLE_OCCUPANCY
    floor_number: int = 1
    bed_capacity: int = 2
    rent_per_bed: Decimal = Decimal("8000.00")
    security_deposit_per_bed: Decimal = Decimal("15000.00")
    is_furnished: bool = True
    has_attached_bath: bool = True
    is_accessible: bool = False


class AccommodationUnitCreate(AccommodationUnitBase):
    pass


class AccommodationBedBase(BaseModel):
    unit_id: UUID
    hostel_bed_id: UUID | None = None
    bed_code: str = Field(..., max_length=32)


class AccommodationBedCreate(AccommodationBedBase):
    pass


class AccommodationBedResponse(AccommodationBedBase):
    id: UUID
    tenant_id: UUID
    is_available: bool
    status: str
    blocked_reason: str | None = None
    blocked_until: date | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccommodationUnitResponse(AccommodationUnitBase):
    id: UUID
    tenant_id: UUID
    occupied_beds: int
    is_available: bool
    status: UnitStatus
    maintenance_reason: str | None = None
    closed_until: date | None = None
    created_at: datetime
    updated_at: datetime
    beds: list[AccommodationBedResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. HOUSING REQUESTS & OFFERS
# =============================================================================

class StudentHousingRequestCreate(BaseModel):
    preferred_property_id: UUID | None = None
    preferred_unit_type: UnitType = UnitType.DOUBLE_OCCUPANCY
    academic_year_id: UUID | None = None
    academic_term: str = "Academic Year 2026-27"
    requested_move_in_date: date
    requested_move_out_date: date
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    accessibility_required: bool = False
    disability_accommodation_notes: str | None = None
    dietary_preference: str | None = None
    lifestyle_preferences: dict[str, Any] = Field(default_factory=dict)
    special_requests: str | None = None
    supporting_document_ids: list[str] = Field(default_factory=list)


class StudentHousingRequestReview(BaseModel):
    status: HousingRequestStatus
    review_notes: str | None = None
    rejection_reason: str | None = None
    priority_score: Decimal | None = None


class StudentHousingRequestResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    request_number: str
    student_id: UUID
    preferred_property_id: UUID | None = None
    preferred_unit_type: UnitType
    academic_year_id: UUID | None = None
    academic_term: str
    requested_move_in_date: date
    requested_move_out_date: date
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    accessibility_required: bool
    disability_accommodation_notes: str | None = None
    dietary_preference: str | None = None
    lifestyle_preferences: dict[str, Any]
    special_requests: str | None = None
    supporting_document_ids: list[str]
    status: HousingRequestStatus
    waitlist_position: int | None = None
    priority_score: Decimal
    review_notes: str | None = None
    reviewed_by_id: UUID | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    # Display enrichments
    student_name: str | None = None
    student_roll_number: str | None = None
    property_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class HousingOfferCreate(BaseModel):
    request_id: UUID
    property_id: UUID
    unit_id: UUID
    bed_id: UUID
    offered_rent_monthly: Decimal
    offered_deposit: Decimal
    occupancy_start_date: date
    occupancy_end_date: date
    offer_valid_days: int = 5


class HousingOfferRespond(BaseModel):
    decision: HousingOfferStatus  # ACCEPTED or DECLINED
    decline_reason: str | None = None
    response_notes: str | None = None


class HousingOfferResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    request_id: UUID
    student_id: UUID
    property_id: UUID
    unit_id: UUID
    bed_id: UUID
    offered_rent_monthly: Decimal
    offered_deposit: Decimal
    occupancy_start_date: date
    occupancy_end_date: date
    offer_valid_until: datetime
    status: HousingOfferStatus
    decline_reason: str | None = None
    response_notes: str | None = None
    responded_at: datetime | None = None
    created_at: datetime

    # Display enrichments
    student_name: str | None = None
    property_name: str | None = None
    unit_number: str | None = None
    bed_code: str | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. ASSIGNMENTS, AGREEMENTS & CHECK-IN/OUT
# =============================================================================

class HousingAssignmentCreate(BaseModel):
    student_id: UUID
    property_id: UUID
    unit_id: UUID
    bed_id: UUID
    request_id: UUID | None = None
    offer_id: UUID | None = None
    start_date: date
    end_date: date
    monthly_rent: Decimal
    security_deposit: Decimal


class HousingAssignmentTransferRequest(BaseModel):
    target_unit_id: UUID
    target_bed_id: UUID
    transfer_reason: str


class HousingAssignmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    assignment_number: str
    student_id: UUID
    property_id: UUID
    unit_id: UUID
    bed_id: UUID
    request_id: UUID | None = None
    offer_id: UUID | None = None
    start_date: date
    end_date: date
    monthly_rent: Decimal
    security_deposit: Decimal
    status: HousingAssignmentStatus
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    transfer_to_unit_id: UUID | None = None
    transfer_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    # Display enrichments
    student_name: str | None = None
    student_roll_number: str | None = None
    property_name: str | None = None
    unit_number: str | None = None
    bed_code: str | None = None

    model_config = ConfigDict(from_attributes=True)


class HousingAgreementCreate(BaseModel):
    assignment_id: UUID
    agreement_title: str
    valid_from: date
    valid_to: date
    rent_amount: Decimal
    deposit_amount: Decimal
    payment_frequency: str = "MONTHLY"
    finance_invoice_reference: str | None = None
    deposit_invoice_reference: str | None = None


class HousingAgreementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    assignment_id: UUID
    property_id: UUID
    provider_id: UUID | None = None
    student_id: UUID
    agreement_number: str
    agreement_title: str
    valid_from: date
    valid_to: date
    rent_amount: Decimal
    deposit_amount: Decimal
    payment_frequency: str
    finance_invoice_reference: str | None = None
    deposit_invoice_reference: str | None = None
    deposit_refund_status: str
    terms_and_conditions_acknowledged: bool
    student_signed_at: datetime | None = None
    provider_signed_at: datetime | None = None
    institutional_witness_id: UUID | None = None
    status: AgreementStatus
    document_file_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HousingCheckInOutCreate(BaseModel):
    assignment_id: UUID
    record_type: str  # "CHECK_IN" or "CHECK_OUT"
    scheduled_date: date
    key_card_issued_or_returned: bool = True
    key_identifier: str | None = None
    room_condition_rating: str = "GOOD"
    checklist_items: dict[str, Any] = Field(default_factory=dict)
    damage_assessed_amount: Decimal = Decimal("0.00")
    damage_description: str | None = None
    photos_evidence_ids: list[str] = Field(default_factory=list)
    student_signature_confirmed: bool = True
    notes: str | None = None


class HousingCheckInOutResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    assignment_id: UUID
    student_id: UUID
    record_type: str
    scheduled_date: date
    actual_timestamp: datetime | None = None
    inspector_user_id: UUID | None = None
    key_card_issued_or_returned: bool
    key_identifier: str | None = None
    room_condition_rating: str
    checklist_items: dict[str, Any]
    damage_assessed_amount: Decimal
    damage_description: str | None = None
    photos_evidence_ids: list[str]
    student_signature_confirmed: bool
    notes: str | None = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 6. PROPERTY INSPECTIONS & MAINTENANCE
# =============================================================================

class HousingPropertyInspectionCreate(BaseModel):
    property_id: UUID
    inspection_date: date
    inspection_type: InspectionType = InspectionType.SAFETY_FIRE
    overall_outcome: InspectionOutcome = InspectionOutcome.PASSED
    safety_score: Decimal = Decimal("100.00")
    checklist_results: dict[str, Any] = Field(default_factory=dict)
    critical_issues_found: bool = False
    availability_suspended: bool = False
    corrective_actions_required: str | None = None
    corrective_action_deadline: date | None = None
    reinspection_due_date: date | None = None


class HousingPropertyInspectionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    property_id: UUID
    inspection_code: str
    inspector_user_id: UUID
    inspection_date: date
    inspection_type: InspectionType
    overall_outcome: InspectionOutcome
    safety_score: Decimal
    checklist_results: dict[str, Any]
    critical_issues_found: bool
    availability_suspended: bool
    corrective_actions_required: str | None = None
    corrective_action_deadline: date | None = None
    reinspection_due_date: date | None = None
    compliance_status: str
    created_at: datetime

    # Display enrichments
    property_name: str | None = None
    inspector_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class HousingMaintenanceRequestCreate(BaseModel):
    property_id: UUID
    unit_id: UUID | None = None
    category: MaintenanceCategory = MaintenanceCategory.PLUMBING
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    title: str = Field(..., max_length=128)
    description: str
    photo_urls: list[str] = Field(default_factory=list)


class HousingMaintenanceRequestUpdate(BaseModel):
    status: MaintenanceStatus
    assigned_technician_name: str | None = None
    assigned_vendor_name: str | None = None
    scheduled_visit_date: date | None = None
    completion_notes: str | None = None
    tenant_satisfaction_rating: int | None = None
    tenant_feedback: str | None = None
    cost_charged_to: str | None = None


class HousingMaintenanceRequestResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    property_id: UUID
    unit_id: UUID | None = None
    reported_by_user_id: UUID
    reported_by_student_id: UUID | None = None
    category: MaintenanceCategory
    priority: MaintenancePriority
    title: str
    description: str
    photo_urls: list[str]
    status: MaintenanceStatus
    assigned_technician_name: str | None = None
    assigned_vendor_name: str | None = None
    linked_work_order_id: UUID | None = None
    scheduled_visit_date: date | None = None
    completed_at: datetime | None = None
    completion_notes: str | None = None
    tenant_satisfaction_rating: int | None = None
    tenant_feedback: str | None = None
    cost_charged_to: str
    created_at: datetime
    updated_at: datetime

    # Display enrichments
    property_name: str | None = None
    unit_number: str | None = None
    reporter_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 7. HOUSING ANALYTICS SUMMARY
# =============================================================================

class HousingAnalyticsSummaryResponse(BaseModel):
    total_approved_properties: int
    total_capacity_beds: int
    occupied_beds: int
    available_beds: int
    occupancy_rate_percentage: float
    pending_housing_requests: int
    waitlisted_students: int
    active_assignments: int
    upcoming_checkins_next_7_days: int
    upcoming_checkouts_next_7_days: int
    expiring_agreements_next_30_days: int
    properties_requiring_inspection: int
    overdue_safety_actions: int
    open_maintenance_requests: int
    average_maintenance_resolution_days: float
    properties_by_type: dict[str, int]
    monthly_occupancy_trend: list[dict[str, Any]]


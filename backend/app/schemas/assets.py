"""CampusOS Enterprise Asset Lifecycle, Maintenance, Facilities & Equipment Management Schemas (Step 53).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Pydantic v2 schemas for:
- Asset Category & Policy Configuration
- Institutional Asset Registry & Bulk Upload
- Validated Lifecycle State Machine Transitions
- Custody Assignment, Receipt Acknowledgement & Loan Management
- Inter-Campus & Departmental Asset Transfers
- Preventive Maintenance Plans & Recurrence
- Maintenance Work Orders, Labor, Downtime & Verification
- Spare Parts Inventory Reservation & Consumption Integration
- Periodic Safety Inspections, Findings & Operational Restrictions
- Warranties, Service Contracts (AMC/CMC) & Vendor Claims
- Depreciation Schedules & Financial Integration
- Physical Audits, Barcode/QR Scanning & Discrepancy Reconciliation
- Controlled Retirement, IT Data Wiping & Certified Disposal
- Executive Asset Analytics & Operational Reports
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.assets import (
    AssetCategoryType,
    AssetCondition,
    AssetCriticality,
    AssetLifecycleState,
    AssetOperationalStatus,
    AssetSource,
    AssetUsageClassification,
    AssignmentType,
    ContractStatus,
    ContractType,
    DepreciationMethod,
    DisposalMethod,
    InspectionActionTaken,
    InspectionOutcome,
    MaintenanceOperationalImpact,
    MaintenanceOrderType,
    MaintenancePriority,
    MaintenanceSeverity,
    RetirementReason,
    WarrantyClaimStatus,
)

# =============================================================================
# 1. ASSET CATEGORY & POLICY SCHEMAS
# =============================================================================


class AssetCategoryBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    description: str | None = None
    category_type: str = AssetCategoryType.OTHER
    is_active: bool = True
    requires_serial_number: bool = False
    requires_custodian_acknowledgement: bool = False
    default_inspection_interval_days: int | None = 90
    default_maintenance_interval_days: int | None = 30
    default_criticality: str = AssetCriticality.MEDIUM
    default_depreciation_method: str = DepreciationMethod.STRAIGHT_LINE
    default_useful_life_months: int = 60
    default_salvage_value_percent: Decimal = Decimal("5.00")
    policy_schema: dict[str, Any] = Field(default_factory=dict)
    assignment_restrictions: dict[str, Any] = Field(default_factory=dict)


class AssetCategoryCreate(AssetCategoryBase):
    pass


class AssetCategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category_type: str | None = None
    is_active: bool | None = None
    requires_serial_number: bool | None = None
    requires_custodian_acknowledgement: bool | None = None
    default_inspection_interval_days: int | None = None
    default_maintenance_interval_days: int | None = None
    default_criticality: str | None = None
    default_depreciation_method: str | None = None
    default_useful_life_months: int | None = None
    default_salvage_value_percent: Decimal | None = None
    policy_schema: dict[str, Any] | None = None
    assignment_restrictions: dict[str, Any] | None = None


class AssetCategoryResponse(AssetCategoryBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. INSTITUTIONAL ASSET REGISTRY SCHEMAS
# =============================================================================


class AssetBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    category_id: UUID
    asset_type: str = "GENERAL"
    make: str | None = None
    model: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    barcode_data: str | None = None

    acquisition_date: date
    acquisition_cost: Decimal = Decimal("0.00")
    currency: str = "INR"
    source: str = AssetSource.PURCHASE
    supplier_vendor_id: UUID | None = None
    purchase_order_id: UUID | None = None
    purchase_order_line_id: UUID | None = None
    goods_receipt_id: UUID | None = None
    invoice_reference: str | None = None

    campus_id: UUID | None = None
    building: str | None = None
    floor: str | None = None
    room_number: str | None = None
    location_description: str | None = None
    department_id: UUID | None = None
    current_custodian_id: UUID | None = None

    condition: str = AssetCondition.GOOD
    operational_status: str = AssetOperationalStatus.OPERATIONAL
    criticality: str = AssetCriticality.MEDIUM
    usage_classification: str = AssetUsageClassification.ACADEMIC
    lifecycle_state: str = AssetLifecycleState.REQUESTED
    is_restricted: bool = False
    restriction_reason: str | None = None

    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    depreciation_method: str = DepreciationMethod.STRAIGHT_LINE
    useful_life_months: int = 60
    salvage_value: Decimal = Decimal("0.00")

    image_keys: list[str] = Field(default_factory=list)
    document_references: list[dict[str, Any]] = Field(default_factory=list)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class AssetCreate(AssetBase):
    asset_tag: str | None = None  # Auto-generated if not supplied


class AssetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category_id: UUID | None = None
    asset_type: str | None = None
    make: str | None = None
    model: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    barcode_data: str | None = None

    campus_id: UUID | None = None
    building: str | None = None
    floor: str | None = None
    room_number: str | None = None
    location_description: str | None = None
    department_id: UUID | None = None
    current_custodian_id: UUID | None = None

    condition: str | None = None
    operational_status: str | None = None
    criticality: str | None = None
    usage_classification: str | None = None
    is_restricted: bool | None = None
    restriction_reason: str | None = None

    warranty_start_date: date | None = None
    warranty_end_date: date | None = None
    depreciation_method: str | None = None
    useful_life_months: int | None = None
    salvage_value: Decimal | None = None

    image_keys: list[str] | None = None
    document_references: list[dict[str, Any]] | None = None
    custom_attributes: dict[str, Any] | None = None


class AssetResponse(AssetBase):
    id: UUID
    tenant_id: UUID
    asset_tag: str
    accumulated_depreciation: Decimal
    current_book_value: Decimal
    last_depreciated_date: date | None = None
    last_maintained_at: datetime | None = None
    next_maintenance_due: date | None = None
    last_inspected_at: datetime | None = None
    next_inspection_due: date | None = None
    created_at: datetime
    updated_at: datetime

    category: AssetCategoryResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class AssetBulkCreateRequest(BaseModel):
    assets: list[AssetCreate] = Field(..., min_length=1, max_length=100)


class AssetBulkCreateResponse(BaseModel):
    created_count: int
    skipped_count: int
    errors: list[str] = Field(default_factory=list)
    created_assets: list[AssetResponse] = Field(default_factory=list)


# =============================================================================
# 3. ASSET LIFECYCLE SCHEMAS
# =============================================================================


class AssetLifecycleTransitionRequest(BaseModel):
    to_state: str = Field(..., max_length=32)
    reason: str = Field(..., min_length=3)
    supporting_documents: list[dict[str, Any]] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class AssetLifecycleEventResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    asset_id: UUID
    from_state: str
    to_state: str
    reason: str
    supporting_documents: list[dict[str, Any]]
    actor_id: UUID
    performed_at: datetime
    metadata_json: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. ASSET ASSIGNMENT & CUSTODY SCHEMAS
# =============================================================================


class AssetAssignmentCreate(BaseModel):
    assignment_type: str = AssignmentType.EMPLOYEE
    custodian_id: UUID | None = None
    department_id: UUID | None = None
    campus_id: UUID | None = None
    location_details: str | None = None
    effective_date: date = Field(default_factory=date.today)
    expected_return_date: date | None = None
    acknowledgement_required: bool = False
    condition_at_assignment: str = AssetCondition.GOOD
    handover_notes: str | None = None
    supporting_evidence: list[dict[str, Any]] = Field(default_factory=list)


class AssetAssignmentAcknowledgeRequest(BaseModel):
    acknowledgement_notes: str | None = None


class AssetAssignmentReturnRequest(BaseModel):
    actual_return_date: date = Field(default_factory=date.today)
    condition_at_return: str = AssetCondition.GOOD
    handover_notes: str | None = None
    supporting_evidence: list[dict[str, Any]] = Field(default_factory=list)


class AssetAssignmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    asset_id: UUID
    assignment_type: str
    custodian_id: UUID | None = None
    department_id: UUID | None = None
    campus_id: UUID | None = None
    location_details: str | None = None
    effective_date: date
    expected_return_date: date | None = None
    actual_return_date: date | None = None
    status: str
    acknowledgement_required: bool
    acknowledged_at: datetime | None = None
    acknowledgement_notes: str | None = None
    assigned_by_id: UUID
    condition_at_assignment: str
    condition_at_return: str | None = None
    handover_notes: str | None = None
    supporting_evidence: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. ASSET TRANSFER SCHEMAS
# =============================================================================


class AssetTransferCreate(BaseModel):
    to_campus_id: UUID | None = None
    to_department_id: UUID | None = None
    to_custodian_id: UUID | None = None
    transfer_reason: str = Field(..., min_length=5)
    dispatch_notes: str | None = None


class AssetTransferActionRequest(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|DISPATCH|RECEIVE|REJECT|CANCEL)$")
    notes: str | None = None


class AssetTransferResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    transfer_number: str
    asset_id: UUID
    from_campus_id: UUID | None = None
    from_department_id: UUID | None = None
    from_custodian_id: UUID | None = None
    to_campus_id: UUID | None = None
    to_department_id: UUID | None = None
    to_custodian_id: UUID | None = None
    transfer_reason: str
    status: str
    initiated_by_id: UUID
    approved_by_id: UUID | None = None
    approved_at: datetime | None = None
    in_transit_at: datetime | None = None
    completed_at: datetime | None = None
    received_by_id: UUID | None = None
    dispatch_notes: str | None = None
    acceptance_notes: str | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 6. MAINTENANCE PLAN & WORK ORDER SCHEMAS
# =============================================================================


class MaintenancePlanCreate(BaseModel):
    plan_code: str | None = None
    title: str = Field(..., max_length=255)
    description: str | None = None
    category_id: UUID | None = None
    asset_id: UUID | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    interval_days: int = 30
    estimated_duration_hours: Decimal = Decimal("2.00")
    checklist: list[dict[str, Any]] = Field(default_factory=list)
    assigned_technician_id: UUID | None = None
    preferred_vendor_id: UUID | None = None
    is_active: bool = True


class MaintenancePlanUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    interval_days: int | None = None
    estimated_duration_hours: Decimal | None = None
    checklist: list[dict[str, Any]] | None = None
    assigned_technician_id: UUID | None = None
    preferred_vendor_id: UUID | None = None
    is_active: bool | None = None


class MaintenancePlanResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    plan_code: str
    title: str
    description: str | None = None
    category_id: UUID | None = None
    asset_id: UUID | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    interval_days: int
    estimated_duration_hours: Decimal
    checklist: list[dict[str, Any]]
    assigned_technician_id: UUID | None = None
    preferred_vendor_id: UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaintenanceWorkOrderCreate(BaseModel):
    asset_id: UUID
    plan_id: UUID | None = None
    order_type: str = MaintenanceOrderType.CORRECTIVE
    priority: str = MaintenancePriority.MEDIUM
    severity: str = MaintenanceSeverity.MODERATE
    operational_impact: str = MaintenanceOperationalImpact.NO_IMPACT
    reported_symptoms: str = Field(..., min_length=5)
    scheduled_start_date: date | None = None
    scheduled_end_date: date | None = None
    assigned_technician_id: UUID | None = None
    vendor_id: UUID | None = None
    estimated_cost: Decimal = Decimal("0.00")
    verification_required: bool = False


class MaintenanceWorkOrderUpdate(BaseModel):
    priority: str | None = None
    severity: str | None = None
    operational_impact: str | None = None
    status: str | None = None
    scheduled_start_date: date | None = None
    scheduled_end_date: date | None = None
    assigned_technician_id: UUID | None = None
    vendor_id: UUID | None = None
    diagnosis: str | None = None
    repair_actions: str | None = None
    downtime_hours: Decimal | None = None
    labor_hours: Decimal | None = None
    labor_cost: Decimal | None = None
    service_charges: Decimal | None = None
    verification_required: bool | None = None
    checklist_results: list[dict[str, Any]] | None = None


class MaintenanceWorkOrderCloseRequest(BaseModel):
    diagnosis: str = Field(..., min_length=3)
    repair_actions: str = Field(..., min_length=3)
    downtime_hours: Decimal = Decimal("0.00")
    labor_hours: Decimal = Decimal("0.00")
    labor_cost: Decimal = Decimal("0.00")
    service_charges: Decimal = Decimal("0.00")
    checklist_results: list[dict[str, Any]] = Field(default_factory=list)
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class MaintenanceWorkOrderVerifyRequest(BaseModel):
    verification_notes: str | None = None


class MaintenanceWorkOrderReopenRequest(BaseModel):
    reopen_reason: str = Field(..., min_length=5)


class WorkOrderPartConsumptionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    work_order_id: UUID
    inventory_item_id: UUID
    inventory_location_id: UUID
    quantity_reserved: Decimal
    quantity_consumed: Decimal
    quantity_returned: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    status: str
    stock_movement_id: UUID | None = None
    consumed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaintenanceWorkOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    work_order_number: str
    asset_id: UUID
    plan_id: UUID | None = None
    order_type: str
    priority: str
    severity: str
    operational_impact: str
    status: str
    reported_by_id: UUID
    reported_symptoms: str
    scheduled_start_date: date | None = None
    scheduled_end_date: date | None = None
    actual_start_at: datetime | None = None
    completed_at: datetime | None = None
    closed_at: datetime | None = None
    assigned_technician_id: UUID | None = None
    vendor_id: UUID | None = None
    diagnosis: str | None = None
    repair_actions: str | None = None
    downtime_hours: Decimal
    labor_hours: Decimal
    labor_cost: Decimal
    parts_cost: Decimal
    service_charges: Decimal
    total_cost: Decimal
    estimated_cost: Decimal
    verification_required: bool
    verified_by_id: UUID | None = None
    verified_at: datetime | None = None
    verification_notes: str | None = None
    attachments: list[dict[str, Any]]
    checklist_results: list[dict[str, Any]]
    reopen_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    parts_consumed: list[WorkOrderPartConsumptionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 7. PART RESERVATION & CONSUMPTION SCHEMAS
# =============================================================================


class PartReservationRequest(BaseModel):
    inventory_item_id: UUID
    inventory_location_id: UUID
    quantity: Decimal = Field(..., gt=0)


class PartConsumptionRequest(BaseModel):
    part_consumption_id: UUID
    quantity_to_consume: Decimal = Field(..., gt=0)


class PartReturnRequest(BaseModel):
    part_consumption_id: UUID
    quantity_to_return: Decimal = Field(..., gt=0)


# =============================================================================
# 8. INSPECTION SCHEMAS
# =============================================================================


class InspectionTemplateCreate(BaseModel):
    code: str = Field(..., max_length=64)
    title: str = Field(..., max_length=255)
    description: str | None = None
    category_id: UUID | None = None
    frequency_days: int = 90
    checklist_items: list[dict[str, Any]] = Field(default_factory=list)
    is_mandatory: bool = True
    is_active: bool = True


class InspectionTemplateUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    frequency_days: int | None = None
    checklist_items: list[dict[str, Any]] | None = None
    is_mandatory: bool | None = None
    is_active: bool | None = None


class InspectionTemplateResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    title: str
    description: str | None = None
    category_id: UUID | None = None
    frequency_days: int
    checklist_items: list[dict[str, Any]]
    is_mandatory: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InspectionRecordCreate(BaseModel):
    asset_id: UUID
    template_id: UUID | None = None
    inspection_date: date = Field(default_factory=date.today)
    overall_outcome: str = InspectionOutcome.PASS
    safety_risk_detected: bool = False
    action_taken: str = InspectionActionTaken.NONE
    checklist_results: list[dict[str, Any]] = Field(default_factory=list)
    findings_summary: str | None = None
    corrective_action_required: bool = False
    corrective_action_due_date: date | None = None
    corrective_action_owner_id: UUID | None = None
    corrective_action_status: str = "RESOLVED"
    evidence_attachments: list[dict[str, Any]] = Field(default_factory=list)


class InspectionRecordResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    inspection_number: str
    asset_id: UUID
    template_id: UUID | None = None
    inspector_id: UUID
    inspection_date: date
    overall_outcome: str
    safety_risk_detected: bool
    action_taken: str
    checklist_results: list[dict[str, Any]]
    findings_summary: str | None = None
    corrective_action_required: bool
    corrective_action_due_date: date | None = None
    corrective_action_owner_id: UUID | None = None
    corrective_action_status: str
    evidence_attachments: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 9. WARRANTY & SERVICE CONTRACT SCHEMAS
# =============================================================================


class AssetWarrantyContractCreate(BaseModel):
    asset_id: UUID
    vendor_id: UUID | None = None
    contract_type: str = ContractType.MANUFACTURER_WARRANTY
    contract_number: str = Field(..., max_length=128)
    provider_name: str = Field(..., max_length=255)
    start_date: date
    end_date: date
    coverage_terms: str | None = None
    exclusions: str | None = None
    sla_response_hours: int = 24
    cost: Decimal = Decimal("0.00")
    status: str = ContractStatus.ACTIVE
    renewal_reminder_days: int = 30
    documents: list[dict[str, Any]] = Field(default_factory=list)


class AssetWarrantyContractUpdate(BaseModel):
    vendor_id: UUID | None = None
    contract_type: str | None = None
    contract_number: str | None = None
    provider_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    coverage_terms: str | None = None
    exclusions: str | None = None
    sla_response_hours: int | None = None
    cost: Decimal | None = None
    status: str | None = None
    renewal_reminder_days: int | None = None
    documents: list[dict[str, Any]] | None = None


class AssetWarrantyContractResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    asset_id: UUID
    vendor_id: UUID | None = None
    contract_type: str
    contract_number: str
    provider_name: str
    start_date: date
    end_date: date
    coverage_terms: str | None = None
    exclusions: str | None = None
    sla_response_hours: int
    cost: Decimal
    status: str
    renewal_reminder_days: int
    documents: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WarrantyClaimCreate(BaseModel):
    contract_id: UUID
    incident_date: date = Field(default_factory=date.today)
    issue_description: str = Field(..., min_length=5)
    vendor_ticket_reference: str | None = None
    supporting_evidence: list[dict[str, Any]] = Field(default_factory=list)


class WarrantyClaimResolveRequest(BaseModel):
    status: str = WarrantyClaimStatus.RESOLVED if hasattr(WarrantyClaimStatus, "RESOLVED") else "REPLACED"
    resolution_summary: str = Field(..., min_length=3)
    reimbursement_amount: Decimal = Decimal("0.00")


class WarrantyClaimResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    claim_number: str
    contract_id: UUID
    asset_id: UUID
    incident_date: date
    issue_description: str
    vendor_ticket_reference: str | None = None
    status: str
    resolution_summary: str | None = None
    reimbursement_amount: Decimal
    resolved_at: datetime | None = None
    supporting_evidence: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 10. DEPRECIATION SCHEMAS
# =============================================================================


class AssetDepreciationScheduleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    asset_id: UUID
    fiscal_year: str
    period_name: str
    period_start_date: date
    period_end_date: date
    opening_book_value: Decimal
    depreciation_amount: Decimal
    closing_book_value: Decimal
    is_posted: bool
    posted_at: datetime | None = None
    posted_by_id: UUID | None = None
    journal_entry_reference: str | None = None
    reversal_reference: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepreciationCalculationRequest(BaseModel):
    fiscal_year: str = Field(..., max_length=16)  # e.g., "2026-2027"
    period_name: str = Field(..., max_length=32)  # e.g., "2026-04" or "Q1"
    period_start_date: date
    period_end_date: date
    asset_id: UUID | None = None  # None = all active assets in tenant


class DepreciationPostRequest(BaseModel):
    schedule_ids: list[UUID] = Field(..., min_length=1)
    journal_entry_reference: str | None = None


class DepreciationPostResponse(BaseModel):
    posted_count: int
    total_depreciation_posted: Decimal
    journal_entry_reference: str


# =============================================================================
# 11. ASSET AUDIT & PHYSICAL VERIFICATION SCHEMAS
# =============================================================================


class AssetAuditCampaignCreate(BaseModel):
    campaign_code: str | None = None
    title: str = Field(..., max_length=255)
    description: str | None = None
    campus_id: UUID | None = None
    building: str | None = None
    department_id: UUID | None = None
    category_id: UUID | None = None
    start_date: date
    end_date: date
    lead_auditor_id: UUID


class AssetAuditCampaignUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    end_date: date | None = None


class AssetAuditCampaignResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    campaign_code: str
    title: str
    description: str | None = None
    campus_id: UUID | None = None
    building: str | None = None
    department_id: UUID | None = None
    category_id: UUID | None = None
    start_date: date
    end_date: date
    status: str
    lead_auditor_id: UUID
    total_assets_scoped: int
    total_verified: int
    total_discrepancies: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetAuditItemScanRequest(BaseModel):
    scanned_tag: str = Field(..., max_length=64)
    actual_campus_id: UUID | None = None
    actual_building: str | None = None
    actual_room: str | None = None
    actual_custodian_id: UUID | None = None
    actual_condition: str | None = AssetCondition.GOOD
    evidence_attachments: list[dict[str, Any]] = Field(default_factory=list)


class AssetAuditItemReconcileRequest(BaseModel):
    reconciliation_status: str = Field(..., pattern="^(APPROVED_UPDATED|DISPUTED|RESOLVED|IGNORED)$")
    reconciliation_notes: str = Field(..., min_length=3)
    apply_to_master: bool = False  # If True, updates authoritative Asset record location/custodian


class AssetAuditItemResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    asset_id: UUID | None = None
    scanned_tag: str
    verification_status: str
    expected_campus_id: UUID | None = None
    actual_campus_id: UUID | None = None
    expected_building: str | None = None
    actual_building: str | None = None
    expected_room: str | None = None
    actual_room: str | None = None
    expected_custodian_id: UUID | None = None
    actual_custodian_id: UUID | None = None
    expected_condition: str | None = None
    actual_condition: str | None = None
    verified_by_id: UUID
    verified_at: datetime
    reconciliation_status: str
    reconciliation_notes: str | None = None
    evidence_attachments: list[dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 12. ASSET RETIREMENT & DISPOSAL SCHEMAS
# =============================================================================


class AssetRetirementRequestCreate(BaseModel):
    asset_id: UUID
    retirement_reason: str = RetirementReason.BEYOND_ECONOMIC_REPAIR
    disposal_method: str = DisposalMethod.RECYCLING
    technical_assessment_notes: str = Field(..., min_length=10)
    estimated_residual_value: Decimal = Decimal("0.00")


class AssetRetirementApprovalRequest(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    notes: str | None = None


class AssetRetirementExecuteRequest(BaseModel):
    actual_realized_value: Decimal = Decimal("0.00")
    data_wiped: bool = False
    data_wipe_certificate_url: str | None = None
    disposal_certificate_url: str | None = None


class AssetRetirementRequestResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    request_number: str
    asset_id: UUID
    requested_by_id: UUID
    retirement_reason: str
    disposal_method: str
    technical_assessment_notes: str
    estimated_residual_value: Decimal
    actual_realized_value: Decimal
    status: str
    approved_by_id: UUID | None = None
    approved_at: datetime | None = None
    data_wiped: bool
    data_wipe_certificate_url: str | None = None
    disposal_certificate_url: str | None = None
    completed_at: datetime | None = None
    reconciliation_checks_passed: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 13. REPORTING & ANALYTICS SCHEMAS
# =============================================================================


class AssetSummaryAnalyticsReport(BaseModel):
    total_assets: int
    total_acquisition_value: Decimal
    total_current_book_value: Decimal
    total_accumulated_depreciation: Decimal
    assets_by_lifecycle_state: dict[str, int]
    assets_by_category: dict[str, int]
    assets_by_criticality: dict[str, int]
    assets_by_condition: dict[str, int]
    missing_or_damaged_count: int
    restricted_assets_count: int


class AssetMaintenanceAnalyticsReport(BaseModel):
    total_work_orders: int
    open_work_orders: int
    critical_work_orders: int
    preventive_compliance_rate: Decimal
    total_downtime_hours: Decimal
    total_maintenance_cost: Decimal
    total_parts_cost: Decimal
    total_labor_cost: Decimal


class AssetComplianceAnalyticsReport(BaseModel):
    total_inspections: int
    passed_inspections: int
    failed_inspections: int
    safety_violations_detected: int
    expiring_warranties_30_days: int
    active_warranty_claims: int
    open_audit_discrepancies: int

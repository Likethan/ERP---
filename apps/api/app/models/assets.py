"""CampusOS Enterprise Asset Lifecycle, Maintenance, Facilities & Equipment Management Models (Step 53).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Enterprise Data Models Governing:
1. Asset Classification & Policy Configuration
2. Institutional Asset Registry
3. Asset Lifecycle State Machine & Audit History
4. Controlled Asset Custody, Assignments & Transfers
5. Preventive & Corrective Maintenance (Plans, Work Orders, Parts Consumption)
6. Periodic Inspections, Safety Checks & Regulatory Compliance
7. Warranties, Service Contracts (AMC/CMC/SLA) & Vendor Claims
8. Depreciation Schedules & Fixed Asset Accounting References
9. Physical Asset Audits, Tag Verification & Discrepancy Reconciliation
10. Controlled Asset Retirement, Data Wiping & Certified Disposal
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# =============================================================================
# ENUM TAXONOMY
# =============================================================================


class AssetCategoryType(StrEnum):
    """Institutional classification of physical and digital assets."""

    IT_EQUIPMENT = "IT_EQUIPMENT"
    LABORATORY_EQUIPMENT = "LABORATORY_EQUIPMENT"
    LAB_EQUIPMENT = "LABORATORY_EQUIPMENT"
    FURNITURE = "FURNITURE"
    VEHICLE = "VEHICLE"
    VEHICLES = "VEHICLE"
    ELECTRICAL_EQUIPMENT = "ELECTRICAL_EQUIPMENT"
    ELECTRICAL = "ELECTRICAL_EQUIPMENT"
    LIBRARY_EQUIPMENT = "LIBRARY_EQUIPMENT"
    FACILITY_PLANT = "FACILITY_PLANT"
    SPORTS_EQUIPMENT = "SPORTS_EQUIPMENT"
    MEDICAL_EQUIPMENT = "MEDICAL_EQUIPMENT"
    OTHER = "OTHER"


class AssetCondition(StrEnum):
    """Physical condition grading."""

    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"


class AssetOperationalStatus(StrEnum):
    """Real-time operational readiness state."""

    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    RESTRICTED = "RESTRICTED"
    NON_OPERATIONAL = "NON_OPERATIONAL"
    IN_MAINTENANCE = "IN_MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class AssetCriticality(StrEnum):
    """Impact severity if asset is unavailable."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MISSION_CRITICAL = "MISSION_CRITICAL"


class AssetUsageClassification(StrEnum):
    """Institutional utility domain."""

    ACADEMIC = "ACADEMIC"
    RESEARCH = "RESEARCH"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    FACILITY = "FACILITY"
    SHARED = "SHARED"


class AssetLifecycleState(StrEnum):
    """Formal asset lifecycle state machine."""

    REQUESTED = "REQUESTED"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    UNDER_INSPECTION = "UNDER_INSPECTION"
    COMMISSIONED = "COMMISSIONED"
    IN_SERVICE = "IN_SERVICE"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    LOST_OR_MISSING = "LOST_OR_MISSING"
    DAMAGED = "DAMAGED"
    PENDING_DISPOSAL = "PENDING_DISPOSAL"
    RETIRED = "RETIRED"
    DISPOSED = "DISPOSED"


class AssetSource(StrEnum):
    """Acquisition channel."""

    PURCHASE = "PURCHASE"
    DONATION = "DONATION"
    GRANT = "GRANT"
    TRANSFER = "TRANSFER"
    LEASE = "LEASE"
    OTHER = "OTHER"


class DepreciationMethod(StrEnum):
    """Accounting depreciation calculation method."""

    STRAIGHT_LINE = "STRAIGHT_LINE"
    DECLINING_BALANCE = "DECLINING_BALANCE"
    SUM_OF_YEARS_DIGITS = "SUM_OF_YEARS_DIGITS"
    NONE = "NONE"


class AssignmentType(StrEnum):
    """Custody allocation scope."""

    EMPLOYEE = "EMPLOYEE"
    DEPARTMENT = "DEPARTMENT"
    LOCATION = "LOCATION"
    TEMPORARY_LOAN = "TEMPORARY_LOAN"


class AssignmentStatus(StrEnum):
    """Lifecycle state of an asset custody assignment."""

    PENDING_ACKNOWLEDGEMENT = "PENDING_ACKNOWLEDGEMENT"
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    DISPUTED = "DISPUTED"
    OVERDUE = "OVERDUE"


class TransferStatus(StrEnum):
    """Inter-departmental or cross-campus asset transfer lifecycle."""

    DRAFT = "DRAFT"
    REQUESTED = "REQUESTED"
    PENDING_DISPATCH = "PENDING_DISPATCH"
    APPROVED = "APPROVED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class MaintenanceOrderType(StrEnum):
    """Maintenance category."""

    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    EMERGENCY = "EMERGENCY"
    INSPECTION_REMEDIAL = "INSPECTION_REMEDIAL"


class MaintenancePriority(StrEnum):
    """Triage priority."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class MaintenanceSeverity(StrEnum):
    """Defect severity."""

    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class MaintenanceOperationalImpact(StrEnum):
    """Degree of service interruption."""

    NO_IMPACT = "NO_IMPACT"
    PARTIAL_DEGRADATION = "PARTIAL_DEGRADATION"
    FULL_OUTAGE = "FULL_OUTAGE"


class MaintenanceOrderStatus(StrEnum):
    """Work order execution lifecycle."""

    REPORTED = "REPORTED"
    TRIAGED = "TRIAGED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_PARTS = "AWAITING_PARTS"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class PartConsumptionStatus(StrEnum):
    """Spare part reservation and consumption state."""

    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class InspectionOutcome(StrEnum):
    """Safety and quality inspection determination."""

    PASS = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    FAIL = "FAIL"
    OBSERVATION_ONLY = "OBSERVATION_ONLY"


class InspectionActionTaken(StrEnum):
    """Remedial safety protocol applied."""

    NONE = "NONE"
    EQUIPMENT_RESTRICTED = "EQUIPMENT_RESTRICTED"
    OPERATIONAL_RESTRICTION = "OPERATIONAL_RESTRICTION"
    WORK_ORDER_CREATED = "WORK_ORDER_CREATED"


class ContractType(StrEnum):
    """Service agreement contract type."""

    MANUFACTURER_WARRANTY = "MANUFACTURER_WARRANTY"
    EXTENDED_WARRANTY = "EXTENDED_WARRANTY"
    AMC = "AMC"
    CMC = "CMC"
    SLA = "SLA"


class ContractStatus(StrEnum):
    """Agreement active state."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"
    RENEWED = "RENEWED"


class WarrantyClaimStatus(StrEnum):
    """Warranty claim processing state."""

    FILED = "FILED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_REPAIR = "UNDER_REPAIR"
    REPLACED = "REPLACED"
    REIMBURSED = "REIMBURSED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class AuditCampaignStatus(StrEnum):
    """Physical verification audit campaign state."""

    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    RECONCILIATION = "RECONCILIATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AuditVerificationStatus(StrEnum):
    """Single asset verification finding."""

    VERIFIED_MATCH = "VERIFIED_MATCH"
    RELOCATED = "RELOCATED"
    CUSTODIAN_MISMATCH = "CUSTODIAN_MISMATCH"
    CONDITION_CHANGED = "CONDITION_CHANGED"
    UNREGISTERED_FOUND = "UNREGISTERED_FOUND"
    MISSING = "MISSING"


class AuditReconciliationStatus(StrEnum):
    """Discrepancy reconciliation disposition."""

    PENDING = "PENDING"
    APPROVED_UPDATED = "APPROVED_UPDATED"
    DISPUTED = "DISPUTED"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"


class RetirementReason(StrEnum):
    """Justification for asset decommissioning."""

    BEYOND_ECONOMIC_REPAIR = "BEYOND_ECONOMIC_REPAIR"
    OBSOLETE = "OBSOLETE"
    DAMAGED = "DAMAGED"
    LOST = "LOST"
    SURPLUS = "SURPLUS"
    REGULATORY_MANDATE = "REGULATORY_MANDATE"


class DisposalMethod(StrEnum):
    """Authorized asset disposal disposition."""

    AUCTION_SALE = "AUCTION_SALE"
    DONATION = "DONATION"
    RECYCLING = "RECYCLING"
    DESTRUCTION = "DESTRUCTION"
    RETURN_TO_MANUFACTURER = "RETURN_TO_MANUFACTURER"


class RetirementRequestStatus(StrEnum):
    """Decommissioning approval and execution lifecycle."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_EVALUATION = "UNDER_EVALUATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISPOSAL_IN_PROGRESS = "DISPOSAL_IN_PROGRESS"
    DISPOSED = "DISPOSED"


# =============================================================================
# 1. ASSET CATEGORIES & POLICY CONFIGURATION
# =============================================================================


class AssetCategory(TenantScopedModel):
    """Institutional asset classification taxonomy and management policy configuration."""

    __tablename__ = "asset_categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_asset_category_tenant_code"),
        Index("idx_asset_category_tenant_type", "tenant_id", "category_type"),
        Index("idx_asset_category_tenant_active", "tenant_id", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_type: Mapped[str] = mapped_column(
        String(32), default=AssetCategoryType.OTHER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Policy Defaults
    requires_serial_number: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_custodian_acknowledgement: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    default_inspection_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_maintenance_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_criticality: Mapped[str] = mapped_column(
        String(32), default=AssetCriticality.MEDIUM, nullable=False
    )

    # Depreciation Policy Defaults
    default_depreciation_method: Mapped[str] = mapped_column(
        String(32), default=DepreciationMethod.STRAIGHT_LINE, nullable=False
    )
    default_useful_life_months: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    default_salvage_value_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("5.00"), nullable=False
    )

    # Policy Rules & Attribute Schema
    policy_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    assignment_restrictions: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    # Relationships
    assets: Mapped[list["Asset"]] = relationship(back_populates="category")


# =============================================================================
# 2. INSTITUTIONAL ASSET REGISTRY
# =============================================================================


class Asset(TenantScopedModel):
    """Centralized enterprise institutional asset record."""

    __tablename__ = "asset_registry"
    __table_args__ = (
        UniqueConstraint("tenant_id", "asset_tag", name="uq_asset_registry_tenant_tag"),
        Index("idx_asset_registry_tenant_cat", "tenant_id", "category_id"),
        Index("idx_asset_registry_tenant_state", "tenant_id", "lifecycle_state"),
        Index("idx_asset_registry_tenant_campus", "tenant_id", "campus_id"),
        Index("idx_asset_registry_tenant_dept", "tenant_id", "department_id"),
        Index("idx_asset_registry_tenant_custodian", "tenant_id", "current_custodian_id"),
        Index("idx_asset_registry_serial", "tenant_id", "serial_number"),
    )

    # Identification & Tagging
    asset_tag: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., AST-2026-00001
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_categories.id", ondelete="RESTRICT"), nullable=False
    )
    asset_type: Mapped[str] = mapped_column(String(64), default="GENERAL", nullable=False)
    make: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    barcode_data: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Procurement & Commercial Reference
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    acquisition_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(16), default="INR", nullable=False)
    source: Mapped[str] = mapped_column(String(32), default=AssetSource.PURCHASE, nullable=False)
    supplier_vendor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="SET NULL"), nullable=True
    )
    purchase_order_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_orders.id", ondelete="SET NULL"), nullable=True
    )
    purchase_order_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_order_lines.id", ondelete="SET NULL"), nullable=True
    )
    goods_receipt_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_goods_receipts.id", ondelete="SET NULL"), nullable=True
    )
    invoice_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Location & Physical Placement
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=True
    )
    building: Mapped[str | None] = mapped_column(String(128), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(32), nullable=True)
    room_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )

    # Custody
    current_custodian_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )

    # Condition & Operational State
    condition: Mapped[str] = mapped_column(
        String(32), default=AssetCondition.GOOD, nullable=False
    )
    operational_status: Mapped[str] = mapped_column(
        String(32), default=AssetOperationalStatus.OPERATIONAL, nullable=False
    )
    criticality: Mapped[str] = mapped_column(
        String(32), default=AssetCriticality.MEDIUM, nullable=False
    )
    usage_classification: Mapped[str] = mapped_column(
        String(32), default=AssetUsageClassification.ACADEMIC, nullable=False
    )
    lifecycle_state: Mapped[str] = mapped_column(
        String(32), default=AssetLifecycleState.REQUESTED, nullable=False
    )
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    restriction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Warranty & Service Contracts
    warranty_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    warranty_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Maintenance & Inspection Milestones
    last_maintained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_maintenance_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_inspected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_inspection_due: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial & Depreciation Tracking
    depreciation_method: Mapped[str] = mapped_column(
        String(32), default=DepreciationMethod.STRAIGHT_LINE, nullable=False
    )
    useful_life_months: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    salvage_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    accumulated_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    current_book_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    last_depreciated_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Documents & Media
    image_keys: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    document_references: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    custom_attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    category: Mapped["AssetCategory"] = relationship(back_populates="assets")
    lifecycle_history: Mapped[list["AssetLifecycleEvent"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", order_by="AssetLifecycleEvent.performed_at.desc()"
    )
    assignments: Mapped[list["AssetAssignment"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", order_by="AssetAssignment.effective_date.desc()"
    )
    transfers: Mapped[list["AssetTransfer"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    work_orders: Mapped[list["MaintenanceWorkOrder"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    inspections: Mapped[list["InspectionRecord"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    warranty_contracts: Mapped[list["AssetWarrantyContract"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )
    depreciation_schedules: Mapped[list["AssetDepreciationSchedule"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", order_by="AssetDepreciationSchedule.period_start_date.asc()"
    )


# =============================================================================
# 3. ASSET LIFECYCLE HISTORY
# =============================================================================


class AssetLifecycleEvent(TenantScopedModel):
    """Immutable audit trail for asset lifecycle state transitions."""

    __tablename__ = "asset_lifecycle_events"
    __table_args__ = (
        Index("idx_asset_lifecycle_tenant_asset", "tenant_id", "asset_id"),
        Index("idx_asset_lifecycle_perf_at", "tenant_id", "performed_at"),
    )

    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=False
    )
    from_state: Mapped[str] = mapped_column(String(32), nullable=False)
    to_state: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_documents: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    actor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    asset: Mapped["Asset"] = relationship(back_populates="lifecycle_history")


# =============================================================================
# 4. ASSET ASSIGNMENT & CUSTODY MANAGEMENT
# =============================================================================


class AssetAssignment(TenantScopedModel):
    """Authoritative custody assignment record."""

    __tablename__ = "asset_assignments"
    __table_args__ = (
        Index("idx_asset_assign_tenant_asset", "tenant_id", "asset_id"),
        Index("idx_asset_assign_custodian", "tenant_id", "custodian_id"),
        Index("idx_asset_assign_status", "tenant_id", "status"),
    )

    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=False
    )
    assignment_type: Mapped[str] = mapped_column(
        String(32), default=AssignmentType.EMPLOYEE, nullable=False
    )
    custodian_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=True
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="RESTRICT"), nullable=True
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=True
    )
    location_details: Mapped[str | None] = mapped_column(String(255), nullable=True)

    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=AssignmentStatus.ACTIVE, nullable=False
    )

    acknowledgement_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledgement_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    condition_at_assignment: Mapped[str] = mapped_column(
        String(32), default=AssetCondition.GOOD, nullable=False
    )
    condition_at_return: Mapped[str | None] = mapped_column(String(32), nullable=True)
    handover_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    supporting_evidence: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )

    asset: Mapped["Asset"] = relationship(back_populates="assignments")


class AssetTransfer(TenantScopedModel):
    """Controlled multi-stage transfer between campuses, departments, or custodians."""

    __tablename__ = "asset_transfers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "transfer_number", name="uq_asset_transfer_number"),
        Index("idx_asset_transfer_tenant_asset", "tenant_id", "asset_id"),
        Index("idx_asset_transfer_status", "tenant_id", "status"),
    )

    transfer_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., TRF-2026-0001
    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=False
    )

    # Origin
    from_campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=True
    )
    from_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="RESTRICT"), nullable=True
    )
    from_custodian_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=True
    )

    # Destination
    to_campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=True
    )
    to_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="RESTRICT"), nullable=True
    )
    to_custodian_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=True
    )

    transfer_reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=TransferStatus.REQUESTED, nullable=False
    )

    initiated_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    in_transit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )

    dispatch_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="transfers")


# =============================================================================
# 5. PREVENTIVE & CORRECTIVE MAINTENANCE
# =============================================================================


class MaintenancePlan(TenantScopedModel):
    """Recurring preventive maintenance plan."""

    __tablename__ = "asset_maintenance_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "plan_code", name="uq_maintenance_plan_code"),
        Index("idx_maint_plan_tenant_cat", "tenant_id", "category_id"),
        Index("idx_maint_plan_tenant_asset", "tenant_id", "asset_id"),
    )

    plan_code: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., PM-GENSET-MONTHLY
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_categories.id", ondelete="SET NULL"), nullable=True
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=True
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )

    interval_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    estimated_duration_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("2.00"), nullable=False
    )
    checklist: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    assigned_technician_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    preferred_vendor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    work_orders: Mapped[list["MaintenanceWorkOrder"]] = relationship(back_populates="plan")


class MaintenanceWorkOrder(TenantScopedModel):
    """Actionable maintenance work order."""

    __tablename__ = "asset_maintenance_work_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "work_order_number", name="uq_maintenance_wo_number"),
        Index("idx_maint_wo_tenant_asset", "tenant_id", "asset_id"),
        Index("idx_maint_wo_tenant_status", "tenant_id", "status"),
        Index("idx_maint_wo_tenant_priority", "tenant_id", "priority"),
    )

    work_order_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., WO-2026-0001
    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="RESTRICT"), nullable=False
    )
    plan_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_maintenance_plans.id", ondelete="SET NULL"), nullable=True
    )

    order_type: Mapped[str] = mapped_column(
        String(32), default=MaintenanceOrderType.CORRECTIVE, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(32), default=MaintenancePriority.MEDIUM, nullable=False
    )
    severity: Mapped[str] = mapped_column(
        String(32), default=MaintenanceSeverity.MODERATE, nullable=False
    )
    operational_impact: Mapped[str] = mapped_column(
        String(32), default=MaintenanceOperationalImpact.NO_IMPACT, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=MaintenanceOrderStatus.REPORTED, nullable=False
    )

    reported_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    reported_symptoms: Mapped[str] = mapped_column(Text, nullable=False)

    scheduled_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    scheduled_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assigned_technician_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    vendor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="SET NULL"), nullable=True
    )

    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    repair_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    downtime_hours: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0.00"), nullable=False
    )
    labor_hours: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0.00"), nullable=False
    )

    # Cost Tracking
    labor_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    parts_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    service_charges: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    estimated_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    # Verification & Closure Control
    verification_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    attachments: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    checklist_results: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    reopen_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="work_orders")
    plan: Mapped["MaintenancePlan | None"] = relationship(back_populates="work_orders")
    parts_consumed: Mapped[list["WorkOrderPartConsumption"]] = relationship(
        back_populates="work_order", cascade="all, delete-orphan"
    )

    @property
    def title(self) -> str:
        return self.reported_symptoms or ""

    @title.setter
    def title(self, value: str):
        self.reported_symptoms = value


class WorkOrderPartConsumption(TenantScopedModel):
    """Spare parts and materials reserved and consumed against a work order."""

    __tablename__ = "asset_wo_part_consumptions"
    __table_args__ = (
        Index("idx_asset_wo_parts_wo", "tenant_id", "work_order_id"),
        Index("idx_asset_wo_parts_item", "tenant_id", "inventory_item_id"),
    )

    work_order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("asset_maintenance_work_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    inventory_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("procurement_inventory_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    inventory_location_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("procurement_inventory_locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity_reserved: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    quantity_consumed: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    quantity_returned: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=PartConsumptionStatus.RESERVED, nullable=False
    )
    stock_movement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("procurement_stock_movements.id", ondelete="SET NULL"),
        nullable=True,
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    work_order: Mapped["MaintenanceWorkOrder"] = relationship(back_populates="parts_consumed")


# =============================================================================
# 6. INSPECTIONS, SAFETY & REGULATORY COMPLIANCE
# =============================================================================


class InspectionTemplate(TenantScopedModel):
    """Institutional inspection and safety checklist template."""

    __tablename__ = "asset_inspection_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_inspection_template_code"),
        Index("idx_insp_template_tenant_cat", "tenant_id", "category_id"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., INSP-FIRE-SAFETY
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_categories.id", ondelete="SET NULL"), nullable=True
    )
    frequency_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    checklist_items: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    inspections: Mapped[list["InspectionRecord"]] = relationship(back_populates="template")


class InspectionRecord(TenantScopedModel):
    """Recorded outcome of physical safety and compliance inspection."""

    __tablename__ = "asset_inspection_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "inspection_number", name="uq_inspection_record_number"),
        Index("idx_asset_insp_tenant_asset", "tenant_id", "asset_id"),
        Index("idx_asset_insp_tenant_date", "tenant_id", "inspection_date"),
        Index("idx_asset_insp_outcome", "tenant_id", "overall_outcome"),
    )

    inspection_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., INS-2026-0001
    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("asset_inspection_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    inspector_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    inspection_date: Mapped[date] = mapped_column(Date, nullable=False)

    overall_outcome: Mapped[str] = mapped_column(
        String(32), default=InspectionOutcome.PASS, nullable=False
    )
    safety_risk_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    action_taken: Mapped[str] = mapped_column(
        String(32), default=InspectionActionTaken.NONE, nullable=False
    )

    checklist_results: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    findings_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Remedial Action
    corrective_action_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    corrective_action_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    corrective_action_owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    corrective_action_status: Mapped[str] = mapped_column(
        String(32), default="RESOLVED", nullable=False
    )  # PENDING, IN_PROGRESS, RESOLVED, ESCALATED
    evidence_attachments: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )

    asset: Mapped["Asset"] = relationship(back_populates="inspections")
    template: Mapped["InspectionTemplate | None"] = relationship(back_populates="inspections")


# =============================================================================
# 7. WARRANTIES, SERVICE CONTRACTS (AMC/CMC) & CLAIMS
# =============================================================================


class AssetWarrantyContract(TenantScopedModel):
    """Warranty policy, AMC/CMC agreement, or vendor service contract."""

    __tablename__ = "asset_warranties_contracts"
    __table_args__ = (
        Index("idx_asset_contract_tenant_asset", "tenant_id", "asset_id"),
        Index("idx_asset_contract_vendor", "tenant_id", "vendor_id"),
        Index("idx_asset_contract_status", "tenant_id", "status"),
        Index("idx_asset_contract_expiry", "tenant_id", "end_date"),
    )

    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=False
    )
    vendor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="SET NULL"), nullable=True
    )
    contract_type: Mapped[str] = mapped_column(
        String(32), default=ContractType.MANUFACTURER_WARRANTY, nullable=False
    )
    contract_number: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    coverage_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusions: Mapped[str | None] = mapped_column(Text, nullable=True)
    sla_response_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ContractStatus.ACTIVE, nullable=False
    )
    renewal_reminder_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    documents: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)

    asset: Mapped["Asset"] = relationship(back_populates="warranty_contracts")
    claims: Mapped[list["WarrantyClaim"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan"
    )


class WarrantyClaim(TenantScopedModel):
    """Formal warranty or service contract claim."""

    __tablename__ = "asset_warranty_claims"
    __table_args__ = (
        UniqueConstraint("tenant_id", "claim_number", name="uq_warranty_claim_number"),
        Index("idx_warranty_claim_contract", "tenant_id", "contract_id"),
        Index("idx_warranty_claim_asset", "tenant_id", "asset_id"),
    )

    claim_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., CLM-2026-0001
    contract_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("asset_warranties_contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=False
    )
    incident_date: Mapped[date] = mapped_column(Date, nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    vendor_ticket_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=WarrantyClaimStatus.FILED, nullable=False
    )

    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reimbursement_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supporting_evidence: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )

    contract: Mapped["AssetWarrantyContract"] = relationship(back_populates="claims")


# =============================================================================
# 8. DEPRECIATION SCHEDULES & ACCOUNTING INTEGRATION
# =============================================================================


class AssetDepreciationSchedule(TenantScopedModel):
    """Period-based fixed-asset depreciation computation and finance reference."""

    __tablename__ = "asset_depreciation_schedules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "asset_id", "fiscal_year", "period_name", name="uq_asset_depr_period"),
        Index("idx_asset_depr_tenant_asset", "tenant_id", "asset_id"),
        Index("idx_asset_depr_fiscal", "tenant_id", "fiscal_year", "period_name"),
    )

    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g., "2026-2027"
    period_name: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g., "2026-04" or "Q1"
    period_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_end_date: Mapped[date] = mapped_column(Date, nullable=False)

    opening_book_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    depreciation_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    closing_book_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    is_posted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    journal_entry_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reversal_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="depreciation_schedules")


# =============================================================================
# 9. PHYSICAL ASSET AUDITS & VERIFICATION
# =============================================================================


class AssetAuditCampaign(TenantScopedModel):
    """Institutional physical audit campaign for stocktaking and tag scanning."""

    __tablename__ = "asset_audit_campaigns"
    __table_args__ = (
        UniqueConstraint("tenant_id", "campaign_code", name="uq_asset_audit_campaign_code"),
        Index("idx_asset_audit_status", "tenant_id", "status"),
    )

    campaign_code: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., AUD-2026-CAMPUS-A
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=True
    )
    building: Mapped[str | None] = mapped_column(String(128), nullable=True)
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_categories.id", ondelete="SET NULL"), nullable=True
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=AuditCampaignStatus.PLANNED, nullable=False
    )
    lead_auditor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )

    total_assets_scoped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_verified: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_discrepancies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    items: Mapped[list["AssetAuditItem"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class AssetAuditItem(TenantScopedModel):
    """Individual verification scan within an audit campaign."""

    __tablename__ = "asset_audit_items"
    __table_args__ = (
        Index("idx_audit_items_campaign", "tenant_id", "campaign_id"),
        Index("idx_audit_items_asset", "tenant_id", "asset_id"),
    )

    campaign_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("asset_audit_campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=True
    )
    scanned_tag: Mapped[str] = mapped_column(String(64), nullable=False)

    verification_status: Mapped[str] = mapped_column(
        String(32), default=AuditVerificationStatus.VERIFIED_MATCH, nullable=False
    )

    # Expected vs Actual
    expected_campus_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    actual_campus_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    expected_building: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actual_building: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expected_room: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actual_room: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expected_custodian_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    actual_custodian_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    expected_condition: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actual_condition: Mapped[str | None] = mapped_column(String(32), nullable=True)

    verified_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    reconciliation_status: Mapped[str] = mapped_column(
        String(32), default=AuditReconciliationStatus.PENDING, nullable=False
    )
    reconciliation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_attachments: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )

    campaign: Mapped["AssetAuditCampaign"] = relationship(back_populates="items")


# =============================================================================
# 10. ASSET RETIREMENT & DISPOSAL
# =============================================================================


class AssetRetirementRequest(TenantScopedModel):
    """Formal asset decommissioning, technical condemnation, and certified disposal."""

    __tablename__ = "asset_retirement_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_number", name="uq_asset_retirement_req_number"),
        Index("idx_asset_retire_tenant_asset", "tenant_id", "asset_id"),
        Index("idx_asset_retire_status", "tenant_id", "status"),
    )

    request_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., RET-2026-0001
    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_registry.id", ondelete="RESTRICT"), nullable=False
    )
    requested_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    retirement_reason: Mapped[str] = mapped_column(
        String(32), default=RetirementReason.BEYOND_ECONOMIC_REPAIR, nullable=False
    )
    disposal_method: Mapped[str] = mapped_column(
        String(32), default=DisposalMethod.RECYCLING, nullable=False
    )
    technical_assessment_notes: Mapped[str] = mapped_column(Text, nullable=False)

    estimated_residual_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    actual_realized_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(32), default=RetirementRequestStatus.DRAFT, nullable=False
    )
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # IT Data Sanitization & Physical Certification
    data_wiped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_wipe_certificate_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    disposal_certificate_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reconciliation_checks_passed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

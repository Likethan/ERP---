"""CampusOS Enterprise Sustainability, Energy Management, Environmental Compliance & Carbon Intelligence Models (Step 67).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Enterprise Data Models Governing:
1. Campus Sustainability Profiles, Targets & Net-Zero Baselines
2. Versioned Emission Factors & Warming Potentials (Scope 1, 2, 3)
3. Energy & Water Resource Measurements with Anomaly Detection
4. Water Loss & Leak Incident Corrective Audits
5. Solid, Organic, Recyclable, E-Waste & Regulated Hazardous Waste Manifests
6. Carbon Emissions Calculations (Verified GHG Accounting Engine)
7. Campus Green Initiatives & Capital Sustainability Projects
8. Environmental Compliance Permits, SPCB / Statutory Consents & Audits
9. Environmental Corrective Actions & Facilities Work Order Escalations
10. IoT Smart Meter Devices, Streams & Telemetry Ingestion Events (with De-duplication)
11. Sustainability Import Batches for Historical & Invoice Reconciliations
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
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

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


# =============================================================================
# ENUM TAXONOMY
# =============================================================================

class TargetCategory(StrEnum):
    ENERGY_REDUCTION = "ENERGY_REDUCTION"
    RENEWABLE_SHARE = "RENEWABLE_SHARE"
    WATER_CONSERVATION = "WATER_CONSERVATION"
    WASTE_DIVERSION = "WASTE_DIVERSION"
    SCOPE_1_REDUCTION = "SCOPE_1_REDUCTION"
    SCOPE_2_REDUCTION = "SCOPE_2_REDUCTION"
    SCOPE_3_REDUCTION = "SCOPE_3_REDUCTION"
    NET_ZERO_GHG = "NET_ZERO_GHG"


class TargetStatus(StrEnum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    ACHIEVED = "ACHIEVED"
    DELAYED = "DELAYED"
    UNDER_REVIEW = "UNDER_REVIEW"


class EmissionScope(StrEnum):
    SCOPE_1 = "SCOPE_1"
    SCOPE_2 = "SCOPE_2"
    SCOPE_3 = "SCOPE_3"


class EmissionFactorCategory(StrEnum):
    ELECTRICITY_GRID = "ELECTRICITY_GRID"
    DIESEL = "DIESEL"
    NATURAL_GAS = "NATURAL_GAS"
    PETROL = "PETROL"
    WATER_MUNICIPAL = "WATER_MUNICIPAL"
    WASTE_LANDFILL = "WASTE_LANDFILL"
    WASTE_COMPOSTING = "WASTE_COMPOSTING"
    STUDENT_COMMUTING = "STUDENT_COMMUTING"
    BUSINESS_TRAVEL = "BUSINESS_TRAVEL"


class ResourceType(StrEnum):
    ELECTRICITY_GRID = "ELECTRICITY_GRID"
    SOLAR_GENERATION = "SOLAR_GENERATION"
    DIESEL_GENSET = "DIESEL_GENSET"
    WATER_MUNICIPAL = "WATER_MUNICIPAL"
    WATER_BOREWELL = "WATER_BOREWELL"
    WATER_RECYCLED = "WATER_RECYCLED"
    RAINWATER_HARVESTED = "RAINWATER_HARVESTED"
    NATURAL_GAS = "NATURAL_GAS"


class MeasurementSource(StrEnum):
    IOT_SENSOR = "IOT_SENSOR"
    UTILITY_BILL = "UTILITY_BILL"
    MANUAL_METER = "MANUAL_METER"
    SUB_METER = "SUB_METER"
    ESTIMATED = "ESTIMATED"


class VerificationStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"


class WasteCategory(StrEnum):
    GENERAL = "GENERAL"
    ORGANIC_COMPOST = "ORGANIC_COMPOST"
    RECYCLABLE_PLASTIC = "RECYCLABLE_PLASTIC"
    RECYCLABLE_PAPER = "RECYCLABLE_PAPER"
    RECYCLABLE_METAL = "RECYCLABLE_METAL"
    E_WASTE = "E_WASTE"
    HAZARDOUS_CHEMICAL = "HAZARDOUS_CHEMICAL"
    BIO_MEDICAL = "BIO_MEDICAL"


class WasteDisposalMethod(StrEnum):
    COMPOSTING = "COMPOSTING"
    RECYCLING_VENDOR = "RECYCLING_VENDOR"
    REGULATED_INCINERATION = "REGULATED_INCINERATION"
    AUTHORIZED_EWASTE_FACILITY = "AUTHORIZED_EWASTE_FACILITY"
    MUNICIPAL_LANDFILL = "MUNICIPAL_LANDFILL"
    AUTHORIZED_HAZARDOUS_TSDF = "AUTHORIZED_HAZARDOUS_TSDF"


class InitiativeCategory(StrEnum):
    SOLAR_ROOFTOP = "SOLAR_ROOFTOP"
    LED_RETROFIT = "LED_RETROFIT"
    RAINWATER_HARVESTING = "RAINWATER_HARVESTING"
    COMPOSTING_UNIT = "COMPOSTING_UNIT"
    EV_SHUTTLE = "EV_SHUTTLE"
    TREE_PLANTATION = "TREE_PLANTATION"
    BEHAVIORAL_AWARENESS = "BEHAVIORAL_AWARENESS"
    BIOGAS_PLANT = "BIOGAS_PLANT"


class InitiativeStatus(StrEnum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    IN_EXECUTION = "IN_EXECUTION"
    OPERATIONAL = "OPERATIONAL"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ComplianceCategory(StrEnum):
    WATER_CONSENT = "WATER_CONSENT"
    AIR_EMISSIONS = "AIR_EMISSIONS"
    HAZARDOUS_WASTE_AUTHORIZATION = "HAZARDOUS_WASTE_AUTHORIZATION"
    E_WASTE_EPR = "E_WASTE_EPR"
    SOLAR_NET_METERING = "SOLAR_NET_METERING"
    GREEN_BUILDING_IGBC = "GREEN_BUILDING_IGBC"
    GROUNDWATER_EXTRACTION_NOC = "GROUNDWATER_EXTRACTION_NOC"


class ComplianceStatus(StrEnum):
    COMPLIANT = "COMPLIANT"
    PENDING_INSPECTION = "PENDING_INSPECTION"
    RENEWAL_DUE = "RENEWAL_DUE"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    OVERDUE = "OVERDUE"


class CorrectiveActionStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    VERIFIED = "VERIFIED"


class IngestionStatus(StrEnum):
    PROCESSED = "PROCESSED"
    DUPLICATE_SKIPPED = "DUPLICATE_SKIPPED"
    REJECTED = "REJECTED"


class ImportBatchStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# =============================================================================
# 1. CAMPUS SUSTAINABILITY PROFILE & TARGETS
# =============================================================================

class SustainabilityProfile(TenantScopedModel):
    """Institutional / Campus sustainability master profile and carbon baseline."""

    __tablename__ = "sustainability_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_sustainability_profile_code"),
        Index("idx_sustainability_profile_tenant_campus", "tenant_id", "campus_id"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True
    )
    reporting_cycle: Mapped[str] = mapped_column(String(32), default="ANNUAL", nullable=False)
    baseline_year: Mapped[int] = mapped_column(Integer, default=2022, nullable=False)
    target_net_zero_year: Mapped[int] = mapped_column(Integer, default=2040, nullable=False)
    lead_coordinator_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    coordinator_name: Mapped[str] = mapped_column(String(128), default="Sustainability Office", nullable=False)
    coordinator_email: Mapped[str] = mapped_column(String(128), default="sustainability@campus.edu", nullable=False)
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    targets: Mapped[list["SustainabilityTarget"]] = relationship(
        "SustainabilityTarget", back_populates="profile", cascade="all, delete-orphan"
    )


class SustainabilityTarget(TenantScopedModel):
    """Quantitative environmental milestone, reduction target, and KPI tracking."""

    __tablename__ = "sustainability_targets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "target_code", name="uq_sustainability_target_code"),
        Index("idx_sustainability_target_status", "tenant_id", "category", "status"),
    )

    profile_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sustainability_profiles.id", ondelete="CASCADE"), nullable=True
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True
    )
    category: Mapped[str] = mapped_column(
        String(32), default=TargetCategory.ENERGY_REDUCTION.value, nullable=False
    )
    target_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline_year: Mapped[int] = mapped_column(Integer, default=2022, nullable=False)
    baseline_value: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, default=2030, nullable=False)
    target_value: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0.000"), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="kWh", nullable=False)
    reduction_pct_target: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("25.00"), nullable=False)
    reduction_pct_achieved: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=TargetStatus.ON_TRACK.value, nullable=False
    )
    responsible_team: Mapped[str] = mapped_column(String(128), default="Estate & Facilities", nullable=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    profile: Mapped[SustainabilityProfile | None] = relationship("SustainabilityProfile", back_populates="targets")


# =============================================================================
# 2. EMISSION FACTORS REGISTRY (VERSIONED & TRACEABLE)
# =============================================================================

class EmissionFactor(TenantScopedModel):
    """Statutory or scientific GHG emission conversion factors."""

    __tablename__ = "sustainability_emission_factors"
    __table_args__ = (
        UniqueConstraint("tenant_id", "factor_code", "factor_version", name="uq_sustainability_factor_version"),
        Index("idx_sustainability_factor_lookup", "tenant_id", "category", "scope", "is_active"),
    )

    factor_code: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), default=EmissionFactorCategory.ELECTRICITY_GRID.value, nullable=False
    )
    scope: Mapped[str] = mapped_column(
        String(16), default=EmissionScope.SCOPE_2.value, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_authority: Mapped[str] = mapped_column(String(128), nullable=False)
    factor_version: Mapped[str] = mapped_column(String(32), default="v2024.1", nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    factor_value: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    unit_denominator: Mapped[str] = mapped_column(String(32), default="kWh", nullable=False)
    gwp_standard: Mapped[str] = mapped_column(String(32), default="AR5", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# =============================================================================
# 3. RESOURCE MEASUREMENTS & TELEMETRY
# =============================================================================

class ResourceMeasurement(TenantScopedModel):
    """Energy, solar generation, fuel, or water meter reading record."""

    __tablename__ = "sustainability_resource_measurements"
    __table_args__ = (
        Index("idx_sustainability_meas_lookup", "tenant_id", "campus_id", "resource_type", "period_start"),
        Index("idx_sustainability_meas_anomaly", "tenant_id", "is_anomaly"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False
    )
    building_name: Mapped[str] = mapped_column(String(128), nullable=False)
    meter_code: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(
        String(32), default=ResourceType.ELECTRICITY_GRID.value, nullable=False
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reading_value: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="kWh", nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(32), default=MeasurementSource.IOT_SENSOR.value, nullable=False
    )
    baseline_expected_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 3), nullable=True)
    variance_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anomaly_severity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    anomaly_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    verification_status: Mapped[str] = mapped_column(
        String(32), default=VerificationStatus.VERIFIED.value, nullable=False
    )
    linked_work_order_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)


# =============================================================================
# 4. WATER INCIDENTS & CONSERVATION AUDITS
# =============================================================================

class WaterIncidentRecord(TenantScopedModel):
    """Water leakage, pipe burst, or pump fault with corrective tracking."""

    __tablename__ = "sustainability_water_incidents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "incident_code", name="uq_sustainability_water_incident_code"),
        Index("idx_sustainability_water_status", "tenant_id", "status"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False
    )
    incident_code: Mapped[str] = mapped_column(String(64), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(32), default="LEAK_PIPE", nullable=False)
    location: Mapped[str] = mapped_column(String(128), nullable=False)
    estimated_loss_litres: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="DETECTED", nullable=False
    )
    linked_work_order_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    remediation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# =============================================================================
# 5. SOLID, ORGANIC & HAZARDOUS WASTE RECORDS
# =============================================================================

class WasteRecord(TenantScopedModel):
    """Waste generation, recycling manifests, and authorized hazardous disposal."""

    __tablename__ = "sustainability_waste_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "waste_code", name="uq_sustainability_waste_code"),
        Index("idx_sustainability_waste_cat", "tenant_id", "waste_category", "is_hazardous"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False
    )
    waste_code: Mapped[str] = mapped_column(String(64), nullable=False)
    waste_category: Mapped[str] = mapped_column(
        String(32), default=WasteCategory.GENERAL.value, nullable=False
    )
    is_hazardous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="kg", nullable=False)
    collection_date: Mapped[date] = mapped_column(Date, nullable=False)
    disposal_method: Mapped[str] = mapped_column(
        String(32), default=WasteDisposalMethod.RECYCLING_VENDOR.value, nullable=False
    )
    partner_name: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    certificate_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verified_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="COLLECTED", nullable=False)


# =============================================================================
# 6. CARBON EMISSIONS ACCOUNTING ENGINE (GHG PROTOCOL)
# =============================================================================

class CarbonEmissionsCalculation(TenantScopedModel):
    """Calculated and verified Scope 1, Scope 2, and Scope 3 GHG records."""

    __tablename__ = "sustainability_carbon_emissions"
    __table_args__ = (
        Index("idx_sustainability_carbon_lookup", "tenant_id", "campus_id", "reporting_period", "scope"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False
    )
    reporting_period: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(
        String(16), default=EmissionScope.SCOPE_2.value, nullable=False
    )
    activity_category: Mapped[str] = mapped_column(String(64), nullable=False)
    activity_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    activity_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    emission_factor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sustainability_emission_factors.id", ondelete="SET NULL"), nullable=True
    )
    factor_value_applied: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    factor_source_applied: Mapped[str] = mapped_column(String(128), nullable=False)
    emissions_kg_co2e: Mapped[Decimal] = mapped_column(Numeric(16, 3), nullable=False)
    emissions_mt_co2e: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(64), default="LOCATION_BASED", nullable=False)
    audit_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


# =============================================================================
# 7. SUSTAINABILITY INITIATIVES & GREEN PROJECTS
# =============================================================================

class SustainabilityInitiative(TenantScopedModel):
    """Campus green energy, efficiency, and sustainability project portfolio."""

    __tablename__ = "sustainability_initiatives"
    __table_args__ = (
        UniqueConstraint("tenant_id", "initiative_code", name="uq_sustainability_initiative_code"),
        Index("idx_sustainability_initiative_status", "tenant_id", "status"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False
    )
    initiative_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), default=InitiativeCategory.SOLAR_ROOFTOP.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=InitiativeStatus.PROPOSED.value, nullable=False
    )
    budget_allocated: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    budget_spent: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    annual_co2_savings_mt: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("0.000"), nullable=False)
    annual_energy_savings_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    annual_water_savings_kl: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsible_owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    lead_department: Mapped[str] = mapped_column(String(128), default="Estate Operations", nullable=False)


# =============================================================================
# 8. ENVIRONMENTAL COMPLIANCE & STATUTORY AUDITS
# =============================================================================

class EnvironmentalComplianceRequirement(TenantScopedModel):
    """State Pollution Control Board consents, NOCs, and environmental laws."""

    __tablename__ = "sustainability_compliance_requirements"
    __table_args__ = (
        UniqueConstraint("tenant_id", "compliance_code", name="uq_sustainability_compliance_code"),
        Index("idx_sustainability_compliance_status", "tenant_id", "status", "next_renewal_date"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False
    )
    compliance_code: Mapped[str] = mapped_column(String(64), nullable=False)
    regulation_title: Mapped[str] = mapped_column(String(255), nullable=False)
    regulatory_body: Mapped[str] = mapped_column(String(128), nullable=False)
    compliance_category: Mapped[str] = mapped_column(
        String(32), default=ComplianceCategory.WATER_CONSENT.value, nullable=False
    )
    frequency: Mapped[str] = mapped_column(String(32), default="ANNUAL", nullable=False)
    last_audit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_renewal_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ComplianceStatus.COMPLIANT.value, nullable=False
    )
    permit_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    document_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    corrective_actions: Mapped[list["EnvironmentalCorrectiveAction"]] = relationship(
        "EnvironmentalCorrectiveAction", back_populates="requirement", cascade="all, delete-orphan"
    )


class EnvironmentalCorrectiveAction(TenantScopedModel):
    """Remediation action items raised from environmental audits."""

    __tablename__ = "sustainability_corrective_actions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "action_code", name="uq_sustainability_action_code"),
        Index("idx_sustainability_action_status", "tenant_id", "status"),
    )

    requirement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sustainability_compliance_requirements.id", ondelete="CASCADE"), nullable=True
    )
    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False
    )
    action_code: Mapped[str] = mapped_column(String(64), nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    action_plan: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=CorrectiveActionStatus.OPEN.value, nullable=False
    )
    assigned_to_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    linked_work_order_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    requirement: Mapped[EnvironmentalComplianceRequirement | None] = relationship(
        "EnvironmentalComplianceRequirement", back_populates="corrective_actions"
    )


# =============================================================================
# 9. IOT SMART METERS & STREAM INGESTION (WITH DEDUPLICATION)
# =============================================================================

class IoTMeterStream(TenantScopedModel):
    """Registered digital smart meters and telemetry feeds."""

    __tablename__ = "sustainability_iot_meters"
    __table_args__ = (
        UniqueConstraint("tenant_id", "device_id", name="uq_sustainability_iot_device_id"),
        Index("idx_sustainability_iot_meter_status", "tenant_id", "campus_id", "status"),
    )

    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    device_name: Mapped[str] = mapped_column(String(128), nullable=False)
    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False
    )
    building_name: Mapped[str] = mapped_column(String(128), nullable=False)
    meter_type: Mapped[str] = mapped_column(
        String(32), default=ResourceType.ELECTRICITY_GRID.value, nullable=False
    )
    protocol: Mapped[str] = mapped_column(String(32), default="MQTT", nullable=False)
    sampling_interval_secs: Mapped[int] = mapped_column(Integer, default=900, nullable=False)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reading_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 3), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ONLINE", nullable=False)
    api_key_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


class IoTIngestionEvent(TenantScopedModel):
    """Raw / parsed IoT telemetry events with strict cryptographic deduplication."""

    __tablename__ = "sustainability_iot_events"
    __table_args__ = (
        Index("idx_sustainability_iot_dedup", "tenant_id", "dedup_hash", unique=True),
        Index("idx_sustainability_iot_device_time", "tenant_id", "device_id", "event_timestamp"),
    )

    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="kWh", nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    ingestion_status: Mapped[str] = mapped_column(
        String(32), default=IngestionStatus.PROCESSED.value, nullable=False
    )
    dedup_hash: Mapped[str] = mapped_column(String(64), nullable=False)


# =============================================================================
# 10. SUSTAINABILITY BATCH IMPORTS & INVOICE RECONCILIATIONS
# =============================================================================

class SustainabilityImportBatch(TenantScopedModel):
    """Bulk import tracking for utility bills, historical logs, and energy bills."""

    __tablename__ = "sustainability_import_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "batch_number", name="uq_sustainability_import_batch_no"),
    )

    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="ENERGY_INVOICE", nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ImportBatchStatus.PENDING.value, nullable=False
    )
    imported_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    error_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)


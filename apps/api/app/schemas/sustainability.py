"""Pydantic schemas for Campus Sustainability, Energy, Environmental Compliance & Carbon Intelligence (Step 67)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.sustainability import (
    ComplianceCategory,
    ComplianceStatus,
    CorrectiveActionStatus,
    EmissionFactorCategory,
    EmissionScope,
    ImportBatchStatus,
    IngestionStatus,
    InitiativeCategory,
    InitiativeStatus,
    MeasurementSource,
    ResourceType,
    TargetCategory,
    TargetStatus,
    VerificationStatus,
    WasteCategory,
    WasteDisposalMethod,
)

# =============================================================================
# 1. SUSTAINABILITY PROFILE & TARGETS
# =============================================================================

class SustainabilityProfileBase(BaseModel):
    name: str = Field(..., max_length=128)
    code: str = Field(..., max_length=64)
    campus_id: UUID | None = None
    reporting_cycle: str = "ANNUAL"
    baseline_year: int = 2022
    target_net_zero_year: int = 2040
    lead_coordinator_id: UUID | None = None
    coordinator_name: str = "Sustainability Office"
    coordinator_email: str = "sustainability@campus.edu"
    settings: dict[str, Any] | None = None
    is_active: bool = True


class SustainabilityProfileCreate(SustainabilityProfileBase):
    pass


class SustainabilityProfileUpdate(BaseModel):
    name: str | None = None
    reporting_cycle: str | None = None
    baseline_year: int | None = None
    target_net_zero_year: int | None = None
    lead_coordinator_id: UUID | None = None
    coordinator_name: str | None = None
    coordinator_email: str | None = None
    settings: dict[str, Any] | None = None
    is_active: bool | None = None


class SustainabilityProfileResponse(SustainabilityProfileBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SustainabilityTargetBase(BaseModel):
    profile_id: UUID | None = None
    campus_id: UUID | None = None
    category: TargetCategory = TargetCategory.ENERGY_REDUCTION
    target_code: str = Field(..., max_length=64)
    title: str = Field(..., max_length=128)
    description: str | None = None
    baseline_year: int = 2022
    baseline_value: Decimal
    target_year: int = 2030
    target_value: Decimal
    current_value: Decimal = Decimal("0.000")
    unit: str = "kWh"
    reduction_pct_target: Decimal = Decimal("25.00")
    responsible_team: str = "Estate & Facilities"
    deadline: date | None = None


class SustainabilityTargetCreate(SustainabilityTargetBase):
    pass


class SustainabilityTargetUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_value: Decimal | None = None
    current_value: Decimal | None = None
    reduction_pct_target: Decimal | None = None
    reduction_pct_achieved: Decimal | None = None
    status: TargetStatus | None = None
    responsible_team: str | None = None
    deadline: date | None = None


class SustainabilityTargetResponse(SustainabilityTargetBase):
    id: UUID
    tenant_id: UUID
    reduction_pct_achieved: Decimal
    status: TargetStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. EMISSION FACTORS
# =============================================================================

class EmissionFactorBase(BaseModel):
    factor_code: str = Field(..., max_length=64)
    category: EmissionFactorCategory = EmissionFactorCategory.ELECTRICITY_GRID
    scope: EmissionScope = EmissionScope.SCOPE_2
    name: str = Field(..., max_length=128)
    source_authority: str = Field(..., max_length=128)
    factor_version: str = "v2024.1"
    effective_from: date
    effective_to: date | None = None
    factor_value: Decimal
    unit_denominator: str = "kWh"
    gwp_standard: str = "AR5"
    is_active: bool = True
    notes: str | None = None


class EmissionFactorCreate(EmissionFactorBase):
    pass


class EmissionFactorUpdate(BaseModel):
    name: str | None = None
    source_authority: str | None = None
    factor_version: str | None = None
    effective_to: date | None = None
    factor_value: Decimal | None = None
    unit_denominator: str | None = None
    gwp_standard: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class EmissionFactorResponse(EmissionFactorBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. RESOURCE MEASUREMENTS
# =============================================================================

class ResourceMeasurementBase(BaseModel):
    campus_id: UUID
    building_name: str = Field(..., max_length=128)
    meter_code: str = Field(..., max_length=64)
    resource_type: ResourceType = ResourceType.ELECTRICITY_GRID
    period_start: datetime
    period_end: datetime
    reading_value: Decimal
    unit: str = "kWh"
    source_type: MeasurementSource = MeasurementSource.IOT_SENSOR
    baseline_expected_value: Decimal | None = None
    variance_pct: Decimal | None = None
    is_anomaly: bool = False
    anomaly_severity: str | None = None
    anomaly_reason: str | None = None
    linked_work_order_id: UUID | None = None


class ResourceMeasurementCreate(ResourceMeasurementBase):
    pass


class ResourceMeasurementUpdate(BaseModel):
    reading_value: Decimal | None = None
    baseline_expected_value: Decimal | None = None
    variance_pct: Decimal | None = None
    is_anomaly: bool | None = None
    anomaly_severity: str | None = None
    anomaly_reason: str | None = None
    verification_status: VerificationStatus | None = None
    linked_work_order_id: UUID | None = None


class ResourceMeasurementResponse(ResourceMeasurementBase):
    id: UUID
    tenant_id: UUID
    verified_by_id: UUID | None = None
    verification_status: VerificationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. WATER INCIDENTS
# =============================================================================

class WaterIncidentBase(BaseModel):
    campus_id: UUID
    incident_code: str = Field(..., max_length=64)
    incident_type: str = "LEAK_PIPE"
    location: str = Field(..., max_length=128)
    estimated_loss_litres: Decimal = Decimal("0.00")
    severity: str = "MEDIUM"
    status: str = "DETECTED"
    linked_work_order_id: UUID | None = None
    remediation_notes: str | None = None


class WaterIncidentCreate(WaterIncidentBase):
    pass


class WaterIncidentUpdate(BaseModel):
    incident_type: str | None = None
    location: str | None = None
    estimated_loss_litres: Decimal | None = None
    severity: str | None = None
    status: str | None = None
    linked_work_order_id: UUID | None = None
    remediation_notes: str | None = None
    resolved_at: datetime | None = None


class WaterIncidentResponse(WaterIncidentBase):
    id: UUID
    tenant_id: UUID
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. WASTE RECORDS
# =============================================================================

class WasteRecordBase(BaseModel):
    campus_id: UUID
    waste_code: str = Field(..., max_length=64)
    waste_category: WasteCategory = WasteCategory.GENERAL
    is_hazardous: bool = False
    quantity: Decimal
    unit: str = "kg"
    collection_date: date
    disposal_method: WasteDisposalMethod = WasteDisposalMethod.RECYCLING_VENDOR
    partner_name: str = Field(..., max_length=128)
    manifest_number: str | None = None
    certificate_ref: str | None = None
    status: str = "COLLECTED"


class WasteRecordCreate(WasteRecordBase):
    pass


class WasteRecordUpdate(BaseModel):
    quantity: Decimal | None = None
    disposal_method: WasteDisposalMethod | None = None
    partner_name: str | None = None
    manifest_number: str | None = None
    certificate_ref: str | None = None
    status: str | None = None


class WasteRecordResponse(WasteRecordBase):
    id: UUID
    tenant_id: UUID
    verified_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 6. CARBON EMISSIONS ACCOUNTING
# =============================================================================

class CarbonCalculationRequest(BaseModel):
    campus_id: UUID
    reporting_period: str = Field(..., max_length=32)
    scope: EmissionScope = EmissionScope.SCOPE_2
    activity_category: str = Field(..., max_length=64)
    activity_quantity: Decimal
    activity_unit: str = "kWh"
    emission_factor_id: UUID | None = None
    calculation_method: str = "LOCATION_BASED"
    is_estimated: bool = False


class CarbonEmissionsResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    campus_id: UUID
    reporting_period: str
    scope: EmissionScope
    activity_category: str
    activity_quantity: Decimal
    activity_unit: str
    emission_factor_id: UUID | None = None
    factor_value_applied: Decimal
    factor_source_applied: str
    emissions_kg_co2e: Decimal
    emissions_mt_co2e: Decimal
    is_estimated: bool
    calculation_method: str
    audit_hash: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CarbonEmissionsSummary(BaseModel):
    campus_id: UUID
    reporting_period: str
    total_scope_1_mt: Decimal
    total_scope_2_mt: Decimal
    total_scope_3_mt: Decimal
    total_emissions_mt: Decimal
    renewable_offset_mt: Decimal
    net_emissions_mt: Decimal
    breakdown_by_category: dict[str, Decimal]


# =============================================================================
# 7. SUSTAINABILITY INITIATIVES
# =============================================================================

class SustainabilityInitiativeBase(BaseModel):
    campus_id: UUID
    initiative_code: str = Field(..., max_length=64)
    title: str = Field(..., max_length=128)
    description: str
    category: InitiativeCategory = InitiativeCategory.SOLAR_ROOFTOP
    status: InitiativeStatus = InitiativeStatus.PROPOSED
    budget_allocated: Decimal = Decimal("0.00")
    budget_spent: Decimal = Decimal("0.00")
    annual_co2_savings_mt: Decimal = Decimal("0.000")
    annual_energy_savings_kwh: Decimal = Decimal("0.00")
    annual_water_savings_kl: Decimal = Decimal("0.00")
    start_date: date
    completion_date: date | None = None
    responsible_owner_id: UUID | None = None
    lead_department: str = "Estate Operations"


class SustainabilityInitiativeCreate(SustainabilityInitiativeBase):
    pass


class SustainabilityInitiativeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: InitiativeStatus | None = None
    budget_allocated: Decimal | None = None
    budget_spent: Decimal | None = None
    annual_co2_savings_mt: Decimal | None = None
    annual_energy_savings_kwh: Decimal | None = None
    annual_water_savings_kl: Decimal | None = None
    completion_date: date | None = None
    responsible_owner_id: UUID | None = None
    lead_department: str | None = None


class SustainabilityInitiativeResponse(SustainabilityInitiativeBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 8. ENVIRONMENTAL COMPLIANCE & AUDITS
# =============================================================================

class EnvironmentalComplianceRequirementBase(BaseModel):
    campus_id: UUID
    compliance_code: str = Field(..., max_length=64)
    regulation_title: str = Field(..., max_length=255)
    regulatory_body: str = Field(..., max_length=128)
    compliance_category: ComplianceCategory = ComplianceCategory.WATER_CONSENT
    frequency: str = "ANNUAL"
    last_audit_date: date | None = None
    next_renewal_date: date
    status: ComplianceStatus = ComplianceStatus.COMPLIANT
    permit_number: str | None = None
    document_reference: str | None = None


class EnvironmentalComplianceRequirementCreate(EnvironmentalComplianceRequirementBase):
    pass


class EnvironmentalComplianceRequirementUpdate(BaseModel):
    regulation_title: str | None = None
    regulatory_body: str | None = None
    frequency: str | None = None
    last_audit_date: date | None = None
    next_renewal_date: date | None = None
    status: ComplianceStatus | None = None
    permit_number: str | None = None
    document_reference: str | None = None


class EnvironmentalComplianceRequirementResponse(EnvironmentalComplianceRequirementBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnvironmentalCorrectiveActionBase(BaseModel):
    requirement_id: UUID | None = None
    campus_id: UUID
    action_code: str = Field(..., max_length=64)
    issue_description: str
    action_plan: str
    priority: str = "MEDIUM"
    status: CorrectiveActionStatus = CorrectiveActionStatus.OPEN
    assigned_to_id: UUID | None = None
    linked_work_order_id: UUID | None = None
    due_date: date


class EnvironmentalCorrectiveActionCreate(EnvironmentalCorrectiveActionBase):
    pass


class EnvironmentalCorrectiveActionUpdate(BaseModel):
    issue_description: str | None = None
    action_plan: str | None = None
    priority: str | None = None
    status: CorrectiveActionStatus | None = None
    assigned_to_id: UUID | None = None
    linked_work_order_id: UUID | None = None
    due_date: date | None = None
    resolved_at: datetime | None = None


class EnvironmentalCorrectiveActionResponse(EnvironmentalCorrectiveActionBase):
    id: UUID
    tenant_id: UUID
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 9. IOT METERS & EVENT TELEMETRY
# =============================================================================

class IoTMeterStreamBase(BaseModel):
    device_id: str = Field(..., max_length=64)
    device_name: str = Field(..., max_length=128)
    campus_id: UUID
    building_name: str = Field(..., max_length=128)
    meter_type: ResourceType = ResourceType.ELECTRICITY_GRID
    protocol: str = "MQTT"
    sampling_interval_secs: int = 900
    status: str = "ONLINE"


class IoTMeterStreamCreate(IoTMeterStreamBase):
    api_key_plain: str | None = None


class IoTMeterStreamUpdate(BaseModel):
    device_name: str | None = None
    building_name: str | None = None
    meter_type: ResourceType | None = None
    protocol: str | None = None
    sampling_interval_secs: int | None = None
    status: str | None = None


class IoTMeterStreamResponse(IoTMeterStreamBase):
    id: UUID
    tenant_id: UUID
    last_heartbeat: datetime | None = None
    last_reading_value: Decimal | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IoTIngestionEventCreate(BaseModel):
    device_id: str = Field(..., max_length=64)
    event_timestamp: datetime
    metric_name: str = Field(..., max_length=64)
    metric_value: Decimal
    unit: str = "kWh"
    raw_payload: dict[str, Any] | None = None


class IoTIngestionEventResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    device_id: str
    event_timestamp: datetime
    metric_name: str
    metric_value: Decimal
    unit: str
    ingestion_status: IngestionStatus
    dedup_hash: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IoTIngestionBatchPayload(BaseModel):
    device_id: str
    events: list[IoTIngestionEventCreate]


# =============================================================================
# 10. IMPORT BATCHES & ESG SCORECARD DASHBOARD
# =============================================================================

class SustainabilityImportBatchCreate(BaseModel):
    batch_number: str = Field(..., max_length=64)
    file_name: str = Field(..., max_length=255)
    category: str = "ENERGY_INVOICE"
    total_rows: int = 0


class SustainabilityImportBatchResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    batch_number: str
    file_name: str
    category: str
    total_rows: int
    processed_rows: int
    error_count: int
    status: ImportBatchStatus
    imported_by_id: UUID | None = None
    error_summary: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SustainabilityDashboardOverview(BaseModel):
    campus_id: UUID | None = None
    reporting_year: int
    esg_composite_score: Decimal  # out of 100
    energy_intensity_kwh_sqm: Decimal
    renewable_share_pct: Decimal
    water_recycling_rate_pct: Decimal
    waste_diversion_rate_pct: Decimal
    scope_1_mt: Decimal
    scope_2_mt: Decimal
    scope_3_mt: Decimal
    net_emissions_mt: Decimal
    active_anomalies_count: int
    statutory_compliance_rate_pct: Decimal
    pending_corrective_actions: int
    total_initiatives_active: int


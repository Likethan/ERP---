/**
 * CampusOS — Enterprise Campus Sustainability, Energy Management, Environmental Compliance & Carbon Intelligence Types (Step 67)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 */

export type TargetCategory =
  | "ENERGY_REDUCTION"
  | "RENEWABLE_SHARE"
  | "WATER_CONSERVATION"
  | "WASTE_DIVERSION"
  | "SCOPE_1_REDUCTION"
  | "SCOPE_2_REDUCTION"
  | "SCOPE_3_REDUCTION"
  | "NET_ZERO_GHG";

export type TargetStatus =
  | "ON_TRACK"
  | "AT_RISK"
  | "ACHIEVED"
  | "DELAYED"
  | "UNDER_REVIEW";

export type EmissionScope = "SCOPE_1" | "SCOPE_2" | "SCOPE_3";

export type EmissionFactorCategory =
  | "ELECTRICITY_GRID"
  | "DIESEL"
  | "NATURAL_GAS"
  | "PETROL"
  | "WATER_MUNICIPAL"
  | "WASTE_LANDFILL"
  | "WASTE_COMPOSTING"
  | "STUDENT_COMMUTING"
  | "BUSINESS_TRAVEL";

export type ResourceType =
  | "ELECTRICITY_GRID"
  | "SOLAR_GENERATION"
  | "DIESEL_GENSET"
  | "WATER_MUNICIPAL"
  | "WATER_BOREWELL"
  | "WATER_RECYCLED"
  | "RAINWATER_HARVESTED"
  | "NATURAL_GAS";

export type MeasurementSource =
  | "IOT_SENSOR"
  | "UTILITY_BILL"
  | "MANUAL_METER"
  | "SUB_METER"
  | "ESTIMATED";

export type VerificationStatus =
  | "PENDING_REVIEW"
  | "VERIFIED"
  | "FLAGGED"
  | "REJECTED";

export type WasteCategory =
  | "GENERAL"
  | "ORGANIC_COMPOST"
  | "RECYCLABLE_PLASTIC"
  | "RECYCLABLE_PAPER"
  | "RECYCLABLE_METAL"
  | "E_WASTE"
  | "HAZARDOUS_CHEMICAL"
  | "BIO_MEDICAL";

export type WasteDisposalMethod =
  | "COMPOSTING"
  | "RECYCLING_VENDOR"
  | "REGULATED_INCINERATION"
  | "AUTHORIZED_EWASTE_FACILITY"
  | "MUNICIPAL_LANDFILL"
  | "AUTHORIZED_HAZARDOUS_TSDF";

export type InitiativeCategory =
  | "SOLAR_ROOFTOP"
  | "LED_RETROFIT"
  | "RAINWATER_HARVESTING"
  | "COMPOSTING_UNIT"
  | "EV_SHUTTLE"
  | "TREE_PLANTATION"
  | "BEHAVIORAL_AWARENESS"
  | "BIOGAS_PLANT";

export type InitiativeStatus =
  | "PROPOSED"
  | "APPROVED"
  | "IN_EXECUTION"
  | "OPERATIONAL"
  | "COMPLETED"
  | "CANCELLED";

export type ComplianceCategory =
  | "WATER_CONSENT"
  | "AIR_EMISSIONS"
  | "HAZARDOUS_WASTE_AUTHORIZATION"
  | "E_WASTE_EPR"
  | "SOLAR_NET_METERING"
  | "GREEN_BUILDING_IGBC"
  | "GROUNDWATER_EXTRACTION_NOC";

export type ComplianceStatus =
  | "COMPLIANT"
  | "PENDING_INSPECTION"
  | "RENEWAL_DUE"
  | "ACTION_REQUIRED"
  | "OVERDUE";

export type CorrectiveActionStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "RESOLVED"
  | "VERIFIED";

export type IngestionStatus =
  | "PROCESSED"
  | "DUPLICATE_SKIPPED"
  | "REJECTED";

export type ImportBatchStatus =
  | "PENDING"
  | "PROCESSING"
  | "COMPLETED"
  | "FAILED";

// =============================================================================
// DOMAIN ENTITIES
// =============================================================================

export interface SustainabilityProfile {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  campus_id?: string | null;
  reporting_cycle: string;
  baseline_year: number;
  target_net_zero_year: number;
  lead_coordinator_id?: string | null;
  coordinator_name: string;
  coordinator_email: string;
  settings?: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SustainabilityTarget {
  id: string;
  tenant_id: string;
  profile_id?: string | null;
  campus_id?: string | null;
  category: TargetCategory;
  target_code: string;
  title: string;
  description?: string | null;
  baseline_year: number;
  baseline_value: number;
  target_year: number;
  target_value: number;
  current_value: number;
  unit: string;
  reduction_pct_target: number;
  reduction_pct_achieved: number;
  status: TargetStatus;
  responsible_team: string;
  deadline?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmissionFactor {
  id: string;
  tenant_id: string;
  factor_code: string;
  category: EmissionFactorCategory;
  scope: EmissionScope;
  name: string;
  source_authority: string;
  factor_version: string;
  effective_from: string;
  effective_to?: string | null;
  factor_value: number;
  unit_denominator: string;
  gwp_standard: string;
  is_active: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResourceMeasurement {
  id: string;
  tenant_id: string;
  campus_id: string;
  building_name: string;
  meter_code: string;
  resource_type: ResourceType;
  period_start: string;
  period_end: string;
  reading_value: number;
  unit: string;
  source_type: MeasurementSource;
  baseline_expected_value?: number | null;
  variance_pct?: number | null;
  is_anomaly: boolean;
  anomaly_severity?: "NORMAL" | "WARNING" | "CRITICAL" | null;
  anomaly_reason?: string | null;
  verified_by_id?: string | null;
  verification_status: VerificationStatus;
  linked_work_order_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WaterIncidentRecord {
  id: string;
  tenant_id: string;
  campus_id: string;
  incident_code: string;
  incident_type: string;
  location: string;
  estimated_loss_litres: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "DETECTED" | "INVESTIGATING" | "WORK_ORDER_CREATED" | "REPAIRED" | "CLOSED";
  linked_work_order_id?: string | null;
  remediation_notes?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WasteRecord {
  id: string;
  tenant_id: string;
  campus_id: string;
  waste_code: string;
  waste_category: WasteCategory;
  is_hazardous: boolean;
  quantity: number;
  unit: string;
  collection_date: string;
  disposal_method: WasteDisposalMethod;
  partner_name: string;
  manifest_number?: string | null;
  certificate_ref?: string | null;
  verified_by_id?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CarbonEmissionsCalculation {
  id: string;
  tenant_id: string;
  campus_id: string;
  reporting_period: string;
  scope: EmissionScope;
  activity_category: string;
  activity_quantity: number;
  activity_unit: string;
  emission_factor_id?: string | null;
  factor_value_applied: number;
  factor_source_applied: string;
  emissions_kg_co2e: number;
  emissions_mt_co2e: number;
  is_estimated: boolean;
  calculation_method: string;
  audit_hash?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CarbonEmissionsSummary {
  campus_id: string;
  reporting_period: string;
  total_scope_1_mt: number;
  total_scope_2_mt: number;
  total_scope_3_mt: number;
  total_emissions_mt: number;
  renewable_offset_mt: number;
  net_emissions_mt: number;
  breakdown_by_category: Record<string, number>;
}

export interface SustainabilityInitiative {
  id: string;
  tenant_id: string;
  campus_id: string;
  initiative_code: string;
  title: string;
  description: string;
  category: InitiativeCategory;
  status: InitiativeStatus;
  budget_allocated: number;
  budget_spent: number;
  annual_co2_savings_mt: number;
  annual_energy_savings_kwh: number;
  annual_water_savings_kl: number;
  start_date: string;
  completion_date?: string | null;
  responsible_owner_id?: string | null;
  lead_department: string;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentalComplianceRequirement {
  id: string;
  tenant_id: string;
  campus_id: string;
  compliance_code: string;
  regulation_title: string;
  regulatory_body: string;
  compliance_category: ComplianceCategory;
  frequency: string;
  last_audit_date?: string | null;
  next_renewal_date: string;
  status: ComplianceStatus;
  permit_number?: string | null;
  document_reference?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentalCorrectiveAction {
  id: string;
  tenant_id: string;
  requirement_id?: string | null;
  campus_id: string;
  action_code: string;
  issue_description: string;
  action_plan: string;
  priority: string;
  status: CorrectiveActionStatus;
  assigned_to_id?: string | null;
  linked_work_order_id?: string | null;
  due_date: string;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IoTMeterStream {
  id: string;
  tenant_id: string;
  device_id: string;
  device_name: string;
  campus_id: string;
  building_name: string;
  meter_type: ResourceType;
  protocol: string;
  sampling_interval_secs: number;
  last_heartbeat?: string | null;
  last_reading_value?: number | null;
  status: "ONLINE" | "WARNING" | "OFFLINE";
  created_at: string;
  updated_at: string;
}

export interface IoTIngestionEvent {
  id: string;
  tenant_id: string;
  device_id: string;
  event_timestamp: string;
  metric_name: string;
  metric_value: number;
  unit: string;
  raw_payload?: Record<string, unknown> | null;
  ingestion_status: IngestionStatus;
  dedup_hash: string;
  created_at: string;
}

export interface SustainabilityImportBatch {
  id: string;
  tenant_id: string;
  batch_number: string;
  file_name: string;
  category: string;
  total_rows: number;
  processed_rows: number;
  error_count: number;
  status: ImportBatchStatus;
  imported_by_id?: string | null;
  error_summary?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface SustainabilityDashboardOverview {
  campus_id?: string | null;
  reporting_year: number;
  esg_composite_score: number;
  energy_intensity_kwh_sqm: number;
  renewable_share_pct: number;
  water_recycling_rate_pct: number;
  waste_diversion_rate_pct: number;
  scope_1_mt: number;
  scope_2_mt: number;
  scope_3_mt: number;
  net_emissions_mt: number;
  active_anomalies_count: number;
  statutory_compliance_rate_pct: number;
  pending_corrective_actions: number;
  total_initiatives_active: number;
}

// =============================================================================
// INPUT TYPES
// =============================================================================

export interface ProfileCreateInput {
  name: string;
  code: string;
  campus_id?: string;
  reporting_cycle?: string;
  baseline_year?: number;
  target_net_zero_year?: number;
  coordinator_name: string;
  coordinator_email: string;
}

export interface TargetCreateInput {
  campus_id?: string;
  category: TargetCategory;
  target_code: string;
  title: string;
  description?: string;
  baseline_year: number;
  baseline_value: number;
  target_year: number;
  target_value: number;
  current_value?: number;
  unit: string;
  reduction_pct_target: number;
  responsible_team: string;
  deadline?: string;
}

export interface MeasurementCreateInput {
  campus_id: string;
  building_name: string;
  meter_code: string;
  resource_type: ResourceType;
  period_start: string;
  period_end: string;
  reading_value: number;
  unit: string;
  source_type: MeasurementSource;
  baseline_expected_value?: number;
  is_anomaly?: boolean;
}

export interface WaterIncidentCreateInput {
  campus_id: string;
  incident_code: string;
  incident_type: string;
  location: string;
  estimated_loss_litres: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status?: "DETECTED" | "INVESTIGATING" | "WORK_ORDER_CREATED" | "REPAIRED" | "CLOSED";
  remediation_notes?: string;
}

export interface WasteRecordCreateInput {
  campus_id: string;
  waste_code: string;
  waste_category: WasteCategory;
  is_hazardous: boolean;
  quantity: number;
  unit: string;
  collection_date: string;
  disposal_method: WasteDisposalMethod;
  partner_name: string;
  manifest_number?: string;
  certificate_ref?: string;
}

export interface CarbonCalculationInput {
  campus_id: string;
  reporting_period: string;
  scope: EmissionScope;
  activity_category: string;
  activity_quantity: number;
  activity_unit: string;
  emission_factor_id?: string;
  calculation_method?: string;
}

export interface InitiativeCreateInput {
  campus_id: string;
  initiative_code: string;
  title: string;
  description: string;
  category: InitiativeCategory;
  status: InitiativeStatus;
  budget_allocated: number;
  budget_spent: number;
  annual_co2_savings_mt: number;
  annual_energy_savings_kwh: number;
  annual_water_savings_kl: number;
  start_date: string;
  completion_date?: string;
  lead_department: string;
}

export interface ComplianceRequirementCreateInput {
  campus_id: string;
  compliance_code: string;
  regulation_title: string;
  regulatory_body: string;
  compliance_category: ComplianceCategory;
  frequency: string;
  next_renewal_date: string;
  status: ComplianceStatus;
  permit_number?: string;
}

export interface CorrectiveActionCreateInput {
  requirement_id?: string;
  campus_id: string;
  action_code: string;
  issue_description: string;
  action_plan: string;
  priority: string;
  status: CorrectiveActionStatus;
  due_date: string;
}

export interface IoTMeterCreateInput {
  device_id: string;
  device_name: string;
  campus_id: string;
  building_name: string;
  meter_type: ResourceType;
  protocol?: string;
  sampling_interval_secs?: number;
}

export interface TelemetryIngestInput {
  device_id: string;
  event_timestamp: string;
  metric_name: string;
  metric_value: number;
  unit: string;
  raw_payload?: Record<string, unknown>;
}


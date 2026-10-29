/**
 * CampusOS — Enterprise Legal Affairs, Contract Lifecycle, Policy Compliance & Institutional Risk Management Types (Step 62)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 */

export type ContractCategory =
  | "VENDOR_PROCUREMENT"
  | "EMPLOYMENT_CONSULTING"
  | "SERVICE_LEVEL"
  | "STUDENT_SERVICE"
  | "RESEARCH_SPONSORED"
  | "INDUSTRY_COLLABORATION"
  | "DATA_PROCESSING_NDA"
  | "FACILITY_PARTNERSHIP"
  | "INTERNATIONAL_INSTITUTIONAL"
  | "OTHER";

export type ContractStatus =
  | "DRAFT"
  | "INTERNAL_REVIEW"
  | "DEPARTMENT_APPROVAL"
  | "LEGAL_REVIEW"
  | "AUTHORIZED_APPROVAL"
  | "READY_FOR_EXECUTION"
  | "EXECUTED"
  | "ACTIVE"
  | "EXPIRING"
  | "RENEWED"
  | "TERMINATED"
  | "EXPIRED"
  | "REJECTED"
  | "WITHDRAWN"
  | "ON_HOLD"
  | "ARCHIVED";

export type ConfidentialityLevel =
  | "PUBLIC"
  | "INTERNAL"
  | "CONFIDENTIAL"
  | "RESTRICTED_LEGAL";

export type ObligationType =
  | "DELIVERABLE"
  | "REPORTING"
  | "PAYMENT_MILESTONE"
  | "SERVICE_COMMITMENT"
  | "RENEWAL_NOTICE"
  | "INSURANCE_CERTIFICATE"
  | "COMPLIANCE_AUDIT"
  | "OTHER";

export type ObligationStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "UNDER_REVIEW"
  | "APPROACHING"
  | "COMPLETED"
  | "OVERDUE"
  | "WAIVED"
  | "DISPUTED";

export type MatterCategory =
  | "CONTRACT_DISPUTE"
  | "VENDOR_DISPUTE"
  | "EMPLOYMENT_DISPUTE"
  | "INSTITUTIONAL_CLAIM"
  | "REGULATORY_INQUIRY"
  | "EXTERNAL_COUNSEL_ENGAGEMENT"
  | "LITIGATION_PROCEEDING"
  | "LEGAL_OPINION"
  | "PRE_LITIGATION_CORRESPONDENCE"
  | "OTHER";

export type MatterRestrictedClassification =
  | "STRICTLY_CONFIDENTIAL"
  | "ATTORNEY_CLIENT_PRIVILEGED"
  | "RESTRICTED_EXECUTIVE"
  | "LEGAL_INTERNAL";

export type MatterStatus =
  | "OPEN"
  | "UNDER_REVIEW"
  | "ACTIVE_PROCEEDING"
  | "SETTLEMENT_PENDING"
  | "CLOSED_RESOLVED"
  | "CLOSED_DISMISSED"
  | "ON_HOLD";

export type MatterPriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type ComplianceCategory =
  | "STATUTORY_REGULATORY"
  | "ACCREDITATION_STANDARD"
  | "DATA_PRIVACY_SECURITY"
  | "LABOR_EMPLOYMENT"
  | "FINANCIAL_TAX"
  | "HEALTH_SAFETY_ENVIRONMENT"
  | "RESEARCH_ETHICS"
  | "INSTITUTIONAL_BYLAW";

export type ComplianceAssessmentStatus =
  | "NOT_ASSESSED"
  | "IN_PROGRESS"
  | "EVIDENCE_REQUIRED"
  | "UNDER_REVIEW"
  | "COMPLIANT"
  | "PARTIALLY_COMPLIANT"
  | "NON_COMPLIANT"
  | "REMEDIATION_IN_PROGRESS"
  | "CLOSED";

export type RiskCategory =
  | "GOVERNANCE_LEGAL"
  | "FINANCIAL"
  | "OPERATIONAL"
  | "REPUTATIONAL"
  | "ACADEMIC_ACCREDITATION"
  | "INFORMATION_SECURITY_PRIVACY"
  | "HEALTH_SAFETY_ENVIRONMENTAL"
  | "STRATEGIC_PARTNERSHIP";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type RiskStatus =
  | "IDENTIFIED"
  | "ASSESSED"
  | "MITIGATION_IN_PROGRESS"
  | "RESIDUAL_RISK_ACCEPTED"
  | "RESIDUAL_ACCEPTED"
  | "RETIRED_RESOLVED"
  | "MONITORED"
  | "CLOSED";

export type ExecutionMethod =
  | "EXTERNAL_DIGITAL_SUITE_CONFIRMED"
  | "WET_SIGNATURE_CONFIRMED"
  | "BOARD_RESOLUTION_CONFIRMED"
  | "HYBRID_CONFIRMED"
  | string;

export type LegalMatterCategory = MatterCategory;
export type LegalMatterPriority = MatterPriority;
export type LegalMatterStatus = MatterStatus;
export type ObligationCategory = ObligationType;
export type ComplianceStatus = ComplianceAssessmentStatus;

// =============================================================================
// ENTITY MODELS
// =============================================================================

export interface ContractAmendment {
  id: string;
  tenant_id: string;
  contract_id: string;
  amendment_number: number;
  title: string;
  summary?: string | null;
  description?: string | null;
  effective_date: string;
  extended_expiration_date?: string | null;
  financial_value_adjustment: number;
  financial_value_delta?: number | null;
  document_id?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ContractObligation {
  id: string;
  tenant_id: string;
  contract_id: string;
  obligation_code: string;
  title: string;
  description?: string | null;
  obligation_type: ObligationType;
  category?: ObligationType;
  responsible_owner_id?: string | null;
  accountable_department_id?: string | null;
  due_date: string;
  review_date?: string | null;
  reminder_lead_days: number;
  status: ObligationStatus;
  evidence_document_id?: string | null;
  required_evidence?: string | null;
  completion_notes?: string | null;
  completed_by_id?: string | null;
  completed_at?: string | null;
  waived_by_id?: string | null;
  waived_at?: string | null;
  waived_reason?: string | null;
  waiver_rationale?: string | null;
  escalation_level: number;
  created_at: string;
  updated_at: string;
}

export interface InstitutionalContract {
  id: string;
  tenant_id: string;
  contract_number: string;
  title: string;
  category: ContractCategory;
  purpose?: string | null;
  internal_owner_id: string;
  department_id?: string | null;
  campus_id?: string | null;
  counterparty_name: string;
  counterparty_contact_json?: Record<string, any> | null;
  related_entity_type?: string | null;
  related_entity_id?: string | null;
  status: ContractStatus;
  effective_date?: string | null;
  expiration_date?: string | null;
  auto_renew: boolean;
  renewal_notice_days: number;
  termination_notice_days: number;
  financial_value?: number | null;
  currency: string;
  confidentiality_level: ConfidentialityLevel;
  draft_document_id?: string | null;
  executed_document_id?: string | null;
  execution_method?: string | null;
  executed_at?: string | null;
  executed_by_id?: string | null;
  governing_law?: string | null;
  approval_chain_json?: Array<{
    step: string;
    role?: string;
    previous_status?: string;
    new_status?: string;
    reviewer_id?: string;
    reviewer_name?: string;
    comments?: string;
    decided_at?: string;
    execution_method?: string;
  }> | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  amendments: ContractAmendment[];
  obligations: ContractObligation[];
}

export interface InstitutionalLegalMatter {
  id: string;
  tenant_id: string;
  matter_number: string;
  title: string;
  category: MatterCategory;
  restricted_classification: MatterRestrictedClassification;
  internal_owner_id: string;
  lead_counsel_user_id?: string | null;
  external_counsel_ref?: string | null;
  counterparty_name?: string | null;
  opposing_counsel_name?: string | null;
  related_contract_id?: string | null;
  related_department_id?: string | null;
  campus_id?: string | null;
  status: MatterStatus;
  priority: MatterPriority;
  financial_exposure_estimate?: number | null;
  settlement_amount?: number | null;
  opened_date: string;
  target_resolution_date?: string | null;
  closed_date?: string | null;
  key_deadlines_json?: Array<{
    title: string;
    due_date: string;
    status: string;
    notes?: string;
  }> | null;
  associated_documents_json?: Array<{
    doc_id: string;
    title: string;
    category?: string;
  }> | null;
  opposing_party_name?: string | null;
  outside_counsel_json?: Record<string, any> | null;
  description?: string | null;
  confidential_notes?: string | null;
  resolution_summary?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InstitutionalComplianceObligation {
  id: string;
  tenant_id: string;
  obligation_code: string;
  name: string;
  description?: string | null;
  authoritative_source_reference: string;
  source_reference?: string;
  governing_authority?: string;
  title?: string;
  category: ComplianceCategory;
  responsible_owner_id?: string | null;
  department_id?: string | null;
  campus_id?: string | null;
  review_frequency_months: number;
  due_date: string;
  next_review_due?: string | null;
  next_review_date?: string | null;
  required_controls?: string | null;
  required_evidence_reference?: string | null;
  status: ComplianceAssessmentStatus;
  assessment_findings?: string | null;
  review_findings?: string | null;
  corrective_action_plan?: Record<string, any> | null;
  assessed_by_id?: string | null;
  assessed_at?: string | null;
  related_policy_id?: string | null;
  related_contract_id?: string | null;
  evidence_records_json?: Array<{
    type?: string;
    verified?: boolean;
    doc_id?: string;
    notes?: string;
  }> | null;
  corrective_actions_json?: Array<{
    id?: string;
    action?: string;
    owner_id?: string;
    deadline?: string;
    status?: string;
  }> | null;
  created_at: string;
  updated_at: string;
}

export interface InstitutionalRisk {
  id: string;
  tenant_id: string;
  risk_code: string;
  risk_identifier?: string;
  title: string;
  description?: string | null;
  category: RiskCategory;
  department_id?: string | null;
  campus_id?: string | null;
  responsible_owner_id?: string | null;
  inherent_likelihood: number;
  inherent_impact: number;
  inherent_score: number;
  inherent_level?: RiskLevel;
  existing_controls?: string | null;
  residual_likelihood: number;
  residual_impact: number;
  residual_score: number;
  residual_level?: RiskLevel;
  risk_level: RiskLevel;
  mitigation_plan?: string | null;
  target_completion_date?: string | null;
  status: RiskStatus;
  accepted_by_id?: string | null;
  acceptance_rationale?: string | null;
  related_contract_id?: string | null;
  related_policy_id?: string | null;
  related_compliance_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LegalOperationsDashboard {
  contracts_pending_review_count: number;
  contracts_expiring_soon_count: number;
  obligations_overdue_count: number;
  policies_pending_review_count: number;
  open_legal_matters_count: number;
  compliance_actions_outstanding_count: number;
  high_priority_risks_count: number;
  recent_contracts: InstitutionalContract[];
  expiring_contracts: InstitutionalContract[];
  overdue_obligations: ContractObligation[];
  critical_matters: InstitutionalLegalMatter[];
  critical_risks: InstitutionalRisk[];
}

export interface RenewalSweepResult {
  contracts_evaluated?: number;
  contracts_flagged_expiring: number;
  contracts_auto_expired?: number;
  obligations_flagged_overdue: number;
  compliance_reviews_flagged: number;
  notifications_dispatched: number;
}

// =============================================================================
// INPUT DTOs
// =============================================================================

export interface ContractCreateInput {
  contract_number?: string;
  title: string;
  category: ContractCategory;
  purpose?: string;
  internal_owner_id: string;
  department_id?: string;
  campus_id?: string;
  counterparty_name: string;
  counterparty_contact_json?: Record<string, any>;
  related_entity_type?: string;
  related_entity_id?: string;
  effective_date?: string;
  expiration_date?: string;
  auto_renew?: boolean;
  renewal_notice_days?: number;
  termination_notice_days?: number;
  financial_value?: number;
  currency?: string;
  confidentiality_level?: ConfidentialityLevel;
  draft_document_id?: string;
  governing_law?: string;
  metadata_json?: Record<string, any>;
}

export interface ContractUpdateInput {
  title?: string;
  category?: ContractCategory;
  purpose?: string;
  internal_owner_id?: string;
  department_id?: string;
  campus_id?: string;
  counterparty_name?: string;
  counterparty_contact_json?: Record<string, any>;
  effective_date?: string;
  expiration_date?: string;
  auto_renew?: boolean;
  renewal_notice_days?: number;
  termination_notice_days?: number;
  financial_value?: number;
  currency?: string;
  confidentiality_level?: ConfidentialityLevel;
  draft_document_id?: string;
  governing_law?: string;
  metadata_json?: Record<string, any>;
}

export interface ContractTransitionInput {
  target_status?: ContractStatus;
  to_status?: ContractStatus;
  comment?: string;
  comments?: string;
  reviewer_name?: string;
}

export interface ContractExecutionConfirmInput {
  execution_method: string;
  executed_at?: string;
  executed_document_id?: string;
  signatory_name?: string;
  signatory_title?: string;
  counterparty_signatory?: string;
  counterparty_signed_date?: string;
  certificate_reference?: string;
  notes?: string;
}

export interface ContractAmendmentCreateInput {
  title?: string;
  summary?: string;
  amendment_number?: number;
  description?: string;
  effective_date: string;
  extended_expiration_date?: string;
  financial_value_adjustment?: number;
  financial_value_delta?: number;
  document_id?: string;
}

export interface ContractObligationCreateInput {
  contract_id: string;
  obligation_code?: string;
  title: string;
  description?: string;
  obligation_type?: ObligationType;
  category?: ObligationType;
  required_evidence?: string;
  responsible_owner_id?: string;
  accountable_department_id?: string;
  due_date: string;
  review_date?: string;
  reminder_lead_days?: number;
}

export interface ObligationCompleteInput {
  evidence_document_id?: string;
  completion_evidence_ref?: string;
  completion_notes?: string;
}

export interface ObligationWaiveInput {
  waived_reason?: string;
  waiver_rationale?: string;
  authorized_by?: string;
}

export interface MatterCreateInput {
  matter_number?: string;
  title: string;
  category: MatterCategory;
  restricted_classification?: MatterRestrictedClassification;
  internal_owner_id?: string;
  lead_counsel_user_id?: string;
  external_counsel_ref?: string;
  counterparty_name?: string;
  opposing_party_name?: string;
  opposing_counsel_name?: string;
  outside_counsel_json?: Record<string, any>;
  description?: string;
  related_contract_id?: string;
  related_department_id?: string;
  campus_id?: string;
  priority?: MatterPriority;
  financial_exposure_estimate?: number;
  opened_date?: string;
  target_resolution_date?: string;
  confidential_notes?: string;
}

export interface MatterUpdateInput {
  title?: string;
  category?: MatterCategory;
  restricted_classification?: MatterRestrictedClassification;
  internal_owner_id?: string;
  lead_counsel_user_id?: string;
  external_counsel_ref?: string;
  counterparty_name?: string;
  opposing_party_name?: string;
  opposing_counsel_name?: string;
  outside_counsel_json?: Record<string, any>;
  description?: string;
  status?: MatterStatus;
  priority?: MatterPriority;
  financial_exposure_estimate?: number;
  settlement_amount?: number;
  target_resolution_date?: string;
  closed_date?: string;
  confidential_notes?: string;
  resolution_summary?: string;
}

export interface ComplianceCreateInput {
  obligation_code?: string;
  name?: string;
  title?: string;
  description?: string;
  authoritative_source_reference?: string;
  source_reference?: string;
  governing_authority?: string;
  category?: ComplianceCategory;
  responsible_owner_id?: string;
  department_id?: string;
  campus_id?: string;
  review_frequency_months?: number;
  review_frequency?: string;
  due_date?: string;
  next_review_due?: string;
  next_review_date?: string;
  required_controls?: string;
  related_policy_id?: string;
  related_contract_id?: string;
}

export interface ComplianceAssessInput {
  status: ComplianceAssessmentStatus;
  assessment_findings?: string;
  findings_summary?: string;
  evidence_records_json?: Array<Record<string, any>>;
  evidence_reference?: string;
  corrective_actions_json?: Array<Record<string, any>>;
  corrective_action_plan?: Record<string, any>;
  next_review_date?: string;
}

export interface RiskCreateInput {
  risk_code?: string;
  title: string;
  description?: string;
  category?: RiskCategory;
  department_id?: string;
  campus_id?: string;
  responsible_owner_id?: string;
  inherent_likelihood?: number;
  inherent_impact?: number;
  existing_controls?: string;
  residual_likelihood?: number;
  residual_impact?: number;
  mitigation_plan?: string;
  target_completion_date?: string;
  target_resolution_date?: string;
  related_contract_id?: string;
  related_policy_id?: string;
  related_compliance_id?: string;
}

export interface RiskUpdateInput {
  title?: string;
  description?: string;
  category?: RiskCategory;
  department_id?: string;
  campus_id?: string;
  responsible_owner_id?: string;
  inherent_likelihood?: number;
  inherent_impact?: number;
  existing_controls?: string;
  residual_likelihood?: number;
  residual_impact?: number;
  mitigation_plan?: string;
  target_completion_date?: string;
  status?: RiskStatus;
}

export interface RiskAcceptInput {
  acceptance_rationale?: string;
  accepted_by?: string;
  rationale?: string;
}

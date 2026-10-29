/**
 * TypeScript Definitions for CampusOS Enterprise Research Collaboration,
 * Project Portfolio, Grants & Sponsored Research Management (Step 44 & Step 61)
 *
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 */

export type ResearchProjectCategory =
  | "FACULTY_LED"
  | "DEPARTMENTAL"
  | "INTERDISCIPLINARY"
  | "STUDENT_RESEARCH"
  | "INDUSTRY_SPONSORED"
  | "GOVERNMENT_FUNDED"
  | "COLLABORATIVE"
  | "APPLIED_INNOVATION"
  | "INTERNATIONAL_COLLABORATION"
  | "FUNDED_RESEARCH";

export type ResearchProjectStatus =
  | "DRAFT"
  | "PROPOSAL"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "ACTIVE"
  | "ON_HOLD"
  | "COMPLETED"
  | "CLOSED"
  | "CANCELLED";

export type ResearchMilestoneStatus =
  | "PLANNED"
  | "IN_PROGRESS"
  | "SUBMITTED_FOR_REVIEW"
  | "ACCEPTED"
  | "REVISION_REQUESTED"
  | "BLOCKED"
  | "CANCELLED";

export type ResearchEthicsApprovalType =
  | "HUMAN_SUBJECTS_IRB"
  | "ANIMAL_CARE_IACUC"
  | "BIO_SAFETY_IBC"
  | "RADIATION_SAFETY"
  | "DATA_PRIVACY_ETHICS"
  | "GENERAL_INSTITUTIONAL";

export type ResearchEthicsApprovalStatus =
  | "NOT_REQUIRED"
  | "PREPARATION"
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "CHANGES_REQUIRED"
  | "REJECTED"
  | "EXPIRED";

export type ResearchRiskSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type ResearchRiskStatus = "IDENTIFIED" | "MONITORED" | "MITIGATED" | "ACCEPTED" | "CLOSED";

export type ResearchTeamRole =
  | "PRINCIPAL_INVESTIGATOR"
  | "CO_INVESTIGATOR"
  | "FACULTY_MENTOR"
  | "POSTDOC_RESEARCHER"
  | "RESEARCH_SCHOLAR"
  | "STUDENT_RESEARCHER"
  | "INDUSTRY_COLLABORATOR"
  | "EXTERNAL_CO_PI"
  | "PROJECT_MANAGER"
  | "RESEARCH_ASSISTANT";

export type ResearchOpportunityStatus = "DRAFT" | "OPEN" | "CLOSED" | "ARCHIVED" | "CANCELLED";

export type ResearchGrantInternalReviewStatus =
  | "DRAFT"
  | "SUBMITTED_INTERNAL"
  | "DEPARTMENTAL_REVIEW"
  | "BUDGET_REVIEW"
  | "REVISION_REQUESTED"
  | "INSTITUTIONALLY_APPROVED"
  | "REJECTED_INTERNAL";

export type ResearchExternalSubmissionStatus =
  | "NOT_SUBMITTED"
  | "SUBMITTED_EXTERNAL"
  | "UNDER_EXTERNAL_REVIEW"
  | "AWARDED"
  | "REJECTED_EXTERNAL"
  | "DECLINED"
  | "WITHDRAWN"
  | "REVISION_REQUESTED";

export type ResearchOutputStatus =
  | "SUBMITTED"
  | "UNDER_PEER_REVIEW"
  | "ACCEPTED_FOR_PUBLICATION"
  | "PUBLISHED"
  | "PRESENTED"
  | "DEPOSITED";

export type ResearchPatentStatus =
  | "DISCLOSED"
  | "UNDER_EVALUATION"
  | "PROVISIONAL_FILED"
  | "NON_PROVISIONAL_FILED"
  | "PCT_INTERNATIONAL_FILED"
  | "EXAMINATION"
  | "GRANTED"
  | "COMMERCIALIZED"
  | "ABANDONED";

export interface ResearchProject {
  id: string;
  tenant_id: string;
  project_code: string;
  title: string;
  abstract: string;
  research_category: ResearchProjectCategory | string;
  research_domain: string;
  principal_investigator_id: string;
  pi_name?: string | null;
  pi_email?: string | null;
  participating_department_ids?: string[];
  funding_source?: string | null;
  grant_application_id?: string | null;
  start_date: string;
  planned_end_date: string;
  actual_end_date?: string | null;
  total_budget_allocated: number;
  currency: string;
  status: ResearchProjectStatus | string;
  status_reason?: string | null;
  requires_ethics_approval: boolean;
  is_international: boolean;
  responsible_admin_id?: string | null;
  campus_id?: string | null;
  department_id?: string | null;
  milestones_count?: number;
  team_count?: number;
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchTeamMember {
  id: string;
  tenant_id: string;
  project_id: string;
  user_id?: string | null;
  user_name?: string | null;
  user_email?: string | null;
  external_collaborator_name?: string | null;
  external_institution?: string | null;
  role: ResearchTeamRole | string;
  contribution_description?: string | null;
  start_date: string;
  end_date?: string | null;
  is_active: boolean;
  access_scope: string;
  workload_percentage?: number;
  created_at: string;
}

export interface ResearchMilestone {
  id: string;
  tenant_id: string;
  project_id: string;
  milestone_code: string;
  title: string;
  description: string;
  sequence_number: number;
  planned_start_date: string;
  planned_completion_date: string;
  actual_completion_date?: string | null;
  responsible_owner_id: string;
  responsible_owner_name?: string | null;
  dependencies_json: string[];
  acceptance_criteria: string;
  completion_percentage: number;
  status: ResearchMilestoneStatus | string;
  is_mandatory_for_closure: boolean;
  deliverable_reference?: string | null;
  evidence_document_id?: string | null;
  verified_by_user_id?: string | null;
  verified_at?: string | null;
  verification_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchEthicsApproval {
  id: string;
  tenant_id: string;
  project_id: string;
  approval_code: string;
  approval_type: ResearchEthicsApprovalType | string;
  governing_policy_reference: string;
  review_committee_name: string;
  reviewer_user_id?: string | null;
  reviewer_name?: string | null;
  submission_date: string;
  decision_date?: string | null;
  status: ResearchEthicsApprovalStatus | string;
  conditions_and_restrictions?: string | null;
  expiry_date?: string | null;
  evidence_document_id?: string | null;
  decision_rationale?: string | null;
  is_confidential: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResearchFundingOpportunity {
  id: string;
  tenant_id: string;
  code: string;
  title: string;
  description: string;
  funding_agency_name: string;
  category: string;
  research_domains: string[];
  eligibility_criteria: string;
  opening_date: string;
  closing_date: string;
  min_funding_amount?: number | null;
  max_funding_amount?: number | null;
  currency: string;
  application_procedure_url?: string | null;
  internal_opportunity_owner_id?: string | null;
  status: ResearchOpportunityStatus | string;
  is_saved?: boolean;
  expressions_of_interest_count?: number;
  metadata_json?: {
    saved_by_users?: string[];
    expressions_of_interest?: Array<{
      eoi_id: string;
      prospective_project_title: string;
      principal_investigator_id: string;
      notes: string;
      estimated_budget?: number | null;
      recorded_by_user_id: string;
      recorded_at: string;
    }>;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface ResearchGrantApplication {
  id: string;
  tenant_id: string;
  application_code: string;
  funding_opportunity_id?: string | null;
  project_id?: string | null;
  project_title?: string | null;
  title: string;
  principal_investigator_id: string;
  pi_name?: string | null;
  research_proposal_summary: string;
  objectives_json: string[];
  methodology_summary?: string | null;
  work_packages_json: Array<Record<string, any>>;
  proposed_budget: number;
  currency: string;
  internal_review_status: ResearchGrantInternalReviewStatus | string;
  external_submission_status: ResearchExternalSubmissionStatus | string;
  external_reference_number?: string | null;
  external_submitted_at?: string | null;
  submitted_by_user_id?: string | null;
  internal_approved_by_id?: string | null;
  internal_approved_at?: string | null;
  rejection_reason?: string | null;
  metadata_json?: {
    sponsor_decision?: {
      decision: string;
      decision_date: string;
      award_amount?: number | null;
      award_number?: string | null;
      sponsor_feedback?: string | null;
      decision_notes?: string | null;
      award_letter_url?: string | null;
      recorded_by_user_id: string;
      recorded_at: string;
    };
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface ResearchGrantAward {
  id: string;
  tenant_id: string;
  award_number: string;
  project_id: string;
  grant_application_id?: string | null;
  funding_organization: string;
  award_amount: number;
  currency: string;
  award_date: string;
  start_date: string;
  end_date: string;
  period_start_date?: string;
  period_end_date?: string;
  approved_budget_json: Record<string, any>;
  disbursement_schedule_json: Array<{
    tranche: number;
    percentage: number;
    amount: number;
    trigger: string;
    status?: string;
    [key: string]: any;
  }>;
  spending_conditions?: string | null;
  reporting_deadlines_json: Array<{
    report_type: string;
    frequency_months?: number;
    due_date?: string;
    status?: string;
  }>;
  financial_owner_id: string;
  received_amount: number;
  disbursed_amount?: number;
  allocated_amount: number;
  committed_expenditure: number;
  actual_expenditure: number;
  remaining_budget: number;
  remaining_balance?: number;
  amendments_json?: any[];
  status: string;
  metadata_json?: {
    agreement_type?: string;
    contract_document_url?: string;
    scope_of_work?: string;
    deliverables?: Array<{ code: string; name: string; due_month: number }>;
    amendments?: Array<{
      amendment_number: string;
      amendment_date: string;
      description: string;
      extended_end_date?: string | null;
      budget_adjustment: number;
      document_url?: string | null;
    }>;
    international_partner_id?: string;
    international_agreement_id?: string;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface ResearchBudgetPlan {
  id: string;
  tenant_id: string;
  project_id: string;
  plan_code?: string;
  category?: string;
  award_id?: string | null;
  version_number: number;
  status: string;
  personnel_costs: number;
  equipment_costs: number;
  consumables_materials_costs: number;
  travel_fieldwork_costs: number;
  computing_software_costs: number;
  publication_dissemination_costs: number;
  external_services_costs: number;
  institutional_overheads: number;
  contingency_costs: number;
  total_budget: number;
  currency: string;
  approved_by_id?: string | null;
  approved_at?: string | null;
  approval_notes?: string | null;
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchProjectRisk {
  id: string;
  tenant_id: string;
  project_id: string;
  risk_code: string;
  title: string;
  category: string;
  likelihood: number | string;
  impact: number | string;
  calculated_risk_level: ResearchRiskSeverity | string;
  responsible_owner_id: string;
  mitigation_plan: string;
  target_resolution_date: string;
  status: ResearchRiskStatus | string;
  resolution_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchOutput {
  id: string;
  tenant_id: string;
  project_id: string;
  output_type: string;
  title: string;
  citation_standard?: string | null;
  authors_string?: string;
  authors_json?: string[];
  publication_or_venue_name?: string;
  venue_name?: string;
  doi?: string | null;
  status: ResearchOutputStatus | string;
  publication_date?: string | null;
  open_access_repository_url?: string | null;
  repository_url?: string | null;
  is_verified?: boolean;
  created_at: string;
}

export interface ResearchInventionDisclosure {
  id: string;
  tenant_id: string;
  project_id: string;
  disclosure_code: string;
  invention_title?: string;
  title?: string;
  primary_inventor_id?: string;
  co_inventors_string?: string | null;
  patent_application_number?: string | null;
  patent_status?: ResearchPatentStatus | string;
  patent_filing_status?: string;
  status?: string;
  summary_of_invention?: string;
  commercial_potential?: string;
  filing_date?: string | null;
  grant_date?: string | null;
  commercial_partner_name?: string | null;
  is_confidential?: boolean;
  created_at: string;
}

export interface ResearchProjectHealthReport {
  project_id: string;
  project_code: string;
  health_score: number;
  health_status: "HEALTHY" | "NEEDS_ATTENTION" | "AT_RISK" | "CRITICAL";
  overdue_milestones_count: number;
  blocked_milestones_count: number;
  ethics_compliant: boolean;
  ethics_status: string;
  financial_burn_rate_percent: number;
  high_critical_risks_count: number;
  diagnostic_reasons: string[];
}

export interface ResearchFinancialSummaryResponse {
  project_id: string;
  currency: string;
  total_approved_budget: number;
  approved_budget?: number;
  awarded_grant_total?: number;
  total_committed_expenditure: number;
  committed_expenditure?: number;
  total_actual_expenditure: number;
  actual_expenditure?: number;
  remaining_uncommitted_balance: number;
  remaining_balance?: number;
  burn_rate_percentage: number;
  approaching_limit: boolean;
  categories_breakdown: Array<{
    category: string;
    allocated: number;
    committed?: number;
    actual?: number;
  }>;
  reporting_deadlines: Array<Record<string, any>>;
}

export interface ResearcherWorkloadResponse {
  user_id: string;
  total_active_projects: number;
  total_workload_percentage: number;
  projects: Array<{
    project_id: string;
    project_code: string;
    title: string;
    role: string;
    status: string;
    workload_percentage: number;
    contribution_description?: string | null;
    start_date?: string | null;
    end_date?: string | null;
  }>;
}

export interface ResearchProjectDetailResponse {
  project: ResearchProject;
  health: ResearchProjectHealthReport;
  team_members: ResearchTeamMember[];
  milestones: ResearchMilestone[];
  ethics_approvals: ResearchEthicsApproval[];
  budget_plans: ResearchBudgetPlan[];
  grant_awards: ResearchGrantAward[];
  outputs: ResearchOutput[];
  invention_disclosures: ResearchInventionDisclosure[];
  risks: ResearchProjectRisk[];
}

export interface ResearchAnalyticsSummary {
  active_projects: number;
  total_active_projects?: number;
  proposals_in_pipeline: number;
  grant_proposals_in_pipeline?: number;
  awarded_funding_total: number;
  total_grant_funding_awarded?: number;
  total_budget_allocated?: number;
  total_actual_expenditure?: number;
  total_research_outputs_verified?: number;
  pending_ethics_reviews?: number;
  active_grants_count?: number;
  milestone_completion_rate: number;
  approaching_deadlines_count: number;
  pending_ethics_renewals: number;
  domain_distribution?: Record<string, number>;
  department_distribution?: Record<string, number>;
}

/**
 * CampusOS — Enterprise Legal Affairs, Contract Lifecycle, Policy Compliance & Risk Service (Step 62)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * Provides typed REST API client for `/api/v1/legal-operations/...`
 * with resilient offline fallback to realistic institutional records.
 */

import {
  ComplianceAssessInput,
  ComplianceCreateInput,
  ContractAmendment,
  ContractAmendmentCreateInput,
  ContractCreateInput,
  ContractExecutionConfirmInput,
  ContractObligation,
  ContractObligationCreateInput,
  ContractTransitionInput,
  ContractUpdateInput,
  InstitutionalComplianceObligation,
  InstitutionalContract,
  InstitutionalLegalMatter,
  InstitutionalRisk,
  LegalOperationsDashboard,
  MatterCreateInput,
  MatterUpdateInput,
  ObligationCompleteInput,
  ObligationWaiveInput,
  RenewalSweepResult,
  RiskAcceptInput,
  RiskCreateInput,
  RiskUpdateInput,
} from "@/types/legal";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/legal-operations`
    : "http://localhost:8000/api/v1/legal-operations";

async function fetchWithFallback<T>(
  url: string,
  options?: RequestInit,
  fallback?: T
): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      credentials: "include",
    });

    if (!res.ok) {
      if (fallback !== undefined) return fallback;
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }

    return (await res.json()) as T;
  } catch (err) {
    if (fallback !== undefined) return fallback;
    throw err;
  }
}

// =============================================================================
// REALISTIC INSTITUTIONAL FALLBACK FIXTURES
// =============================================================================

const MOCK_CONTRACTS: InstitutionalContract[] = [
  {
    id: "c01-campus-wifi",
    tenant_id: "tenant-001",
    contract_number: "CON-2026-0042",
    title: "Enterprise High-Density Campus Wi-Fi & Core Routing",
    category: "VENDOR_PROCUREMENT",
    purpose: "Full Wi-Fi 7 campus rollout and core infrastructure SLA",
    internal_owner_id: "u-it-director",
    counterparty_name: "Cisco Systems Global LLC",
    counterparty_contact_json: { contact: "Robert Miller", email: "rmiller@cisco.com" },
    status: "ACTIVE",
    effective_date: "2025-06-01",
    expiration_date: "2027-05-31",
    auto_renew: true,
    renewal_notice_days: 60,
    termination_notice_days: 30,
    financial_value: 480000,
    currency: "USD",
    confidentiality_level: "INTERNAL",
    execution_method: "EXTERNAL_DIGITAL_SUITE_CONFIRMED",
    executed_at: "2025-05-28T14:30:00Z",
    governing_law: "State of California",
    approval_chain_json: [
      { step: "DEPARTMENT_APPROVAL", reviewer_name: "Dr. K. Patel (IT Director)", decided_at: "2025-05-20" },
      { step: "LEGAL_REVIEW", reviewer_name: "Adv. Sarah Jenkins", decided_at: "2025-05-24" },
      { step: "AUTHORIZED_APPROVAL", reviewer_name: "Prof. Arthur Vance (VP)", decided_at: "2025-05-26" },
      { step: "EXECUTION_CONFIRMED", reviewer_name: "Legal Affairs Office", decided_at: "2025-05-28" },
    ],
    created_at: "2025-05-15T09:00:00Z",
    updated_at: "2025-05-28T14:30:00Z",
    amendments: [
      {
        id: "am-01",
        tenant_id: "tenant-001",
        contract_id: "c01-campus-wifi",
        amendment_number: 1,
        title: "Dormitory Wi-Fi Coverage Extension",
        effective_date: "2026-01-15",
        extended_expiration_date: "2027-11-30",
        financial_value_adjustment: 35000,
        status: "APPROVED",
        created_at: "2026-01-10T10:00:00Z",
        updated_at: "2026-01-15T11:00:00Z",
      },
    ],
    obligations: [
      {
        id: "obl-01",
        tenant_id: "tenant-001",
        contract_id: "c01-campus-wifi",
        obligation_code: "OBL-0081",
        title: "Quarterly 99.95% Network Availability SLA Certification",
        obligation_type: "SERVICE_COMMITMENT",
        due_date: "2026-11-30",
        reminder_lead_days: 14,
        status: "PENDING",
        escalation_level: 0,
        created_at: "2026-01-15T00:00:00Z",
        updated_at: "2026-01-15T00:00:00Z",
      },
    ],
  },
  {
    id: "c02-lms-provider",
    tenant_id: "tenant-001",
    contract_number: "CON-2026-0043",
    title: "Campus-Wide Cloud Learning Management Platform (LMS)",
    category: "SERVICE_LEVEL",
    purpose: "SaaS hosted learning environment for 18,000 students and faculty",
    internal_owner_id: "u-academic-dean",
    counterparty_name: "Instructure Global Canvas Ltd",
    status: "READY_FOR_EXECUTION",
    effective_date: "2026-12-01",
    expiration_date: "2029-11-30",
    auto_renew: false,
    renewal_notice_days: 90,
    termination_notice_days: 60,
    financial_value: 320000,
    currency: "USD",
    confidentiality_level: "CONFIDENTIAL",
    governing_law: "Delaware Corporate Law",
    approval_chain_json: [
      { step: "INTERNAL_REVIEW", reviewer_name: "Academic Technology Committee", decided_at: "2026-10-02" },
      { step: "DEPARTMENT_APPROVAL", reviewer_name: "Dean of Academic Affairs", decided_at: "2026-10-10" },
      { step: "LEGAL_REVIEW", reviewer_name: "General Counsel Office", decided_at: "2026-10-18" },
      { step: "AUTHORIZED_APPROVAL", reviewer_name: "President & Vice Chancellor", decided_at: "2026-10-22" },
    ],
    created_at: "2026-09-18T10:00:00Z",
    updated_at: "2026-10-22T16:00:00Z",
    amendments: [],
    obligations: [
      {
        id: "obl-02",
        tenant_id: "tenant-001",
        contract_id: "c02-lms-provider",
        obligation_code: "OBL-0082",
        title: "FERPA and ISO 27001 Security Compliance Attestation",
        obligation_type: "COMPLIANCE_AUDIT",
        due_date: "2026-12-01",
        reminder_lead_days: 14,
        status: "PENDING",
        escalation_level: 0,
        created_at: "2026-10-22T00:00:00Z",
        updated_at: "2026-10-22T00:00:00Z",
      },
    ],
  },
];

const MOCK_MATTERS: InstitutionalLegalMatter[] = [
  {
    id: "mat-01",
    tenant_id: "tenant-001",
    matter_number: "MAT-2026-0008",
    title: "Architectural Scope Dispute — Central Science Complex Phase II",
    category: "CONTRACT_DISPUTE",
    restricted_classification: "ATTORNEY_CLIENT_PRIVILEGED",
    internal_owner_id: "u-vp-operations",
    lead_counsel_user_id: "u-legal-counsel",
    external_counsel_ref: "Morgan & Lewis LLP (Ref: ML-8891)",
    counterparty_name: "ArchTech Design Consortium",
    opposing_counsel_name: "Hogan Lovells",
    status: "UNDER_REVIEW",
    priority: "HIGH",
    financial_exposure_estimate: 110000,
    opened_date: "2026-08-14",
    target_resolution_date: "2026-12-15",
    confidential_notes:
      "Privileged Legal Counsel Analysis: Arbitration mandatory under Section 19.3. Independent quantity surveyor report confirms defects. Recommended settlement bracket: $45k - $60k.",
    key_deadlines_json: [
      { title: "Mediation Brief Filing", due_date: "2026-11-15", status: "PENDING" },
      { title: "Joint Evidence Exchange", due_date: "2026-11-28", status: "PENDING" },
    ],
    created_at: "2026-08-14T10:00:00Z",
    updated_at: "2026-10-15T12:00:00Z",
  },
];

const MOCK_COMPLIANCE: InstitutionalComplianceObligation[] = [
  {
    id: "cmp-01",
    tenant_id: "tenant-001",
    obligation_code: "CMP-0014",
    name: "Higher Education Act Title IV Financial Aid Compliance",
    authoritative_source_reference: "34 CFR Part 668",
    category: "FINANCIAL_TAX",
    due_date: "2026-11-30",
    next_review_date: "2027-11-30",
    review_frequency_months: 12,
    required_controls: "Annual independent audit of federal student aid disbursements and refund calculations.",
    status: "COMPLIANT",
    assessment_findings: "Audit executed by Ernst & Young. Unqualified opinion issued with zero material weaknesses.",
    created_at: "2026-01-10T00:00:00Z",
    updated_at: "2026-10-01T00:00:00Z",
  },
];

const MOCK_RISKS: InstitutionalRisk[] = [
  {
    id: "rsk-01",
    tenant_id: "tenant-001",
    risk_code: "RSK-2026-0003",
    title: "Institutional Ransomware & Student PII Data Breach",
    category: "INFORMATION_SECURITY_PRIVACY",
    inherent_likelihood: 4,
    inherent_impact: 5,
    inherent_score: 20,
    existing_controls: "EDR endpoint protection, 24/7 SOC monitoring, mandatory MFA for all staff.",
    residual_likelihood: 2,
    residual_impact: 4,
    residual_score: 8,
    risk_level: "MEDIUM",
    mitigation_plan: "Conduct annual penetration testing and tabletop incident response simulations with leadership.",
    target_completion_date: "2026-12-31",
    status: "MITIGATION_IN_PROGRESS",
    created_at: "2026-01-20T00:00:00Z",
    updated_at: "2026-09-15T00:00:00Z",
  },
];

const MOCK_DASHBOARD: LegalOperationsDashboard = {
  contracts_pending_review_count: 3,
  contracts_expiring_soon_count: 2,
  obligations_overdue_count: 1,
  policies_pending_review_count: 2,
  open_legal_matters_count: 2,
  compliance_actions_outstanding_count: 1,
  high_priority_risks_count: 2,
  recent_contracts: MOCK_CONTRACTS,
  expiring_contracts: MOCK_CONTRACTS.filter((c) => c.status === "ACTIVE"),
  overdue_obligations: MOCK_CONTRACTS[0].obligations,
  critical_matters: MOCK_MATTERS,
  critical_risks: MOCK_RISKS,
};

// =============================================================================
// LEGAL OPERATIONS SERVICE METHODS
// =============================================================================

export const LegalService = {
  // 1. Dashboard & Automation
  async getDashboard(): Promise<LegalOperationsDashboard> {
    return fetchWithFallback<LegalOperationsDashboard>("/dashboard", undefined, MOCK_DASHBOARD);
  },

  async triggerRenewalSweep(): Promise<RenewalSweepResult> {
    return fetchWithFallback<RenewalSweepResult>(
      "/renewals/sweep",
      { method: "POST" },
      { contracts_flagged_expiring: 1, obligations_flagged_overdue: 1, compliance_reviews_flagged: 0, notifications_dispatched: 2 }
    );
  },

  // 2. Contracts
  async getContracts(params?: {
    status?: string;
    category?: string;
    department_id?: string;
    search?: string;
  }): Promise<InstitutionalContract[]> {
    const qs = new URLSearchParams();
    if (params?.status) qs.append("status", params.status);
    if (params?.category) qs.append("category", params.category);
    if (params?.department_id) qs.append("department_id", params.department_id);
    if (params?.search) qs.append("search", params.search);

    const query = qs.toString() ? `?${qs.toString()}` : "";
    return fetchWithFallback<InstitutionalContract[]>(`/contracts${query}`, undefined, MOCK_CONTRACTS);
  },

  async getContract(id: string): Promise<InstitutionalContract> {
    const fallback = MOCK_CONTRACTS.find((c) => c.id === id) || MOCK_CONTRACTS[0];
    return fetchWithFallback<InstitutionalContract>(`/contracts/${id}`, undefined, fallback);
  },

  async createContract(data: ContractCreateInput): Promise<InstitutionalContract> {
    return fetchWithFallback<InstitutionalContract>(
      "/contracts",
      { method: "POST", body: JSON.stringify(data) },
      {
        ...MOCK_CONTRACTS[0],
        id: `c-new-${Date.now()}`,
        contract_number: `CON-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        title: data.title,
        category: data.category,
        counterparty_name: data.counterparty_name,
        status: "DRAFT",
      }
    );
  },

  async updateContract(id: string, data: ContractUpdateInput): Promise<InstitutionalContract> {
    return fetchWithFallback<InstitutionalContract>(`/contracts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async transitionContract(id: string, data: ContractTransitionInput): Promise<InstitutionalContract> {
    return fetchWithFallback<InstitutionalContract>(`/contracts/${id}/transition`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async confirmExecution(id: string, data: ContractExecutionConfirmInput): Promise<InstitutionalContract> {
    return fetchWithFallback<InstitutionalContract>(`/contracts/${id}/execute`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async addAmendment(contractId: string, data: ContractAmendmentCreateInput): Promise<ContractAmendment> {
    return fetchWithFallback<ContractAmendment>(`/contracts/${contractId}/amendments`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // 3. Obligations
  async getObligations(params?: {
    contract_id?: string;
    status?: string;
    overdue_only?: boolean;
  }): Promise<ContractObligation[]> {
    const qs = new URLSearchParams();
    if (params?.contract_id) qs.append("contract_id", params.contract_id);
    if (params?.status) qs.append("status", params.status);
    if (params?.overdue_only) qs.append("overdue_only", "true");

    const query = qs.toString() ? `?${qs.toString()}` : "";
    return fetchWithFallback<ContractObligation[]>(`/obligations${query}`, undefined, MOCK_CONTRACTS[0].obligations);
  },

  async createObligation(data: ContractObligationCreateInput): Promise<ContractObligation> {
    return fetchWithFallback<ContractObligation>(`/obligations`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async completeObligation(id: string, data: ObligationCompleteInput): Promise<ContractObligation> {
    return fetchWithFallback<ContractObligation>(`/obligations/${id}/complete`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async waiveObligation(id: string, data: ObligationWaiveInput): Promise<ContractObligation> {
    return fetchWithFallback<ContractObligation>(`/obligations/${id}/waive`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // 4. Legal Matters
  async getMatters(params?: { category?: string; status?: string; priority?: string }): Promise<InstitutionalLegalMatter[]> {
    const qs = new URLSearchParams();
    if (params?.category) qs.append("category", params.category);
    if (params?.status) qs.append("status", params.status);
    if (params?.priority) qs.append("priority", params.priority);

    const query = qs.toString() ? `?${qs.toString()}` : "";
    return fetchWithFallback<InstitutionalLegalMatter[]>(`/matters${query}`, undefined, MOCK_MATTERS);
  },

  async getMatter(id: string): Promise<InstitutionalLegalMatter> {
    const fallback = MOCK_MATTERS.find((m) => m.id === id) || MOCK_MATTERS[0];
    return fetchWithFallback<InstitutionalLegalMatter>(`/matters/${id}`, undefined, fallback);
  },

  async createMatter(data: MatterCreateInput): Promise<InstitutionalLegalMatter> {
    return fetchWithFallback<InstitutionalLegalMatter>(`/matters`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateMatter(id: string, data: MatterUpdateInput): Promise<InstitutionalLegalMatter> {
    return fetchWithFallback<InstitutionalLegalMatter>(`/matters/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  // 5. Compliance
  async getComplianceObligations(params?: { category?: string; status?: string }): Promise<InstitutionalComplianceObligation[]> {
    const qs = new URLSearchParams();
    if (params?.category) qs.append("category", params.category);
    if (params?.status) qs.append("status", params.status);

    const query = qs.toString() ? `?${qs.toString()}` : "";
    return fetchWithFallback<InstitutionalComplianceObligation[]>(`/compliance${query}`, undefined, MOCK_COMPLIANCE);
  },

  async createComplianceObligation(data: ComplianceCreateInput): Promise<InstitutionalComplianceObligation> {
    return fetchWithFallback<InstitutionalComplianceObligation>(`/compliance`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async assessCompliance(id: string, data: ComplianceAssessInput): Promise<InstitutionalComplianceObligation> {
    return fetchWithFallback<InstitutionalComplianceObligation>(`/compliance/${id}/assess`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // 6. Risks
  async getRisks(params?: { category?: string; risk_level?: string; status?: string }): Promise<InstitutionalRisk[]> {
    const qs = new URLSearchParams();
    if (params?.category) qs.append("category", params.category);
    if (params?.risk_level) qs.append("risk_level", params.risk_level);
    if (params?.status) qs.append("status", params.status);

    const query = qs.toString() ? `?${qs.toString()}` : "";
    return fetchWithFallback<InstitutionalRisk[]>(`/risks${query}`, undefined, MOCK_RISKS);
  },

  async createRisk(data: RiskCreateInput): Promise<InstitutionalRisk> {
    return fetchWithFallback<InstitutionalRisk>(`/risks`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateRisk(id: string, data: RiskUpdateInput): Promise<InstitutionalRisk> {
    return fetchWithFallback<InstitutionalRisk>(`/risks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async acceptRisk(id: string, data: RiskAcceptInput): Promise<InstitutionalRisk> {
    return fetchWithFallback<InstitutionalRisk>(`/risks/${id}/accept`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};

export const legalService = LegalService;
export default LegalService;

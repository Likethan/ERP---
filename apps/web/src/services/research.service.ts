/**
 * CampusOS — Enterprise Research Collaboration, Portfolio & Grants API Client (Step 61)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * Typed REST API service communicating with `/api/v1/research/...`
 */

import {
  ResearchAnalyticsSummary,
  ResearchBudgetPlan,
  ResearchEthicsApproval,
  ResearchFinancialSummaryResponse,
  ResearchFundingOpportunity,
  ResearchGrantApplication,
  ResearchGrantAward,
  ResearchInventionDisclosure,
  ResearchMilestone,
  ResearchOutput,
  ResearchProject,
  ResearchProjectDetailResponse,
  ResearchProjectHealthReport,
  ResearchProjectRisk,
  ResearchTeamMember,
  ResearcherWorkloadResponse,
} from "@/types/research";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/research";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    credentials: "include",
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    const message = errorBody?.detail || errorBody?.message || `Request failed with status ${res.status}`;
    throw new Error(message);
  }

  const json = await res.json();
  return json.data !== undefined ? json.data : json;
}

export const ResearchService = {
  // =========================================================================
  // 1. PROJECT PORTFOLIO & WORKSPACE
  // =========================================================================

  async getProjects(params?: {
    search?: string;
    category?: string;
    status?: string;
    pi_id?: string;
    user_id?: string;
    department_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<ResearchProject[]> {
    const query = new URLSearchParams();
    if (params?.search) query.set("search", params.search);
    if (params?.category) query.set("category", params.category);
    if (params?.status) query.set("status", params.status);
    if (params?.pi_id) query.set("pi_id", params.pi_id);
    if (params?.user_id) query.set("user_id", params.user_id);
    if (params?.department_id) query.set("department_id", params.department_id);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));

    const qs = query.toString();
    const data = await request<any>(`/projects${qs ? `?${qs}` : ""}`);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async getProject(projectId: string): Promise<ResearchProject> {
    return request<ResearchProject>(`/projects/${projectId}`);
  },

  async getProjectHealth(projectId: string): Promise<ResearchProjectHealthReport> {
    return request<ResearchProjectHealthReport>(`/projects/${projectId}/health`);
  },

  async getProjectDetails(projectId: string): Promise<ResearchProjectDetailResponse> {
    return request<ResearchProjectDetailResponse>(`/projects/${projectId}/details`);
  },

  async createProject(payload: Partial<ResearchProject>): Promise<ResearchProject> {
    return request<ResearchProject>("/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateProject(projectId: string, payload: Partial<ResearchProject>): Promise<ResearchProject> {
    return request<ResearchProject>(`/projects/${projectId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async transitionProjectStatus(
    projectId: string,
    targetStatus: string,
    reason?: string
  ): Promise<ResearchProject> {
    return request<ResearchProject>(`/projects/${projectId}/transition`, {
      method: "POST",
      body: JSON.stringify({
        target_status: targetStatus,
        transition_reason: reason || `Transitioned to ${targetStatus}`,
      }),
    });
  },

  // =========================================================================
  // 2. RESEARCH TEAMS & WORKLOAD
  // =========================================================================

  async getTeamMembers(projectId: string): Promise<ResearchTeamMember[]> {
    const data = await request<any>(`/projects/${projectId}/team`);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async addTeamMember(projectId: string, payload: Partial<ResearchTeamMember>): Promise<ResearchTeamMember> {
    return request<ResearchTeamMember>(`/projects/${projectId}/team`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getResearcherWorkload(userId: string): Promise<ResearcherWorkloadResponse> {
    return request<ResearcherWorkloadResponse>(`/team/users/${userId}/workload`);
  },

  async getMyProjects(): Promise<ResearcherWorkloadResponse> {
    return request<ResearcherWorkloadResponse>("/team/my-projects");
  },

  // =========================================================================
  // 3. FUNDING OPPORTUNITIES & EXPRESSIONS OF INTEREST
  // =========================================================================

  async getFundingOpportunities(params?: {
    status?: string;
    category?: string;
    limit?: number;
    offset?: number;
  }): Promise<ResearchFundingOpportunity[]> {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.category) query.set("category", params.category);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));

    const qs = query.toString();
    const data = await request<any>(`/opportunities${qs ? `?${qs}` : ""}`);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async getFundingOpportunity(opportunityId: string): Promise<ResearchFundingOpportunity> {
    return request<ResearchFundingOpportunity>(`/opportunities/${opportunityId}`);
  },

  async createFundingOpportunity(payload: Partial<ResearchFundingOpportunity>): Promise<ResearchFundingOpportunity> {
    return request<ResearchFundingOpportunity>("/opportunities", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async saveOpportunity(opportunityId: string, saved: boolean): Promise<ResearchFundingOpportunity> {
    return request<ResearchFundingOpportunity>(`/opportunities/${opportunityId}/save`, {
      method: "POST",
      body: JSON.stringify({ saved }),
    });
  },

  async recordOpportunityEOI(
    opportunityId: string,
    payload: {
      prospective_project_title: string;
      principal_investigator_id: string;
      notes: string;
      estimated_budget?: number | null;
    }
  ): Promise<ResearchFundingOpportunity> {
    return request<ResearchFundingOpportunity>(`/opportunities/${opportunityId}/eoi`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // =========================================================================
  // 4. GRANT PROPOSALS & SPONSOR DECISION
  // =========================================================================

  async getGrantApplications(params?: {
    project_id?: string;
    internal_status?: string;
    external_status?: string;
    limit?: number;
    offset?: number;
  }): Promise<ResearchGrantApplication[]> {
    const query = new URLSearchParams();
    if (params?.project_id) query.set("project_id", params.project_id);
    if (params?.internal_status) query.set("internal_status", params.internal_status);
    if (params?.external_status) query.set("external_status", params.external_status);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));

    const qs = query.toString();
    const data = await request<any>(`/grants/applications${qs ? `?${qs}` : ""}`);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async getGrantApplication(applicationId: string): Promise<ResearchGrantApplication> {
    return request<ResearchGrantApplication>(`/grants/applications/${applicationId}`);
  },

  async createGrantApplication(payload: Partial<ResearchGrantApplication>): Promise<ResearchGrantApplication> {
    return request<ResearchGrantApplication>("/grants/applications", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async reviewGrantApplication(
    applicationId: string,
    decision: string,
    comments: string
  ): Promise<ResearchGrantApplication> {
    return request<ResearchGrantApplication>(`/grants/applications/${applicationId}/review`, {
      method: "POST",
      body: JSON.stringify({ decision, comments }),
    });
  },

  async confirmExternalSubmission(
    applicationId: string,
    payload: {
      external_submission_reference: string;
      submission_date?: string;
      portal_url?: string;
    }
  ): Promise<ResearchGrantApplication> {
    return request<ResearchGrantApplication>(`/grants/applications/${applicationId}/confirm-submission`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async recordSponsorDecision(
    applicationId: string,
    payload: {
      decision: string;
      decision_date?: string;
      award_amount?: number;
      award_number?: string;
      sponsor_feedback?: string;
      decision_notes?: string;
      award_letter_url?: string;
      create_award_record?: boolean;
    }
  ): Promise<ResearchGrantApplication> {
    return request<ResearchGrantApplication>(`/grants/applications/${applicationId}/sponsor-decision`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // =========================================================================
  // 5. SPONSORED AGREEMENTS & AWARDS
  // =========================================================================

  async getSponsoredAgreements(params?: {
    project_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<ResearchGrantAward[]> {
    const query = new URLSearchParams();
    if (params?.project_id) query.set("project_id", params.project_id);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));

    const qs = query.toString();
    const data = await request<any>(`/agreements${qs ? `?${qs}` : ""}`);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async createSponsoredAgreement(payload: {
    agreement_number: string;
    project_id: string;
    grant_application_id?: string;
    funding_organization: string;
    award_amount: number;
    currency?: string;
    start_date: string;
    end_date: string;
    agreement_type?: string;
    contract_document_url?: string;
    scope_of_work?: string;
    deliverables?: any[];
    payment_milestones?: any[];
    reporting_obligations?: any[];
    financial_owner_id?: string;
  }): Promise<ResearchGrantAward> {
    return request<ResearchGrantAward>("/agreements", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async recordAgreementAmendment(
    awardId: string,
    payload: {
      amendment_number: string;
      amendment_date?: string;
      description: string;
      extended_end_date?: string;
      budget_adjustment?: number;
      document_url?: string;
    }
  ): Promise<ResearchGrantAward> {
    return request<ResearchGrantAward>(`/agreements/${awardId}/amendments`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // =========================================================================
  // 6. BUDGETS & RECONCILED FINANCIALS
  // =========================================================================

  async getProjectFinancialSummary(projectId: string): Promise<ResearchFinancialSummaryResponse> {
    return request<ResearchFinancialSummaryResponse>(`/budgets/projects/${projectId}/financial-summary`);
  },

  async getBudgetPlans(projectId?: string): Promise<ResearchBudgetPlan[]> {
    const path = projectId ? `/budgets/projects/${projectId}` : "/budgets";
    const data = await request<any>(path);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async createBudgetPlan(payload: Partial<ResearchBudgetPlan>): Promise<ResearchBudgetPlan> {
    return request<ResearchBudgetPlan>("/budgets", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // =========================================================================
  // 7. MILESTONES & DELIVERABLES
  // =========================================================================

  async getMilestones(projectId?: string): Promise<ResearchMilestone[]> {
    const path = projectId ? `/milestones/projects/${projectId}` : "/milestones";
    const data = await request<any>(path);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async createMilestone(payload: Partial<ResearchMilestone>): Promise<ResearchMilestone> {
    return request<ResearchMilestone>("/milestones", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async verifyMilestone(
    milestoneId: string,
    decision: string,
    notes: string
  ): Promise<ResearchMilestone> {
    return request<ResearchMilestone>(`/milestones/${milestoneId}/verify`, {
      method: "POST",
      body: JSON.stringify({ decision, verification_notes: notes }),
    });
  },

  // =========================================================================
  // 8. ETHICS & COMPLIANCE
  // =========================================================================

  async getEthicsApprovals(projectId?: string): Promise<ResearchEthicsApproval[]> {
    const path = projectId ? `/ethics/projects/${projectId}` : "/ethics";
    const data = await request<any>(path);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async createEthicsApproval(payload: Partial<ResearchEthicsApproval>): Promise<ResearchEthicsApproval> {
    return request<ResearchEthicsApproval>("/ethics", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async recordEthicsDecision(
    approvalId: string,
    payload: {
      decision: string;
      decision_rationale: string;
      conditions_and_restrictions?: string;
      expiry_date?: string;
    }
  ): Promise<ResearchEthicsApproval> {
    return request<ResearchEthicsApproval>(`/ethics/${approvalId}/decision`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // =========================================================================
  // 9. OUTPUTS & INTELLECTUAL PROPERTY
  // =========================================================================

  async getResearchOutputs(projectId?: string): Promise<ResearchOutput[]> {
    const path = projectId ? `/outputs?project_id=${projectId}` : "/outputs";
    const data = await request<any>(path);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async createResearchOutput(payload: Partial<ResearchOutput>): Promise<ResearchOutput> {
    return request<ResearchOutput>("/outputs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getInventionDisclosures(projectId?: string): Promise<ResearchInventionDisclosure[]> {
    const path = projectId ? `/ip/disclosures?project_id=${projectId}` : "/ip/disclosures";
    const data = await request<any>(path);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async createInventionDisclosure(payload: Partial<ResearchInventionDisclosure>): Promise<ResearchInventionDisclosure> {
    return request<ResearchInventionDisclosure>("/ip/disclosures", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // =========================================================================
  // 10. RISKS
  // =========================================================================

  async getProjectRisks(projectId: string): Promise<ResearchProjectRisk[]> {
    const data = await request<any>(`/risks/projects/${projectId}`);
    return Array.isArray(data) ? data : data?.items || [];
  },

  async createProjectRisk(payload: Partial<ResearchProjectRisk>): Promise<ResearchProjectRisk> {
    return request<ResearchProjectRisk>("/risks", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // =========================================================================
  // 11. ANALYTICS
  // =========================================================================

  async getAnalyticsSummary(): Promise<ResearchAnalyticsSummary> {
    return request<ResearchAnalyticsSummary>("/analytics/summary");
  },
};

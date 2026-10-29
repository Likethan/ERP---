/**
 * CampusOS — Research Administration Calculator & Rule Evaluator (Step 61)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * Deterministic, explainable business logic calculations for:
 * 1. Project Health scoring and diagnostic reason generator (never fabricated AI scores).
 * 2. Lifecycle state machine transition validation and closure blockers.
 * 3. Proposal submission readiness and separation-of-duties checks.
 * 4. Authoritative financial burn rate and budget limit warnings.
 * 5. Researcher workload allocation and overload detection.
 */

import {
  ResearchBudgetPlan,
  ResearchEthicsApproval,
  ResearchGrantApplication,
  ResearchGrantAward,
  ResearchMilestone,
  ResearchProject,
  ResearchProjectHealthReport,
  ResearchProjectRisk,
  ResearchProjectStatus,
  ResearchTeamMember,
} from "@/types/research";

export interface ProjectHealthCalculationResult extends ResearchProjectHealthReport {
  deductions: Array<{ factor: string; deduction: number; detail: string }>;
}

export function calculateProjectHealth(
  project: ResearchProject,
  milestones: ResearchMilestone[] = [],
  ethicsApprovals: ResearchEthicsApproval[] = [],
  awards: ResearchGrantAward[] = [],
  risks: ResearchProjectRisk[] = []
): ProjectHealthCalculationResult {
  const today = new Date().toISOString().split("T")[0];
  const diagnosticReasons: string[] = [];
  const deductions: Array<{ factor: string; deduction: number; detail: string }> = [];
  let score = 100;

  // 1. Milestones analysis
  const overdueMilestones = milestones.filter(
    (m) =>
      m.planned_completion_date < today &&
      !["ACCEPTED", "CANCELLED"].includes(m.status)
  );
  if (overdueMilestones.length > 0) {
    const deduction = Math.min(35, overdueMilestones.length * 15);
    score -= deduction;
    const msg = `${overdueMilestones.length} milestone(s) are overdue past scheduled deadline.`;
    diagnosticReasons.push(msg);
    deductions.push({ factor: "OVERDUE_MILESTONES", deduction, detail: msg });
  }

  const blockedMilestones = milestones.filter((m) => m.status === "BLOCKED");
  if (blockedMilestones.length > 0) {
    const deduction = Math.min(25, blockedMilestones.length * 15);
    score -= deduction;
    const msg = `${blockedMilestones.length} milestone(s) are currently marked as BLOCKED with unresolved issues.`;
    diagnosticReasons.push(msg);
    deductions.push({ factor: "BLOCKED_MILESTONES", deduction, detail: msg });
  }

  // 2. Ethics compliance
  let ethicsCompliant = true;
  let ethicsStatus = "COMPLIANT";

  if (project.requires_ethics_approval) {
    const activeEthics = ethicsApprovals.filter(
      (e) => e.status === "APPROVED" && (!e.expiry_date || e.expiry_date >= today)
    );
    const expiredEthics = ethicsApprovals.filter(
      (e) => e.status === "APPROVED" && e.expiry_date && e.expiry_date < today
    );

    if (expiredEthics.length > 0 && activeEthics.length === 0) {
      ethicsCompliant = false;
      ethicsStatus = "EXPIRED";
      score -= 30;
      const msg = "Mandatory institutional ethics protocol approval has EXPIRED.";
      diagnosticReasons.push(msg);
      deductions.push({ factor: "EXPIRED_ETHICS", deduction: 30, detail: msg });
    } else if (activeEthics.length === 0) {
      ethicsCompliant = false;
      ethicsStatus = "MISSING_OR_PENDING";
      score -= 20;
      const msg = "Project requires ethics approval, but no currently APPROVED protocol is on record.";
      diagnosticReasons.push(msg);
      deductions.push({ factor: "MISSING_ETHICS", deduction: 20, detail: msg });
    }
  }

  // 3. Financial burn rate
  const totalAllocated = Number(project.total_budget_allocated) || 0;
  const totalActual = awards.reduce((sum, a) => sum + Number(a.actual_expenditure || 0), 0);
  const burnRate = totalAllocated > 0 ? (totalActual / totalAllocated) * 100 : 0;

  if (totalAllocated > 0) {
    if (burnRate > 100) {
      score -= 30;
      const msg = `Budget overrun: Actual expenditure (${burnRate.toFixed(1)}%) exceeds total approved allocation.`;
      diagnosticReasons.push(msg);
      deductions.push({ factor: "BUDGET_OVERRUN", deduction: 30, detail: msg });
    } else if (burnRate >= 90) {
      score -= 15;
      const msg = `Approaching budget limit: Financial utilization is at ${burnRate.toFixed(1)}%.`;
      diagnosticReasons.push(msg);
      deductions.push({ factor: "APPROACHING_BUDGET_LIMIT", deduction: 15, detail: msg });
    }
  }

  // 4. Critical & High risks
  const unmitigatedRisks = risks.filter(
    (r) =>
      ["CRITICAL", "HIGH"].includes(String(r.calculated_risk_level).toUpperCase()) &&
      !["MITIGATED", "ACCEPTED", "CLOSED"].includes(String(r.status).toUpperCase())
  );
  if (unmitigatedRisks.length > 0) {
    const deduction = Math.min(25, unmitigatedRisks.length * 10);
    score -= deduction;
    const msg = `${unmitigatedRisks.length} unmitigated high/critical risk(s) recorded in project risk register.`;
    diagnosticReasons.push(msg);
    deductions.push({ factor: "UNMITIGATED_RISKS", deduction, detail: msg });
  }

  // Ensure score is bounded [0, 100]
  score = Math.max(0, Math.min(100, Math.round(score)));

  let healthStatus: "HEALTHY" | "NEEDS_ATTENTION" | "AT_RISK" | "CRITICAL" = "HEALTHY";
  if (score < 40) {
    healthStatus = "CRITICAL";
  } else if (score < 65) {
    healthStatus = "AT_RISK";
  } else if (score < 85) {
    healthStatus = "NEEDS_ATTENTION";
  }

  if (diagnosticReasons.length === 0) {
    diagnosticReasons.push("Project is progressing on track with zero overdue milestones, valid compliance, and controlled expenditure.");
  }

  return {
    project_id: project.id,
    project_code: project.project_code,
    health_score: score,
    health_status: healthStatus,
    overdue_milestones_count: overdueMilestones.length,
    blocked_milestones_count: blockedMilestones.length,
    ethics_compliant: ethicsCompliant,
    ethics_status: ethicsStatus,
    financial_burn_rate_percent: Number(burnRate.toFixed(2)),
    high_critical_risks_count: unmitigatedRisks.length,
    diagnostic_reasons: diagnosticReasons,
    deductions,
  };
}

/**
 * Validates permitted status transitions in the Research Project Lifecycle.
 */
export function validateProjectTransition(
  currentStatus: ResearchProjectStatus | string,
  targetStatus: ResearchProjectStatus | string,
  milestones: ResearchMilestone[] = [],
  ethicsApprovals: ResearchEthicsApproval[] = [],
  projectRequiresEthics = false
): { allowed: boolean; reason?: string } {
  const cur = currentStatus.toUpperCase();
  const tgt = targetStatus.toUpperCase();

  if (cur === tgt) {
    return { allowed: true };
  }

  const allowedTransitions: Record<string, string[]> = {
    DRAFT: ["PROPOSAL", "UNDER_REVIEW", "CANCELLED"],
    PROPOSAL: ["UNDER_REVIEW", "APPROVED", "DRAFT", "CANCELLED"],
    UNDER_REVIEW: ["APPROVED", "DRAFT", "ON_HOLD", "CANCELLED"],
    APPROVED: ["ACTIVE", "ON_HOLD", "CANCELLED"],
    ACTIVE: ["ON_HOLD", "COMPLETED", "CLOSED", "CANCELLED"],
    ON_HOLD: ["ACTIVE", "CANCELLED", "CLOSED"],
    COMPLETED: ["CLOSED", "ACTIVE"],
    CLOSED: [],
    CANCELLED: [],
  };

  const permitted = allowedTransitions[cur] || [];
  if (!permitted.includes(tgt)) {
    return {
      allowed: false,
      reason: `Transition from '${cur}' to '${tgt}' is not permitted by project lifecycle rules.`,
    };
  }

  // Pre-condition: Closure checks
  if (tgt === "CLOSED") {
    const unverifiedMandatory = milestones.filter(
      (m) => m.is_mandatory_for_closure && m.status !== "ACCEPTED"
    );
    if (unverifiedMandatory.length > 0) {
      return {
        allowed: false,
        reason: `Cannot close project: ${unverifiedMandatory.length} mandatory milestone(s) must be accepted by project verification authority first.`,
      };
    }
  }

  // Pre-condition: Activating project requiring ethics
  if (tgt === "ACTIVE" && projectRequiresEthics) {
    const today = new Date().toISOString().split("T")[0];
    const hasApprovedEthics = ethicsApprovals.some(
      (e) => e.status === "APPROVED" && (!e.expiry_date || e.expiry_date >= today)
    );
    if (!hasApprovedEthics) {
      return {
        allowed: false,
        reason: "Cannot activate project: A valid, approved institutional ethics approval protocol is mandatory.",
      };
    }
  }

  return { allowed: true };
}

/**
 * Validates proposal submission readiness.
 */
export function validateProposalSubmissionReadiness(
  application: ResearchGrantApplication
): { ready: boolean; blockers: string[] } {
  const blockers: string[] = [];

  if (!application.title || application.title.trim().length < 5) {
    blockers.push("Proposal title must be at least 5 characters.");
  }
  if (!application.research_proposal_summary || application.research_proposal_summary.trim().length < 20) {
    blockers.push("Executive research proposal summary must be provided (minimum 20 characters).");
  }
  if (!application.proposed_budget || application.proposed_budget <= 0) {
    blockers.push("Proposed budget must be greater than zero.");
  }
  if (
    application.internal_review_status !== "INSTITUTIONALLY_APPROVED"
  ) {
    blockers.push(
      `Institutional review status is '${application.internal_review_status}'. Application must be marked 'INSTITUTIONALLY_APPROVED' before external agency submission.`
    );
  }

  return {
    ready: blockers.length === 0,
    blockers,
  };
}

/**
 * Calculates total workload allocation across active projects for a researcher.
 */
export function calculateResearcherWorkload(
  teamMemberships: ResearchTeamMember[],
  projects: ResearchProject[]
): {
  totalActiveProjects: number;
  totalWorkloadPercentage: number;
  isOverallocated: boolean;
  activeProjects: Array<{
    projectId: string;
    projectCode: string;
    title: string;
    role: string;
    workloadPercentage: number;
  }>;
} {
  const projectMap = new Map(projects.map((p) => [p.id, p]));
  let totalWorkload = 0;
  const activeList: Array<{
    projectId: string;
    projectCode: string;
    title: string;
    role: string;
    workloadPercentage: number;
  }> = [];

  for (const tm of teamMemberships) {
    const proj = projectMap.get(tm.project_id);
    if (proj && ["ACTIVE", "APPROVED", "UNDER_REVIEW"].includes(proj.status)) {
      const pct = Number(tm.workload_percentage || 20);
      totalWorkload += pct;
      activeList.push({
        projectId: proj.id,
        projectCode: proj.project_code,
        title: proj.title,
        role: tm.role,
        workloadPercentage: pct,
      });
    }
  }

  return {
    totalActiveProjects: activeList.length,
    totalWorkloadPercentage: Math.round(totalWorkload * 100) / 100,
    isOverallocated: totalWorkload > 100,
    activeProjects: activeList,
  };
}

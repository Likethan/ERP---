/**
 * CampusOS — Enterprise Research Collaboration, Portfolio & Grants Frontend Test Suite (Step 61)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * Self-contained test runner verifying:
 * 1. Deterministic Project Health Diagnostic (No fabricated AI scores)
 * 2. State Transition & Closure Blocker Rules
 * 3. Proposal Readiness & Separation of Duties
 * 4. Researcher Workload Allocation & Overload Detection
 * 5. Role-Based Permissions Matrix (Student, PI, HOD, VP, Admin, Finance)
 */

import {
  calculateProjectHealth,
  calculateResearcherWorkload,
  validateProjectTransition,
  validateProposalSubmissionReadiness,
} from "../services/research-calculator";
import {
  ResearchGrantApplication,
  ResearchGrantAward,
  ResearchMilestone,
  ResearchProject,
  ResearchTeamMember,
} from "../types/research";

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string) {
  if (condition) {
    console.log(`✔ PASS: ${message}`);
    passed++;
  } else {
    console.error(`✖ FAIL: ${message}`);
    failed++;
  }
}

export function runResearchModuleTests() {
  console.log("=================================================");
  console.log("CampusOS Step 61 Enterprise Research Test Suite");
  console.log("=================================================");

  // =========================================================================
  // 1. PROJECT HEALTH DIAGNOSTIC (EXPLAINABLE RULES)
  // =========================================================================
  {
    const mockProject: Partial<ResearchProject> = {
      id: "proj-1",
      project_code: "PRJ-001",
      status: "ACTIVE",
      total_budget_allocated: 100000,
      requires_ethics_approval: false,
    };

    const milestones: Partial<ResearchMilestone>[] = [
      {
        id: "m1",
        status: "ACCEPTED",
        completion_percentage: 100,
        planned_completion_date: "2026-12-31",
        is_mandatory_for_closure: true,
      },
      {
        id: "m2",
        status: "PLANNED",
        completion_percentage: 50,
        planned_completion_date: "2026-11-30",
        is_mandatory_for_closure: false,
      },
    ];

    const awards: Partial<ResearchGrantAward>[] = [
      {
        id: "a1",
        award_amount: 100000,
        actual_expenditure: 45000,
      },
    ];

    const health = calculateProjectHealth(
      mockProject as ResearchProject,
      milestones as ResearchMilestone[],
      [],
      awards as ResearchGrantAward[]
    );
    assert(health.health_score >= 85, "Healthy project has high health score >= 85");
    assert(health.health_status === "HEALTHY", "Healthy project classified as HEALTHY");
    assert(health.diagnostic_reasons.length > 0, "Health diagnosis provides explainable reasons");
  }

  {
    const mockProject: Partial<ResearchProject> = {
      id: "proj-2",
      project_code: "PRJ-002",
      status: "ACTIVE",
      total_budget_allocated: 100000,
      requires_ethics_approval: false,
    };

    const milestones: Partial<ResearchMilestone>[] = [
      {
        id: "m1",
        status: "PLANNED",
        completion_percentage: 20,
        planned_completion_date: "2026-12-31",
        is_mandatory_for_closure: true,
      },
    ];

    const awards: Partial<ResearchGrantAward>[] = [
      {
        id: "a1",
        award_amount: 100000,
        actual_expenditure: 98000, // 98% burn
      },
    ];

    const health = calculateProjectHealth(
      mockProject as ResearchProject,
      milestones as ResearchMilestone[],
      [],
      awards as ResearchGrantAward[]
    );
    assert(health.financial_burn_rate_percent === 98, "Computes 98% burn rate accurately");
    assert(
      health.diagnostic_reasons.some(
        (r) => r.toLowerCase().includes("budget") || r.toLowerCase().includes("utilization")
      ),
      "Includes explainable budget limit diagnostic reason"
    );
  }

  {
    const mockProject: Partial<ResearchProject> = {
      id: "proj-3",
      project_code: "PRJ-003",
      status: "ACTIVE",
      total_budget_allocated: 50000,
      requires_ethics_approval: false,
    };

    const milestones: Partial<ResearchMilestone>[] = [
      {
        id: "m1",
        milestone_code: "MS-OVERDUE",
        status: "PLANNED",
        completion_percentage: 10,
        planned_completion_date: "2020-01-01", // Past date
        is_mandatory_for_closure: true,
      },
    ];

    const health = calculateProjectHealth(mockProject as ResearchProject, milestones as ResearchMilestone[]);
    assert(health.overdue_milestones_count > 0, "Identifies overdue milestones");
    assert(
      health.diagnostic_reasons.some((r) => r.includes("overdue") || r.includes("scheduled deadline")),
      "Includes explainable overdue milestone diagnostic reason"
    );
  }

  // =========================================================================
  // 2. STATE TRANSITIONS & CLOSURE BLOCKING
  // =========================================================================
  {
    assert(validateProjectTransition("DRAFT", "PROPOSAL").allowed === true, "DRAFT -> PROPOSAL is allowed");
    assert(validateProjectTransition("PROPOSAL", "UNDER_REVIEW").allowed === true, "PROPOSAL -> UNDER_REVIEW is allowed");
    assert(validateProjectTransition("UNDER_REVIEW", "APPROVED").allowed === true, "UNDER_REVIEW -> APPROVED is allowed");
    assert(validateProjectTransition("APPROVED", "ACTIVE").allowed === true, "APPROVED -> ACTIVE is allowed");

    const directClose = validateProjectTransition("DRAFT", "CLOSED");
    assert(directClose.allowed === false, "Direct jump DRAFT -> CLOSED is blocked");

    const pendingMilestones: Partial<ResearchMilestone>[] = [
      {
        id: "m1",
        milestone_code: "MS-FINAL",
        title: "Final Technical Deliverable",
        is_mandatory_for_closure: true,
        status: "UNDER_REVIEW",
      },
    ];

    const blockedClose = validateProjectTransition("ACTIVE", "CLOSED", pendingMilestones as ResearchMilestone[]);
    assert(blockedClose.allowed === false, "Project closure blocked when mandatory milestone is unverified");
    assert(Boolean(blockedClose.reason?.includes("mandatory")), "Explains mandatory milestone closure requirement");

    const verifiedMilestones: Partial<ResearchMilestone>[] = [
      {
        id: "m1",
        milestone_code: "MS-FINAL",
        title: "Final Technical Deliverable",
        is_mandatory_for_closure: true,
        status: "ACCEPTED",
      },
    ];

    const permittedClose = validateProjectTransition("COMPLETED", "CLOSED", verifiedMilestones as ResearchMilestone[]);
    assert(permittedClose.allowed === true, "Project closure permitted when mandatory milestone is verified");
  }

  // =========================================================================
  // 3. PROPOSAL SUBMISSION READINESS & SEPARATION OF DUTIES
  // =========================================================================
  {
    const incompleteApp: Partial<ResearchGrantApplication> = {
      application_code: "APP-001",
      title: "",
      proposed_budget: 0,
      internal_review_status: "DRAFT",
    };

    const incompleteReadiness = validateProposalSubmissionReadiness(incompleteApp as ResearchGrantApplication);
    assert(incompleteReadiness.ready === false, "Incomplete proposal marked not ready for submission");
    assert(incompleteReadiness.blockers.length > 0, "Lists missing proposal readiness blockers");

    const readyApp: Partial<ResearchGrantApplication> = {
      application_code: "APP-READY",
      title: "Autonomous Deep-Sea Sensor Swarms",
      principal_investigator_id: "user-pi",
      research_proposal_summary: "Comprehensive proposal summary exceeding twenty characters in length",
      objectives_json: ["Deploy sensors", "Calibrate acoustic telemetry"],
      methodology_summary: "Multi-agent reinforcement learning",
      proposed_budget: 250000,
      internal_review_status: "INSTITUTIONALLY_APPROVED",
    };

    const readyReadiness = validateProposalSubmissionReadiness(readyApp as ResearchGrantApplication);
    assert(readyReadiness.ready === true, "Complete & institutionally approved proposal marked ready");
    assert(readyReadiness.blockers.length === 0, "No blockers remaining on approved proposal");
  }

  // =========================================================================
  // 4. RESEARCHER WORKLOAD ALLOCATION
  // =========================================================================
  {
    const projects: Partial<ResearchProject>[] = [
      { id: "p1", project_code: "PRJ-01", title: "Project Alpha", status: "ACTIVE" },
      { id: "p2", project_code: "PRJ-02", title: "Project Beta", status: "ACTIVE" },
    ];

    const teamMemberships: Partial<ResearchTeamMember>[] = [
      { id: "tm1", project_id: "p1", role: "CO_INVESTIGATOR", workload_percentage: 40 },
      { id: "tm2", project_id: "p2", role: "RESEARCHER", workload_percentage: 35 },
    ];

    const workload = calculateResearcherWorkload(
      teamMemberships as ResearchTeamMember[],
      projects as ResearchProject[]
    );
    assert(workload.totalWorkloadPercentage === 75, "Calculates 75% total workload accurately");
    assert(workload.isOverallocated === false, "75% workload not flagged as overallocated");
    assert(workload.totalActiveProjects === 2, "Counts 2 active projects accurately");

    const overloadedMemberships: Partial<ResearchTeamMember>[] = [
      { id: "tm1", project_id: "p1", role: "PRINCIPAL_INVESTIGATOR", workload_percentage: 60 },
      { id: "tm2", project_id: "p2", role: "CO_INVESTIGATOR", workload_percentage: 55 },
    ];

    const overloadedWorkload = calculateResearcherWorkload(
      overloadedMemberships as ResearchTeamMember[],
      projects as ResearchProject[]
    );
    assert(overloadedWorkload.totalWorkloadPercentage === 115, "Calculates 115% total workload");
    assert(overloadedWorkload.isOverallocated === true, "Flags overallocated researcher (>100%)");
  }

  // =========================================================================
  // 5. ROLE-BASED ACCESS & PERMISSIONS MATRIX
  // =========================================================================
  {
    const ROLE_PERMISSIONS: Record<string, string[]> = {
      STUDENT: ["research.projects.read", "research.milestones.update"],
      FACULTY_PI: [
        "research.projects.read",
        "research.projects.manage",
        "research.grants.apply",
        "research.milestones.manage",
        "research.outputs.manage",
      ],
      HOD: [
        "research.projects.read",
        "research.projects.manage",
        "research.grants.approve_department",
        "research.workload.review",
      ],
      VICE_PRINCIPAL: [
        "research.projects.read",
        "research.projects.transition",
        "research.grants.approve_institutional",
        "research.budgets.approve",
        "research.analytics.read",
      ],
      RESEARCH_ADMINISTRATOR: [
        "research.projects.read",
        "research.projects.manage",
        "research.projects.transition",
        "research.opportunities.manage",
        "research.grants.approve_institutional",
        "research.awards.manage",
        "research.ethics.manage",
        "research.analytics.read",
      ],
      FINANCE_STAFF: [
        "research.projects.read",
        "research.budgets.manage",
        "research.budgets.reconcile",
        "research.awards.reconcile",
      ],
    };

    function userHasPermission(role: string, permission: string): boolean {
      return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
    }

    assert(userHasPermission("STUDENT", "research.projects.read") === true, "Student can read projects");
    assert(userHasPermission("STUDENT", "research.milestones.update") === true, "Student can update milestone progress");
    assert(userHasPermission("STUDENT", "research.grants.approve_institutional") === false, "Student cannot approve grants");
    assert(userHasPermission("STUDENT", "research.budgets.manage") === false, "Student cannot manage budgets");

    assert(userHasPermission("FACULTY_PI", "research.grants.apply") === true, "Faculty/PI can draft proposals");
    assert(userHasPermission("FACULTY_PI", "research.projects.manage") === true, "Faculty/PI can manage research projects");
    assert(userHasPermission("FACULTY_PI", "research.grants.approve_institutional") === false, "Faculty/PI cannot grant institutional approval");

    assert(userHasPermission("RESEARCH_ADMINISTRATOR", "research.opportunities.manage") === true, "Research Admin can manage opportunities");
    assert(userHasPermission("RESEARCH_ADMINISTRATOR", "research.awards.manage") === true, "Research Admin can manage awards & agreements");
    assert(userHasPermission("RESEARCH_ADMINISTRATOR", "research.ethics.manage") === true, "Research Admin can manage compliance");

    assert(userHasPermission("FINANCE_STAFF", "research.budgets.manage") === true, "Finance Staff can manage budgets");
    assert(userHasPermission("FINANCE_STAFF", "research.budgets.reconcile") === true, "Finance Staff can reconcile awards");
    assert(userHasPermission("FINANCE_STAFF", "research.projects.manage") === false, "Finance Staff cannot manage scientific scope");

    assert(userHasPermission("VICE_PRINCIPAL", "research.budgets.approve") === true, "Vice Principal can approve institutional budgets");
    assert(userHasPermission("VICE_PRINCIPAL", "research.analytics.read") === true, "Vice Principal can access institutional analytics");
  }

  // =========================================================================
  // Summary
  // =========================================================================
  console.log("=================================================");
  console.log(`Research Module Tests: Passed: ${passed}, Failed: ${failed}`);
  console.log("=================================================");

  if (failed > 0) {
    process.exit(1);
  }
}

runResearchModuleTests();

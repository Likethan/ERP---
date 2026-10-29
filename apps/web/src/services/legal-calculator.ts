/**
 * CampusOS — Institutional Legal Affairs & Contract Lifecycle Calculator (Step 62)
 * Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
 *
 * Deterministic business logic & explainable scoring for:
 * 1. Contract state machine transition validation
 * 2. Explainable 5x5 enterprise institutional risk scoring matrix
 * 3. Obligation compliance, overdue evaluation, and completion metrics
 * 4. Contract lifecycle badges, deadline warnings, and audit status tags
 */

import {
  ContractObligation,
  ContractStatus,
  ExecutionMethod,
  LegalMatterPriority,
  LegalMatterStatus,
  ObligationStatus,
  RiskLevel,
} from "@/types/legal";

export const VALID_CONTRACT_TRANSITIONS: Record<ContractStatus, ContractStatus[]> = {
  DRAFT: ["INTERNAL_REVIEW", "WITHDRAWN", "ON_HOLD"],
  INTERNAL_REVIEW: ["DEPARTMENT_APPROVAL", "REJECTED", "DRAFT", "ON_HOLD"],
  DEPARTMENT_APPROVAL: ["LEGAL_REVIEW", "REJECTED", "INTERNAL_REVIEW", "ON_HOLD"],
  LEGAL_REVIEW: ["AUTHORIZED_APPROVAL", "REJECTED", "DEPARTMENT_APPROVAL", "ON_HOLD"],
  AUTHORIZED_APPROVAL: ["READY_FOR_EXECUTION", "REJECTED", "ON_HOLD"],
  READY_FOR_EXECUTION: ["EXECUTED", "ON_HOLD", "REJECTED"],
  EXECUTED: ["ACTIVE"],
  ACTIVE: ["EXPIRING", "TERMINATED", "EXPIRED", "ON_HOLD", "RENEWED"],
  EXPIRING: ["RENEWED", "TERMINATED", "EXPIRED"],
  ON_HOLD: [
    "DRAFT",
    "INTERNAL_REVIEW",
    "DEPARTMENT_APPROVAL",
    "LEGAL_REVIEW",
    "AUTHORIZED_APPROVAL",
    "READY_FOR_EXECUTION",
    "ACTIVE",
  ],
  RENEWED: ["ACTIVE", "ARCHIVED"],
  TERMINATED: ["ARCHIVED"],
  EXPIRED: ["ARCHIVED"],
  REJECTED: ["DRAFT", "ARCHIVED"],
  WITHDRAWN: ["DRAFT", "ARCHIVED"],
  ARCHIVED: [],
};

export function canTransitionContract(
  current: ContractStatus,
  target: ContractStatus
): boolean {
  if (current === target) return false;
  const allowed = VALID_CONTRACT_TRANSITIONS[current] || [];
  return allowed.includes(target);
}

/**
 * 5x5 Enterprise Risk Scoring Matrix
 * Likelihood: 1 (Rare) to 5 (Almost Certain)
 * Impact: 1 (Negligible) to 5 (Catastrophic)
 * Likelihood x Impact = Score (1 to 25)
 * CRITICAL: 16-25 | HIGH: 10-15 | MEDIUM: 5-9 | LOW: 1-4
 */
export interface RiskScoreCalculation {
  score: number;
  level: RiskLevel;
  badgeClass: string;
  label: string;
  actionGuidance: string;
}

export function calculateRiskMatrix(
  likelihood: number,
  impact: number
): RiskScoreCalculation {
  const safeL = Math.max(1, Math.min(5, Math.round(likelihood)));
  const safeI = Math.max(1, Math.min(5, Math.round(impact)));
  const score = safeL * safeI;

  if (score >= 16) {
    return {
      score,
      level: "CRITICAL",
      badgeClass: "bg-rose-500/10 text-rose-700 border-rose-500/20",
      label: "Critical (16–25)",
      actionGuidance:
        "Immediate executive escalation required. Mandatory institutional mitigation plan and continuous monitoring.",
    };
  }
  if (score >= 10) {
    return {
      score,
      level: "HIGH",
      badgeClass: "bg-amber-500/10 text-amber-700 border-amber-500/20",
      label: "High (10–15)",
      actionGuidance:
        "Senior leadership review needed. Active mitigation controls must be implemented within 30 days.",
    };
  }
  if (score >= 5) {
    return {
      score,
      level: "MEDIUM",
      badgeClass: "bg-yellow-500/10 text-yellow-700 border-yellow-500/20",
      label: "Medium (5–9)",
      actionGuidance:
        "Department-level management and scheduled periodic review.",
    };
  }
  return {
    score,
    level: "LOW",
    badgeClass: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20",
    label: "Low (1–4)",
    actionGuidance:
      "Manageable under existing standard institutional controls.",
  };
}

export function isObligationOverdue(
  dueDateOrObl: string | ContractObligation,
  status?: ObligationStatus
): boolean {
  if (typeof dueDateOrObl === "object" && dueDateOrObl !== null) {
    const obl = dueDateOrObl as ContractObligation;
    if (obl.status === "COMPLETED" || obl.status === "WAIVED") return false;
    const today = new Date().toISOString().split("T")[0];
    return obl.due_date < today;
  }
  if (status === "COMPLETED" || status === "WAIVED") return false;
  const today = new Date().toISOString().split("T")[0];
  return (dueDateOrObl as string) < today;
}

export interface ObligationHealthMetrics {
  total: number;
  completed: number;
  pending: number;
  in_progress: number;
  overdue: number;
  waived: number;
  completionRatePercent: number;
}

export function calculateObligationHealth(
  obligations: ContractObligation[]
): ObligationHealthMetrics {
  const total = obligations.length;
  if (total === 0) {
    return {
      total: 0,
      completed: 0,
      pending: 0,
      in_progress: 0,
      overdue: 0,
      waived: 0,
      completionRatePercent: 100,
    };
  }

  let completed = 0;
  let pending = 0;
  let in_progress = 0;
  let overdue = 0;
  let waived = 0;

  for (const obl of obligations) {
    if (obl.status === "COMPLETED") completed++;
    else if (obl.status === "WAIVED") waived++;
    else if (isObligationOverdue(obl)) overdue++;
    else if (obl.status === "IN_PROGRESS") in_progress++;
    else pending++;
  }

  const effectiveTotal = total - waived;
  const completionRatePercent =
    effectiveTotal > 0 ? Math.round((completed / effectiveTotal) * 100) : 100;

  return {
    total,
    completed,
    pending,
    in_progress,
    overdue,
    waived,
    completionRatePercent,
  };
}

export interface ContractBadge {
  label: string;
  className: string;
  toString(): string;
}

function makeBadge(label: string, className: string): ContractBadge {
  return {
    label,
    className,
    toString() {
      return this.className;
    },
  };
}

export function getContractStatusBadge(status: ContractStatus): ContractBadge {
  switch (status) {
    case "DRAFT":
      return makeBadge("Draft", "bg-slate-100 text-slate-700 border-slate-200");
    case "INTERNAL_REVIEW":
      return makeBadge("Internal Review", "bg-blue-50 text-blue-700 border-blue-200");
    case "DEPARTMENT_APPROVAL":
      return makeBadge("Dept Approval", "bg-indigo-50 text-indigo-700 border-indigo-200");
    case "LEGAL_REVIEW":
      return makeBadge("Legal Review", "bg-purple-50 text-purple-700 border-purple-200");
    case "AUTHORIZED_APPROVAL":
      return makeBadge("Executive Signoff", "bg-violet-50 text-violet-700 border-violet-200");
    case "READY_FOR_EXECUTION":
      return makeBadge("Ready for Execution", "bg-amber-50 text-amber-700 border-amber-200");
    case "EXECUTED":
      return makeBadge("Executed", "bg-teal-50 text-teal-700 border-teal-200");
    case "ACTIVE":
      return makeBadge("Active", "bg-emerald-50 text-emerald-700 border-emerald-200");
    case "EXPIRING":
      return makeBadge("Expiring Soon", "bg-rose-50 text-rose-700 border-rose-200 animate-pulse");
    case "RENEWED":
      return makeBadge("Renewed", "bg-cyan-50 text-cyan-700 border-cyan-200");
    case "TERMINATED":
      return makeBadge("Terminated", "bg-red-50 text-red-700 border-red-200");
    case "EXPIRED":
      return makeBadge("Expired", "bg-gray-100 text-gray-700 border-gray-200");
    case "REJECTED":
      return makeBadge("Rejected", "bg-red-50 text-red-700 border-red-200");
    case "WITHDRAWN":
      return makeBadge("Withdrawn", "bg-zinc-100 text-zinc-700 border-zinc-200");
    case "ON_HOLD":
      return makeBadge("On Hold", "bg-yellow-50 text-yellow-700 border-yellow-200");
    case "ARCHIVED":
      return makeBadge("Archived", "bg-stone-100 text-stone-600 border-stone-200");
    default:
      return makeBadge(status, "bg-slate-100 text-slate-700 border-slate-200");
  }
}

export function formatCurrency(amount?: number | null, currency = "USD"): string {
  if (amount === undefined || amount === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatLegalDate(dateStr?: string | null): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export function getExecutionMethodLabel(method?: string | null): string {
  switch (method) {
    case "EXTERNAL_DIGITAL_SUITE_CONFIRMED":
      return "DocuSign / Adobe Sign Audit Certificate";
    case "WET_SIGNATURE_CONFIRMED":
      return "Physical Wet Signature (Countersigned Scan)";
    case "BOARD_RESOLUTION_CONFIRMED":
      return "Governing Board Seal & Resolution";
    case "HYBRID_CONFIRMED":
      return "Hybrid Counterpart Execution";
    default:
      return method ? method.replace(/_/g, " ") : "External Signature Verification";
  }
}

export function getConfidentialityBadge(level?: string): string {
  switch (level) {
    case "PUBLIC":
      return "bg-slate-100 text-slate-600 border border-slate-200";
    case "INTERNAL":
      return "bg-blue-50 text-blue-700 border border-blue-200";
    case "CONFIDENTIAL":
      return "bg-amber-50 text-amber-700 border border-amber-200";
    case "RESTRICTED":
      return "bg-rose-50 text-rose-700 border border-rose-200 font-bold";
    default:
      return "bg-slate-100 text-slate-600 border border-slate-200";
  }
}

export function getObligationStatusBadge(status: string): string {
  switch (status) {
    case "PENDING":
      return "bg-slate-100 text-slate-700 border border-slate-200";
    case "IN_PROGRESS":
      return "bg-blue-50 text-blue-700 border border-blue-200";
    case "UNDER_REVIEW":
      return "bg-indigo-50 text-indigo-700 border border-indigo-200";
    case "COMPLETED":
      return "bg-emerald-50 text-emerald-700 border border-emerald-200";
    case "WAIVED":
      return "bg-amber-50 text-amber-700 border border-amber-200";
    case "OVERDUE":
      return "bg-rose-50 text-rose-700 border border-rose-200 font-bold animate-pulse";
    default:
      return "bg-slate-100 text-slate-600 border border-slate-200";
  }
}

export function getMatterPriorityBadge(priority: string): string {
  switch (priority) {
    case "CRITICAL":
      return "bg-rose-100 text-rose-700 border border-rose-300 font-bold";
    case "HIGH":
      return "bg-amber-100 text-amber-700 border border-amber-300";
    case "MEDIUM":
      return "bg-blue-100 text-blue-700 border border-blue-300";
    case "LOW":
      return "bg-slate-100 text-slate-600 border border-slate-200";
    default:
      return "bg-slate-100 text-slate-600 border border-slate-200";
  }
}

export function getMatterStatusBadge(status: string): string {
  switch (status) {
    case "OPEN":
      return "bg-blue-50 text-blue-700 border border-blue-200";
    case "IN_INVESTIGATION":
      return "bg-indigo-50 text-indigo-700 border border-indigo-200";
    case "SETTLEMENT_NEGOTIATION":
      return "bg-purple-50 text-purple-700 border border-purple-200";
    case "LITIGATION_PENDING":
      return "bg-rose-50 text-rose-700 border border-rose-200 font-semibold";
    case "RESOLVED":
      return "bg-emerald-50 text-emerald-700 border border-emerald-200";
    case "CLOSED":
      return "bg-slate-100 text-slate-600 border border-slate-200";
    default:
      return "bg-slate-100 text-slate-600 border border-slate-200";
  }
}

export function getComplianceStatusBadge(status: string): string {
  switch (status) {
    case "COMPLIANT":
      return "bg-emerald-50 text-emerald-700 border border-emerald-200";
    case "PARTIALLY_COMPLIANT":
      return "bg-amber-50 text-amber-700 border border-amber-200";
    case "EVIDENCE_REQUIRED":
      return "bg-blue-50 text-blue-700 border border-blue-200";
    case "REMEDIATION_IN_PROGRESS":
      return "bg-purple-50 text-purple-700 border border-purple-200";
    case "NON_COMPLIANT":
      return "bg-rose-50 text-rose-700 border border-rose-200 font-bold";
    case "UNDER_REVIEW":
      return "bg-indigo-50 text-indigo-700 border border-indigo-200";
    default:
      return "bg-slate-100 text-slate-600 border border-slate-200";
  }
}

export function getRiskLevelBadge(level: string): string {
  switch (level) {
    case "CRITICAL":
      return "bg-rose-100 text-rose-700 border border-rose-300";
    case "HIGH":
      return "bg-amber-100 text-amber-700 border border-amber-300";
    case "MEDIUM":
      return "bg-yellow-100 text-yellow-700 border border-yellow-300";
    case "LOW":
      return "bg-emerald-100 text-emerald-700 border border-emerald-300";
    default:
      return "bg-slate-100 text-slate-600 border border-slate-200";
  }
}

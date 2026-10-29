/**
 * CampusOS Student Affairs & Disciplinary Case Calculations & Safeguard Helpers
 * "One Campus. One System. One Source of Truth."
 */

import {
  SACasePriority,
  SACaseStatus,
  SADisciplinaryStage,
  SAFindingStatus,
  GrievanceCaseModel,
  DisciplinaryProceedingModel,
} from "../types/student-affairs";

export interface SlaStatusResult {
  isOverdue: boolean;
  hoursRemaining: number;
  statusLabel: "ON_TRACK" | "AT_RISK" | "BREACHED" | "RESOLVED";
  badgeColor: string;
}

export interface ProceduralMilestone {
  stage: SADisciplinaryStage;
  label: string;
  isComplete: boolean;
  isCurrent: boolean;
}

export class StudentAffairsCalculator {
  /**
   * Calculates SLA compliance and remaining time for a case
   */
  static calculateSlaStatus(
    targetDateStr: string | null | undefined,
    currentStatus: SACaseStatus | string
  ): SlaStatusResult {
    if (
      currentStatus === SACaseStatus.RESOLVED ||
      currentStatus === SACaseStatus.CLOSED
    ) {
      return {
        isOverdue: false,
        hoursRemaining: 0,
        statusLabel: "RESOLVED",
        badgeColor: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
      };
    }

    if (!targetDateStr) {
      return {
        isOverdue: false,
        hoursRemaining: 999,
        statusLabel: "ON_TRACK",
        badgeColor: "bg-blue-500/10 text-blue-500 border-blue-500/20",
      };
    }

    const target = new Date(targetDateStr).getTime();
    const now = Date.now();
    const diffHours = Math.round((target - now) / (1000 * 60 * 60));

    if (diffHours < 0) {
      return {
        isOverdue: true,
        hoursRemaining: diffHours,
        statusLabel: "BREACHED",
        badgeColor: "bg-red-500/10 text-red-500 border-red-500/20 animate-pulse",
      };
    } else if (diffHours <= 24) {
      return {
        isOverdue: false,
        hoursRemaining: diffHours,
        statusLabel: "AT_RISK",
        badgeColor: "bg-amber-500/10 text-amber-500 border-amber-500/20",
      };
    }

    return {
      isOverdue: false,
      hoursRemaining: diffHours,
      statusLabel: "ON_TRACK",
      badgeColor: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    };
  }

  /**
   * Checks whether an appeal is within the authorized appeal window
   */
  static isAppealWindowActive(appealDeadlineStr: string | null | undefined): boolean {
    if (!appealDeadlineStr) return false;
    const deadline = new Date(appealDeadlineStr).getTime();
    return Date.now() <= deadline;
  }

  /**
   * Calculates remaining days for appeal filing
   */
  static getAppealDaysRemaining(appealDeadlineStr: string | null | undefined): number {
    if (!appealDeadlineStr) return 0;
    const deadline = new Date(appealDeadlineStr).getTime();
    const now = Date.now();
    const diffDays = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));
    return Math.max(0, diffDays);
  }

  /**
   * Validates separation of duties: appeal reviewer cannot be original decision maker
   */
  static validateSeparationOfDuties(
    originalDecisionMakerId: string | null | undefined,
    proposedAppealReviewerId: string | null | undefined
  ): { isValid: boolean; errorMessage?: string } {
    if (!originalDecisionMakerId || !proposedAppealReviewerId) {
      return { isValid: true };
    }
    if (originalDecisionMakerId === proposedAppealReviewerId) {
      return {
        isValid: false,
        errorMessage:
          "Institutional Procedural Fairness Policy: The original decision maker cannot act as the appellate reviewer.",
      };
    }
    return { isValid: true };
  }

  /**
   * Evaluates procedural milestones for disciplinary proceeding
   */
  static evaluateProceduralMilestones(
    proceeding: DisciplinaryProceedingModel | null | undefined
  ): {
    milestones: ProceduralMilestone[];
    completionPercentage: number;
  } {
    const stages: Array<{ stage: SADisciplinaryStage; label: string }> = [
      { stage: SADisciplinaryStage.INTAKE_ASSESSMENT, label: "Intake & Policy Review" },
      { stage: SADisciplinaryStage.NOTICE_ISSUED, label: "Formal Notice Served" },
      { stage: SADisciplinaryStage.INVESTIGATION_ACTIVE, label: "Investigation & Inquiry" },
      { stage: SADisciplinaryStage.HEARING_SCHEDULED, label: "Hearing / Committee Panel" },
      { stage: SADisciplinaryStage.FINDINGS_RECORDED, label: "Formal Findings" },
      { stage: SADisciplinaryStage.SANCTION_APPROVED, label: "Sanction / Decision" },
      { stage: SADisciplinaryStage.CONCLUDED, label: "Concluded / Post-Appeal" },
    ];

    if (!proceeding) {
      return {
        milestones: stages.map((s) => ({
          ...s,
          isComplete: false,
          isCurrent: false,
        })),
        completionPercentage: 0,
      };
    }

    const currentStage = proceeding.procedural_stage as SADisciplinaryStage;
    const stageIndexMap: Record<string, number> = {
      [SADisciplinaryStage.INTAKE_ASSESSMENT]: 0,
      [SADisciplinaryStage.NOTICE_ISSUED]: 1,
      [SADisciplinaryStage.INVESTIGATION_ACTIVE]: 2,
      [SADisciplinaryStage.HEARING_SCHEDULED]: 3,
      [SADisciplinaryStage.FINDINGS_RECORDED]: 4,
      [SADisciplinaryStage.SANCTION_APPROVED]: 5,
      [SADisciplinaryStage.APPEAL_PENDING]: 5,
      [SADisciplinaryStage.CONCLUDED]: 6,
    };

    const currentIdx = stageIndexMap[currentStage] ?? 0;

    const milestones: ProceduralMilestone[] = stages.map((s, idx) => {
      const isComplete = idx < currentIdx || currentStage === SADisciplinaryStage.CONCLUDED;
      const isCurrent = idx === currentIdx && currentStage !== SADisciplinaryStage.CONCLUDED;
      return {
        ...s,
        isComplete,
        isCurrent,
      };
    });

    const completedCount = milestones.filter((m) => m.isComplete).length;
    const completionPercentage = Math.round((completedCount / stages.length) * 100);

    return { milestones, completionPercentage };
  }

  /**
   * Formats case number with readable prefix
   */
  static formatCaseNumber(caseNumber: string): string {
    return caseNumber.toUpperCase();
  }

  /**
   * Computes priority badge styling
   */
  static getPriorityBadge(priority: SACasePriority | string): {
    label: string;
    className: string;
  } {
    switch (priority) {
      case SACasePriority.CRITICAL_URGENT:
        return {
          label: "Critical Urgent",
          className: "bg-red-500/10 text-red-500 border-red-500/20 font-semibold",
        };
      case SACasePriority.HIGH:
        return {
          label: "High Priority",
          className: "bg-orange-500/10 text-orange-500 border-orange-500/20",
        };
      case SACasePriority.MEDIUM:
        return {
          label: "Medium Priority",
          className: "bg-blue-500/10 text-blue-500 border-blue-500/20",
        };
      case SACasePriority.LOW:
      default:
        return {
          label: "Low Priority",
          className: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
        };
    }
  }

  /**
   * Computes status badge styling
   */
  static getStatusBadge(status: SACaseStatus | string): {
    label: string;
    className: string;
  } {
    switch (status) {
      case SACaseStatus.SUBMITTED:
        return { label: "Submitted", className: "bg-amber-500/10 text-amber-500 border-amber-500/20" };
      case SACaseStatus.ACKNOWLEDGED:
        return { label: "Acknowledged", className: "bg-blue-500/10 text-blue-500 border-blue-500/20" };
      case SACaseStatus.UNDER_REVIEW:
        return { label: "Under Review", className: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20" };
      case SACaseStatus.INVESTIGATION:
        return { label: "Investigation", className: "bg-purple-500/10 text-purple-500 border-purple-500/20" };
      case SACaseStatus.HEARING:
        return { label: "Hearing Scheduled", className: "bg-pink-500/10 text-pink-500 border-pink-500/20" };
      case SACaseStatus.AWAITING_INFO:
        return { label: "Awaiting Info", className: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" };
      case SACaseStatus.RESOLVED:
        return { label: "Resolved", className: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" };
      case SACaseStatus.CLOSED:
        return { label: "Closed", className: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20" };
      case SACaseStatus.REOPENED:
        return { label: "Reopened", className: "bg-rose-500/10 text-rose-500 border-rose-500/20" };
      default:
        return { label: String(status), className: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20" };
    }
  }
}

/**
 * CampusOS Centralized Attendance Calculation Engine
 * Standardized institutional calculations for percentages, weighted attendance,
 * risk classifications, and recovery projections.
 */

import { AttendanceRiskLevel, AttendancePolicy } from "@/types/attendance";

export interface AttendanceCounts {
  present: number;
  absent: number;
  late: number;
  excused: number;
  total?: number;
}

export const DEFAULT_ATTENDANCE_POLICY: AttendancePolicy = {
  id: "pol-default",
  name: "CampusOS Standard Academic Regulations",
  departmentId: "ALL",
  departmentName: "Institutional Default",
  academicYear: "2026-2027",
  minimumPercentage: 75,
  warningThreshold: 80,
  criticalThreshold: 65,
  includeExcusedInTotal: true,
  lateArrivalWeight: 0.5,
  requireApprovalForCorrections: true,
  maxLeaveDaysConsecutive: 5,
  status: "ACTIVE",
};

/**
 * Calculates attendance percentage considering late weights and excused session rules.
 */
export function calculateAttendancePercentage(
  counts: AttendanceCounts,
  policy: AttendancePolicy = DEFAULT_ATTENDANCE_POLICY
): number {
  const total = counts.total ?? (counts.present + counts.absent + counts.late + counts.excused);
  if (total <= 0) return 100;

  const excusedValue = policy.includeExcusedInTotal ? counts.excused : 0;
  const effectivePresent = counts.present + counts.late * policy.lateArrivalWeight + excusedValue;

  const rawPercent = (effectivePresent / total) * 100;
  return Number(Math.min(100, Math.max(0, rawPercent)).toFixed(1));
}

/**
 * Derives risk status according to policy thresholds.
 */
export function determineAttendanceRisk(
  percentage: number,
  policy: AttendancePolicy = DEFAULT_ATTENDANCE_POLICY
): AttendanceRiskLevel {
  if (percentage < policy.criticalThreshold) {
    return "CRITICAL";
  }
  if (percentage < policy.warningThreshold) {
    return "WARNING";
  }
  return "HEALTHY";
}

/**
 * Calculates how many consecutive sessions a student must attend to reach target minimum (e.g. 75%).
 * Formula: (P*T - A) / (1 - P) where P is target fraction (0.75), T is total sessions, A is attended.
 */
export function calculateSessionsNeededToRecover(
  attended: number,
  total: number,
  targetPercentage: number = 75
): number {
  if (total <= 0) return 0;
  const targetFraction = targetPercentage / 100;
  const currentFraction = attended / total;

  if (currentFraction >= targetFraction) {
    return 0;
  }

  // (targetFraction * total - attended) / (1 - targetFraction)
  const numerator = targetFraction * total - attended;
  const denominator = 1 - targetFraction;
  return Math.max(0, Math.ceil(numerator / denominator));
}

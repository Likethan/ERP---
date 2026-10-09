/**
 * CampusOS Intelligence — Pure Domain Calculators
 * Pure arithmetic and rule-based decision engines without side-effects.
 */

import {
  StudentIntelligenceProfile,
  DepartmentHealthSummary,
  CampusHealthMetric,
} from "@campusos/types";

/**
 * Categorizes attendance risk based on institutional policy thresholds:
 * >= 85%: LOW risk
 * 75% - 84.9%: MEDIUM risk (warning zone)
 * 60% - 74.9%: HIGH risk (exam condonation required)
 * < 60%: CRITICAL risk (detention risk)
 */
export function calculateAttendanceRisk(
  attendancePercentage: number
): "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" {
  if (attendancePercentage >= 85) return "LOW";
  if (attendancePercentage >= 75) return "MEDIUM";
  if (attendancePercentage >= 60) return "HIGH";
  return "CRITICAL";
}

/**
 * Computes academic risk using CGPA and backlogs/failed subjects:
 * CGPA >= 7.5 and 0 backlogs -> LOW
 * CGPA >= 6.0 and <= 1 backlog -> MEDIUM
 * CGPA >= 5.0 or 2 backlogs -> HIGH
 * CGPA < 5.0 or > 2 backlogs -> CRITICAL
 */
export function calculateAcademicRisk(
  cgpa: number,
  failedSubjects = 0
): "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" {
  if (failedSubjects > 2 || cgpa < 5.0) return "CRITICAL";
  if (failedSubjects >= 2 || cgpa < 6.0) return "HIGH";
  if (failedSubjects === 1 || cgpa < 7.5) return "MEDIUM";
  return "LOW";
}

/**
 * Calculates finance risk based on outstanding balance and overdue aging:
 */
export function calculateFinanceRisk(
  outstandingBalance: number,
  overdueDays = 0
): "CLEAR" | "LOW" | "MEDIUM" | "HIGH" {
  if (outstandingBalance <= 0) return "CLEAR";
  if (outstandingBalance > 50000 || overdueDays > 60) return "HIGH";
  if (outstandingBalance > 20000 || overdueDays > 30) return "MEDIUM";
  return "LOW";
}

/**
 * Computes placement funnel metrics:
 * Conversion rate = (Placed / Eligible) * 100
 * Shortlist rate = (Shortlisted / Applied) * 100
 */
export function calculatePlacementActivity(
  eligibleCount: number,
  appliedCount: number,
  shortlistedCount: number,
  placedCount: number
): {
  placementRate: number;
  shortlistRate: number;
  applicationRate: number;
} {
  const safeEligible = Math.max(0, eligibleCount);
  const safeApplied = Math.max(0, appliedCount);

  const placementRate = safeEligible > 0
    ? Number(((placedCount / safeEligible) * 100).toFixed(1))
    : 0;

  const shortlistRate = safeApplied > 0
    ? Number(((shortlistedCount / safeApplied) * 100).toFixed(1))
    : 0;

  const applicationRate = safeEligible > 0
    ? Number(((appliedCount / safeEligible) * 100).toFixed(1))
    : 0;

  return {
    placementRate: Math.min(100, placementRate),
    shortlistRate: Math.min(100, shortlistRate),
    applicationRate: Math.min(100, applicationRate),
  };
}

/**
 * Evaluates student extracurricular engagement:
 */
export function calculateCampusEngagement(
  clubMemberships: number,
  eventParticipations: number
): "LOW" | "MODERATE" | "HIGH" | "VERY_HIGH" {
  const points = clubMemberships * 2 + eventParticipations;
  if (points >= 6) return "VERY_HIGH";
  if (points >= 4) return "HIGH";
  if (points >= 2) return "MODERATE";
  return "LOW";
}

/**
 * Computes infrastructure operational risk:
 * High occupancy (>95%) with open complaints (>5) yields HIGH risk
 */
export function calculateInfrastructureRisk(
  occupancyPercentage: number,
  openComplaints: number,
  pendingWorkOrders = 0
): {
  score: number;
  status: "NORMAL" | "ELEVATED" | "CRITICAL";
} {
  let score = 0;
  if (occupancyPercentage > 95) score += 40;
  else if (occupancyPercentage > 85) score += 20;

  if (openComplaints > 10) score += 40;
  else if (openComplaints > 5) score += 20;

  if (pendingWorkOrders > 5) score += 20;

  const finalScore = Math.min(100, score);
  const status = finalScore >= 70 ? "CRITICAL" : finalScore >= 40 ? "ELEVATED" : "NORMAL";

  return { score: finalScore, status };
}

/**
 * Computes document compliance risk:
 */
export function calculateDocumentRisk(
  missingDocumentsCount: number,
  expiringDocumentsCount: number
): "LOW" | "MEDIUM" | "HIGH" {
  if (missingDocumentsCount > 2) return "HIGH";
  if (missingDocumentsCount > 0 || expiringDocumentsCount > 1) return "MEDIUM";
  return "LOW";
}

/**
 * Evaluates a holistic Student Risk Score (0 = perfect standing, 100 = critical intervention required)
 */
export function calculateStudentRiskSummary(
  profile: Partial<StudentIntelligenceProfile>
): {
  compositeScore: number;
  primaryRiskFactor: string;
  recommendedUrgency: "IMMEDIATE" | "MONITOR" | "NONE";
} {
  let riskScore = 0;
  let primaryFactor = "None";

  // Attendance weight: 35%
  const attPct = profile.attendancePercentage ?? 100;
  if (attPct < 60) {
    riskScore += 35;
    primaryFactor = "Severe Attendance Shortfall (<60%)";
  } else if (attPct < 75) {
    riskScore += 20;
    if (primaryFactor === "None") primaryFactor = "Attendance Condonation Risk (<75%)";
  }

  // Academic weight: 35%
  const failed = profile.failedSubjectsCount ?? 0;
  const cgpa = profile.cgpa ?? 8.0;
  if (failed > 1 || cgpa < 5.0) {
    riskScore += 35;
    primaryFactor = "Academic Backlogs";
  } else if (failed === 1 || cgpa < 6.0) {
    riskScore += 20;
    if (primaryFactor === "None") primaryFactor = "Marginal Academic Standing";
  }

  // Finance weight: 15%
  if (profile.financeStatus === "OVERDUE") {
    riskScore += 15;
    if (primaryFactor === "None") primaryFactor = "Overdue Fee Installments";
  }

  // Document weight: 15%
  if ((profile.missingDocumentsCount ?? 0) > 0) {
    riskScore += 15;
    if (primaryFactor === "None") primaryFactor = "Missing Mandatory Credentials";
  }

  const urgency = riskScore >= 50 ? "IMMEDIATE" : riskScore >= 25 ? "MONITOR" : "NONE";

  return {
    compositeScore: Math.min(100, riskScore),
    primaryRiskFactor: primaryFactor,
    recommendedUrgency: urgency,
  };
}

/**
 * Computes Department Health Index (0 - 100)
 */
export function calculateDepartmentHealth(
  dept: Partial<DepartmentHealthSummary>
): {
  score: number;
  status: "EXCELLENT" | "GOOD" | "ATTENTION" | "CRITICAL";
} {
  const att = dept.avgAttendance ?? 85;
  const place = dept.placementRate ?? 80;
  const fee = dept.feeCollectionRate ?? 90;
  const docs = dept.documentCompletionRate ?? 95;

  // Weighted health index
  const score = Math.round(
    att * 0.35 +
    place * 0.30 +
    fee * 0.20 +
    docs * 0.15
  );

  const clamped = Math.max(0, Math.min(100, score));
  let status: "EXCELLENT" | "GOOD" | "ATTENTION" | "CRITICAL" = "GOOD";

  if (clamped >= 88) status = "EXCELLENT";
  else if (clamped >= 75) status = "GOOD";
  else if (clamped >= 60) status = "ATTENTION";
  else status = "CRITICAL";

  return { score: clamped, status };
}

/**
 * Computes Overall Campus Health Index across all domains
 */
export function calculateCampusHealth(
  metrics: CampusHealthMetric[]
): {
  overallScore: number;
  status: "EXCELLENT" | "GOOD" | "ATTENTION" | "CRITICAL";
  criticalAlertCount: number;
} {
  if (!metrics || metrics.length === 0) {
    return { overallScore: 85, status: "GOOD", criticalAlertCount: 0 };
  }

  const totalScore = metrics.reduce((acc, m) => acc + (m.healthScore || 0), 0);
  const avg = Math.round(totalScore / metrics.length);
  const criticalAlerts = metrics.reduce((acc, m) => acc + (m.alertCount || 0), 0);

  let status: "EXCELLENT" | "GOOD" | "ATTENTION" | "CRITICAL" = "GOOD";
  if (avg >= 88 && criticalAlerts <= 1) status = "EXCELLENT";
  else if (avg >= 75 && criticalAlerts <= 3) status = "GOOD";
  else if (avg >= 60) status = "ATTENTION";
  else status = "CRITICAL";

  return {
    overallScore: avg,
    status,
    criticalAlertCount: criticalAlerts,
  };
}

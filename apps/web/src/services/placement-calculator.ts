/**
 * CampusOS Placement Management — Placement & Eligibility Calculator Engine
 * Pure mathematical functions for eligibility evaluation, compensation metrics, and placement rates.
 */

import {
  StudentPlacementProfile,
  Position,
  EligibilitySnapshot,
  RuleEvaluationResult,
  EligibilityStatus,
} from "@/types/placement";

// ==========================================
// 1. Eligibility Rule Checkers
// ==========================================

export function checkProgramEligibility(
  studentProgram: string,
  targetPrograms: string[],
): RuleEvaluationResult {
  if (!targetPrograms || targetPrograms.length === 0) {
    return {
      rule: "PROGRAM",
      ruleName: "Academic Program",
      required: "Any Program",
      actual: studentProgram,
      passed: true,
      message: "Open to all programs",
    };
  }

  const passed = targetPrograms.some(
    (p) =>
      p.toLowerCase().trim() === studentProgram.toLowerCase().trim() ||
      studentProgram.toLowerCase().includes(p.toLowerCase()) ||
      p.toLowerCase().includes(studentProgram.toLowerCase()),
  );

  return {
    rule: "PROGRAM",
    ruleName: "Academic Program",
    required: targetPrograms,
    actual: studentProgram,
    passed,
    message: passed
      ? `Program ${studentProgram} satisfies requirement`
      : `Program ${studentProgram} is not in target programs (${targetPrograms.join(", ")})`,
  };
}

export function checkGraduationYearEligibility(
  studentGradYear: number,
  targetGradYear: number,
): RuleEvaluationResult {
  if (!targetGradYear) {
    return {
      rule: "GRADUATION_YEAR",
      ruleName: "Graduation Batch",
      required: "Any Batch",
      actual: studentGradYear,
      passed: true,
      message: "No specific graduation year restriction",
    };
  }

  const passed = studentGradYear === targetGradYear;
  return {
    rule: "GRADUATION_YEAR",
    ruleName: "Graduation Batch",
    required: targetGradYear,
    actual: studentGradYear,
    passed,
    message: passed
      ? `Batch ${studentGradYear} matches target drive batch`
      : `Target batch is ${targetGradYear}, student belongs to ${studentGradYear}`,
  };
}

export function checkCgpaEligibility(
  studentCgpa: number,
  minCgpa: number,
): RuleEvaluationResult {
  const passed = studentCgpa >= (minCgpa || 0);
  return {
    rule: "MIN_CGPA",
    ruleName: "Minimum CGPA Threshold",
    required: minCgpa || 0,
    actual: studentCgpa,
    passed,
    message: passed
      ? `CGPA ${studentCgpa.toFixed(2)} meets minimum cutoff ${minCgpa.toFixed(2)}`
      : `CGPA ${studentCgpa.toFixed(2)} is below minimum cutoff ${minCgpa.toFixed(2)}`,
  };
}

export function checkBacklogEligibility(
  activeBacklogs: number,
  maxBacklogs: number,
): RuleEvaluationResult {
  const allowed = maxBacklogs !== undefined ? maxBacklogs : 0;
  const passed = activeBacklogs <= allowed;
  return {
    rule: "MAX_BACKLOGS",
    ruleName: "Active Backlog Limit",
    required: allowed,
    actual: activeBacklogs,
    passed,
    message: passed
      ? `Active backlogs (${activeBacklogs}) within acceptable limit (${allowed})`
      : `Active backlogs (${activeBacklogs}) exceeds maximum allowed limit (${allowed})`,
  };
}

export function checkAttendanceEligibility(
  attendancePercent: number,
  minAttendancePercent?: number,
): RuleEvaluationResult {
  if (!minAttendancePercent || minAttendancePercent <= 0) {
    return {
      rule: "MIN_ATTENDANCE",
      ruleName: "Attendance Compliance",
      required: "N/A",
      actual: `${attendancePercent}%`,
      passed: true,
      message: "Attendance criterion not enforced for this drive",
    };
  }

  const passed = attendancePercent >= minAttendancePercent;
  return {
    rule: "MIN_ATTENDANCE",
    ruleName: "Attendance Compliance",
    required: `${minAttendancePercent}%`,
    actual: `${attendancePercent}%`,
    passed,
    message: passed
      ? `Attendance ${attendancePercent}% meets minimum requirement (${minAttendancePercent}%)`
      : `Attendance ${attendancePercent}% is below mandatory threshold (${minAttendancePercent}%)`,
  };
}

export function checkSkillEligibility(
  studentSkills: string[],
  requiredSkills: string[],
): RuleEvaluationResult {
  if (!requiredSkills || requiredSkills.length === 0) {
    return {
      rule: "SKILLS",
      ruleName: "Key Skill Competencies",
      required: "None Specified",
      actual: studentSkills,
      passed: true,
      message: "No specific mandatory skills declared",
    };
  }

  const lowerStudentSkills = studentSkills.map((s) => s.toLowerCase().trim());
  const matched = requiredSkills.filter((req) =>
    lowerStudentSkills.some(
      (s) => s === req.toLowerCase().trim() || s.includes(req.toLowerCase()),
    ),
  );

  const passed = matched.length >= Math.ceil(requiredSkills.length * 0.5); // at least 50% match
  return {
    rule: "SKILLS",
    ruleName: "Key Skill Competencies",
    required: requiredSkills,
    actual: matched,
    passed,
    message: passed
      ? `Matched ${matched.length}/${requiredSkills.length} required skills (${matched.join(", ")})`
      : `Missing key skills. Matched only ${matched.length}/${requiredSkills.length} (${matched.join(", ") || "None"})`,
  };
}

// ==========================================
// 2. Comprehensive Eligibility Engine
// ==========================================

export function calculateEligibility(
  student: StudentPlacementProfile,
  position: Position,
): EligibilitySnapshot {
  // Combine all student technical and programming skills
  const allStudentSkills = [
    ...(student.skills?.technical || []),
    ...(student.skills?.programmingLanguages || []),
    ...(student.skills?.toolsAndFrameworks || []),
    ...(student.skills?.domains || []),
  ];

  const progRule = checkProgramEligibility(
    student.program,
    position.targetPrograms,
  );
  const gradRule = checkGraduationYearEligibility(
    student.graduationYear,
    position.graduationYear,
  );
  const cgpaRule = checkCgpaEligibility(student.cgpa, position.minCgpa);
  const backlogRule = checkBacklogEligibility(
    student.activeBacklogs,
    position.maxBacklogs,
  );
  const attRule = checkAttendanceEligibility(
    student.attendancePercent,
    position.minAttendancePercent,
  );
  const skillRule = checkSkillEligibility(
    allStudentSkills,
    position.requiredSkills,
  );

  const rules: RuleEvaluationResult[] = [
    progRule,
    gradRule,
    cgpaRule,
    backlogRule,
    attRule,
    skillRule,
  ];

  // Determine overall status
  let status: EligibilityStatus = "ELIGIBLE";

  // Critical barriers: Program, Grad Year, CGPA, Backlogs
  const criticalFails = [progRule, gradRule, cgpaRule, backlogRule].filter(
    (r) => !r.passed,
  );

  if (criticalFails.length > 0) {
    status = "INELIGIBLE";
  } else if (!attRule.passed || !skillRule.passed) {
    status = "CONDITIONALLY_ELIGIBLE";
  }

  return {
    studentId: student.studentId,
    studentName: student.studentName,
    rollNumber: student.rollNumber,
    driveId: position.driveId,
    positionId: position.id,
    status,
    rules,
    evaluatedAt: new Date().toISOString(),
  };
}

// ==========================================
// 3. Compensation & Rate Metrics
// ==========================================

export function calculatePlacementRate(
  placedCount: number,
  eligibleCount: number,
): number {
  if (!eligibleCount || eligibleCount <= 0) return 0;
  return Math.min(100, Math.round((placedCount / eligibleCount) * 100));
}

export function calculateOfferRate(
  offersCount: number,
  eligibleCount: number,
): number {
  if (!eligibleCount || eligibleCount <= 0) return 0;
  return Math.min(100, Math.round((offersCount / eligibleCount) * 100));
}

export function calculateShortlistRate(
  shortlistedCount: number,
  applicationsCount: number,
): number {
  if (!applicationsCount || applicationsCount <= 0) return 0;
  return Math.min(
    100,
    Math.round((shortlistedCount / applicationsCount) * 100),
  );
}

export function calculateApplicationConversion(
  placedCount: number,
  applicationsCount: number,
): number {
  if (!applicationsCount || applicationsCount <= 0) return 0;
  return Math.min(100, Math.round((placedCount / applicationsCount) * 100));
}

export function calculateAveragePackage(packages: number[]): number {
  if (!packages || packages.length === 0) return 0;
  const valid = packages.filter((p) => p > 0);
  if (valid.length === 0) return 0;
  const sum = valid.reduce((acc, curr) => acc + curr, 0);
  return Math.round((sum / valid.length) * 10) / 10;
}

export function calculateMedianPackage(packages: number[]): number {
  if (!packages || packages.length === 0) return 0;
  const valid = packages.filter((p) => p > 0).sort((a, b) => a - b);
  if (valid.length === 0) return 0;
  const mid = Math.floor(valid.length / 2);
  if (valid.length % 2 !== 0) {
    return valid[mid];
  }
  return Math.round(((valid[mid - 1] + valid[mid]) / 2) * 10) / 10;
}

export function calculateHighestPackage(packages: number[]): number {
  if (!packages || packages.length === 0) return 0;
  const valid = packages.filter((p) => p > 0);
  if (valid.length === 0) return 0;
  return Math.max(...valid);
}

export function formatLPA(lpa: number): string {
  if (!lpa || lpa <= 0) return "₹0.0 LPA";
  return `₹${lpa.toFixed(1)} LPA`;
}

export function formatPackageRange(minLpa: number, maxLpa: number): string {
  if (!minLpa && !maxLpa) return "As per industry norms";
  if (minLpa === maxLpa) return formatLPA(minLpa);
  return `${formatLPA(minLpa)} - ${formatLPA(maxLpa)}`;
}

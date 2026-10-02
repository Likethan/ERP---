/**
 * CampusOS Grading and Assessment Calculation Engine
 * Pure mathematical functions for weighted marks, percentage, grade mapping,
 * result statuses, and grade distributions.
 */

import {
  GradeScale,
  GradeRule,
  ResultStatus,
  AssessmentComponent,
} from "@/types/examinations";

export const DEFAULT_GRADE_SCALE: GradeScale = {
  id: "grade-scale-ug-2026",
  name: "UGC 10-Point Choice Based Credit System (CBCS)",
  academicYear: "2026-2027",
  isDefault: true,
  rules: [
    { grade: "A+", minPercentage: 90, maxPercentage: 100, gradePoint: 10.0, isPass: true, description: "Outstanding" },
    { grade: "A",  minPercentage: 80, maxPercentage: 89.9, gradePoint: 9.0,  isPass: true, description: "Excellent" },
    { grade: "B+", minPercentage: 70, maxPercentage: 79.9, gradePoint: 8.0,  isPass: true, description: "Very Good" },
    { grade: "B",  minPercentage: 60, maxPercentage: 69.9, gradePoint: 7.0,  isPass: true, description: "Good" },
    { grade: "C",  minPercentage: 50, maxPercentage: 59.9, gradePoint: 6.0,  isPass: true, description: "Above Average" },
    { grade: "D",  minPercentage: 40, maxPercentage: 49.9, gradePoint: 5.0,  isPass: true, description: "Pass" },
    { grade: "E",  minPercentage: 35, maxPercentage: 39.9, gradePoint: 4.0,  isPass: true, description: "Marginal / Conditional Pass" },
    { grade: "F",  minPercentage: 0,  maxPercentage: 34.9, gradePoint: 0.0,  isPass: false, description: "Fail" },
  ],
};

/**
 * Calculates total max marks and cumulative weightage across assessment components.
 */
export function calculateAssessmentTotal(components: AssessmentComponent[]): {
  totalMaxMarks: number;
  totalWeightage: number;
  isValidWeightage: boolean;
} {
  if (!components || components.length === 0) {
    return { totalMaxMarks: 0, totalWeightage: 0, isValidWeightage: false };
  }

  const totalMaxMarks = components.reduce((acc, c) => acc + (c.maxMarks || 0), 0);
  const totalWeightage = components.reduce((acc, c) => acc + (c.weightage || 0), 0);
  const isValidWeightage = Math.abs(totalWeightage - 100) < 0.01;

  return { totalMaxMarks, totalWeightage, isValidWeightage };
}

/**
 * Calculates weighted score contribution for a component.
 * e.g. 18 / 20 with 20% weightage = 18.0
 */
export function calculateWeightedMarks(
  obtained: number | null | undefined,
  max: number,
  weightagePercent: number
): number {
  if (obtained === null || obtained === undefined || isNaN(obtained) || max <= 0) {
    return 0;
  }
  const clampedObtained = Math.min(Math.max(obtained, 0), max);
  const weighted = (clampedObtained / max) * weightagePercent;
  return Math.round(weighted * 10) / 10;
}

/**
 * Computes standard percentage rounded to 1 decimal place.
 */
export function calculatePercentage(obtained: number, max: number): number {
  if (!max || max <= 0) return 0;
  const pct = (obtained / max) * 100;
  return Math.min(100, Math.max(0, Math.round(pct * 10) / 10));
}

/**
 * Maps a numeric percentage to letter grade and grade point.
 */
export function calculateGrade(
  percentage: number,
  scale: GradeScale = DEFAULT_GRADE_SCALE
): GradeRule {
  const normalized = Math.min(100, Math.max(0, percentage));
  const matched = scale.rules.find(
    (r) => normalized >= r.minPercentage && normalized <= r.maxPercentage
  );

  return (
    matched || {
      grade: "F",
      minPercentage: 0,
      maxPercentage: 34.9,
      gradePoint: 0.0,
      isPass: false,
      description: "Fail",
    }
  );
}

/**
 * Determines formal result status based on mark states and percentage.
 */
export function calculateResultStatus(options: {
  percentage: number;
  isAbsent?: boolean;
  isWithheld?: boolean;
  isMalpractice?: boolean;
  isIncomplete?: boolean;
  passingPercentage?: number;
}): ResultStatus {
  const {
    percentage,
    isAbsent,
    isWithheld,
    isMalpractice,
    isIncomplete,
    passingPercentage = 40,
  } = options;

  if (isWithheld || isMalpractice) return "WITHHELD";
  if (isAbsent) return "ABSENT";
  if (isIncomplete) return "INCOMPLETE";

  return percentage >= passingPercentage ? "PASS" : "FAIL";
}

/**
 * Compiles statistical grade distribution across result items.
 */
export function calculateGradeDistribution(
  results: { grade: string }[]
): { grade: string; count: number; percentage: number }[] {
  const grades = ["A+", "A", "B+", "B", "C", "D", "E", "F"];
  const counts: Record<string, number> = {};
  grades.forEach((g) => (counts[g] = 0));

  results.forEach((r) => {
    if (counts[r.grade] !== undefined) {
      counts[r.grade]++;
    } else {
      counts["F"] = (counts["F"] || 0) + 1;
    }
  });

  const total = results.length || 1;
  return grades.map((grade) => ({
    grade,
    count: counts[grade] || 0,
    percentage: Math.round(((counts[grade] || 0) / total) * 100),
  }));
}

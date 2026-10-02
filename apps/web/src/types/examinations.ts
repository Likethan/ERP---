/**
 * CampusOS Examination & Assessment Domain Types
 * Canonical types for Assessments, Components, Examinations, Exam Schedules,
 * Eligibility, Marks Entry, Mark Corrections, Grade Scales, Results, and Publications.
 */

// ==========================================
// 1. Status & Core Enums
// ==========================================

export type AssessmentType =
  | "INTERNAL"
  | "ASSIGNMENT"
  | "QUIZ"
  | "LABORATORY"
  | "PRACTICAL"
  | "MODEL_EXAM"
  | "MIDTERM"
  | "END_SEMESTER"
  | "PROJECT"
  | "VIVA";

export type AssessmentStatus =
  | "DRAFT"
  | "SCHEDULED"
  | "OPEN"
  | "COMPLETED"
  | "FINALIZED"
  | "CANCELLED";

export type ExaminationType =
  | "INTERNAL"
  | "MODEL"
  | "MID_SEMESTER"
  | "END_SEMESTER"
  | "PRACTICAL"
  | "VIVA"
  | "PROJECT";

export type ExaminationStatus =
  | "DRAFT"
  | "SCHEDULED"
  | "ONGOING"
  | "COMPLETED"
  | "CANCELLED";

export type ExamScheduleStatus =
  | "SCHEDULED"
  | "CONFIRMED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "RESCHEDULED"
  | "CANCELLED";

export type EligibilityStatus =
  | "ELIGIBLE"
  | "INELIGIBLE"
  | "PENDING_REVIEW"
  | "CONDITIONALLY_ELIGIBLE";

export type MarkStatus =
  | "NOT_ENTERED"
  | "ENTERED"
  | "ABSENT"
  | "NOT_ATTEMPTED"
  | "WITHHELD"
  | "MALPRACTICE"
  | "FINALIZED";

export type MarkCorrectionStatus =
  | "PENDING"
  | "APPROVED"
  | "REJECTED"
  | "CANCELLED";

export type ResultStatus =
  | "PASS"
  | "FAIL"
  | "ABSENT"
  | "WITHHELD"
  | "INCOMPLETE";

export type PublicationStatus =
  | "DRAFT"
  | "READY"
  | "PUBLISHED"
  | "REVOKED";

// ==========================================
// 2. Assessment & Component Types
// ==========================================

export interface AssessmentComponent {
  id: string;
  name: string;
  type: AssessmentType;
  maxMarks: number;
  passingMarks: number;
  weightage: number; // percentage, e.g. 20
  sequence: number;
  description?: string;
}

export interface Assessment {
  id: string;
  name: string;
  code?: string;
  type: AssessmentType;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  section: string;
  department: string;
  academicYear: string;
  semester: number;
  facultyId: string;
  facultyName: string;
  maxMarks: number;
  passingMarks: number;
  weightage: number; // e.g. 40%
  sequence: number;
  date: string;
  status: AssessmentStatus;
  isFinalized: boolean;
  finalizedAt?: string;
  components?: AssessmentComponent[];
  totalEnrolled: number;
  totalEntered: number;
  createdAt: string;
}

// ==========================================
// 3. Examination & Timetable Schedules
// ==========================================

export interface Examination {
  id: string;
  name: string;
  academicYear: string;
  semester: number;
  type: ExaminationType;
  startDate: string;
  endDate: string;
  status: ExaminationStatus;
  totalSubjects: number;
  totalCandidates: number;
  description?: string;
  createdAt: string;
}

export interface ExamSchedule {
  id: string;
  examinationId: string;
  examinationName: string;
  assessmentId?: string;
  assessmentTitle?: string;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  program: string;
  department: string;
  semester: number;
  section: string;
  date: string;
  startTime: string;
  endTime: string;
  room: string;
  facultyId: string;
  facultyName: string;
  totalCandidates: number;
  status: ExamScheduleStatus;
  invigilatorNotes?: string;
  createdAt: string;
}

export interface ExamConflictCheck {
  hasConflict: boolean;
  conflictType?: "ROOM_OVERLAP" | "SECTION_OVERLAP" | "FACULTY_OVERLAP" | "STUDENT_OVERLAP";
  message?: string;
  conflictingScheduleId?: string;
}

// ==========================================
// 4. Student Eligibility Types
// ==========================================

export interface ExamEligibility {
  id: string;
  examinationId: string;
  examinationName: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  program: string;
  department: string;
  semester: number;
  section: string;
  attendancePercentage: number;
  minimumRequirement: number; // default 75%
  eligibilityStatus: EligibilityStatus;
  reason?: string;
  evaluatedDate: string;
  evaluatedBy: string;
  isOverridden: boolean;
  overrideReason?: string;
  overriddenBy?: string;
}

// ==========================================
// 5. Marks Entry & Corrections
// ==========================================

export interface Mark {
  id: string;
  assessmentId: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  courseOfferingId: string;
  maxMarks: number;
  marksObtained: number | null;
  status: MarkStatus;
  isAbsent: boolean;
  remarks?: string;
  moderatedMarks?: number | null;
  isFinalized: boolean;
  finalizedAt?: string;
  updatedAt: string;
}

export interface MarkCorrection {
  id: string;
  markId: string;
  assessmentId: string;
  assessmentName: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  courseCode: string;
  courseName: string;
  originalMark: number | null;
  requestedMark: number | null;
  originalStatus: MarkStatus;
  requestedStatus: MarkStatus;
  reason: string;
  requestedBy: string;
  requestedDate: string;
  reviewedBy?: string;
  reviewedDate?: string;
  status: MarkCorrectionStatus;
  reviewerNotes?: string;
  timeline: {
    timestamp: string;
    action: string;
    actor: string;
    notes?: string;
  }[];
}

// ==========================================
// 6. Grade Scale & Rules
// ==========================================

export interface GradeRule {
  grade: string;
  minPercentage: number;
  maxPercentage: number;
  gradePoint: number;
  isPass: boolean;
  description: string;
}

export interface GradeScale {
  id: string;
  name: string;
  academicYear: string;
  rules: GradeRule[];
  isDefault: boolean;
}

// ==========================================
// 7. Results & Publication
// ==========================================

export interface AssessmentScoreBreakdown {
  componentName: string;
  componentType: AssessmentType;
  maxMarks: number;
  obtainedMarks: number;
  weightage: number; // percentage
  weightedScore: number;
}

export interface Result {
  id: string;
  examinationId: string;
  examinationName: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  department: string;
  semester: number;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  credits: number;
  facultyName: string;
  academicYear: string;
  assessmentBreakdown: AssessmentScoreBreakdown[];
  totalMarks: number;
  maxMarks: number;
  percentage: number;
  grade: string;
  gradePoint: number;
  status: ResultStatus;
  isFinalized: boolean;
  finalizedAt?: string;
  isPublished: boolean;
  publishedAt?: string;
}

export interface ResultPublication {
  id: string;
  batchNumber: string;
  examinationId: string;
  examinationName: string;
  academicYear: string;
  semester: number;
  program: string;
  department: string;
  publicationDate: string;
  status: PublicationStatus;
  resultCount: number;
  publishedBy?: string;
  notes?: string;
  publishedAt?: string;
}

// ==========================================
// 8. Operations Dashboard & Reports
// ==========================================

export interface ExamReportFilter {
  academicYear?: string;
  semester?: number;
  department?: string;
  program?: string;
  section?: string;
  courseOfferingId?: string;
  examinationId?: string;
  startDate?: string;
  endDate?: string;
  reportType:
    | "COMPLETION"
    | "MARKS_ROSTER"
    | "SCHEDULE"
    | "ELIGIBILITY"
    | "RESULTS"
    | "DEPARTMENT_PERFORMANCE"
    | "PUBLICATIONS";
}

export interface ExamDashboardSummary {
  activeExaminationsCount: number;
  upcomingExamsCount: number;
  totalAssessmentsCount: number;
  pendingMarksCount: number;
  marksAwaitingReviewCount: number;
  eligibleStudentsCount: number;
  ineligibleStudentsCount: number;
  resultsAwaitingFinalizationCount: number;
  resultsAwaitingPublicationCount: number;
  publishedResultsCount: number;
  departmentPerformance: {
    department: string;
    passRate: number;
    studentCount: number;
  }[];
  gradeDistribution: {
    grade: string;
    count: number;
    percentage: number;
  }[];
}

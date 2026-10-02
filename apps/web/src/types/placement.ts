/**
 * CampusOS Placement Management — Domain Types
 * Unified typing for students, corporate partners, job drives, positions,
 * eligibility engine, applications, shortlisting, interviews, offers, outcomes, and reports.
 */

export interface AuditEntry {
  id: string;
  action: string;
  actor: string;
  timestamp: string;
  details?: string;
  fromStatus?: string;
  toStatus?: string;
}

// ==========================================
// 1. Student Placement Profile & Skills
// ==========================================

export type PlacementProfileStatus =
  | "ACTIVE"
  | "INACTIVE"
  | "OPTED_OUT"
  | "BLOCKED";

export type ResumeStatus =
  | "NOT_UPLOADED"
  | "UPLOADED"
  | "UNDER_REVIEW"
  | "VERIFIED"
  | "REJECTED";

export interface StudentSkillsProfile {
  technical: string[];
  programmingLanguages: string[];
  toolsAndFrameworks: string[];
  domains: string[];
  certifications: string[];
}

export interface StudentPlacementProfile {
  id: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  email: string;
  phone: string;
  program: string;
  department: string;
  graduationYear: number;
  currentSemester: number;
  cgpa: number;
  activeBacklogs: number;
  historyBacklogs: number;
  attendancePercent: number;
  skills: StudentSkillsProfile;
  resumeUrl?: string;
  resumeStatus: ResumeStatus;
  resumeUpdatedAt?: string;
  resumeNotes?: string;
  profileCompletionPercent: number;
  status: PlacementProfileStatus;
  applicationsCount: number;
  shortlistsCount: number;
  interviewsCount: number;
  offersCount: number;
  placementStatus: PlacementStatus;
  placedCompany?: string;
  placedPackageLpa?: number;
  createdAt?: string;
  updatedAt?: string;
  timeline: AuditEntry[];
}

// ==========================================
// 2. Corporate Partners & Companies
// ==========================================

export type CompanyStatus =
  | "PROSPECT"
  | "ACTIVE"
  | "INACTIVE"
  | "BLACKLISTED";

export type CompanyType =
  | "PRODUCT"
  | "SERVICE"
  | "STARTUP"
  | "CONSULTING"
  | "CORE_ENGINEERING"
  | "GOVERNMENT";

export type CompanyTier =
  | "TIER_1_SUPER_DREAM"
  | "TIER_2_DREAM"
  | "TIER_3_MASS";

export interface CompanyContact {
  id: string;
  name: string;
  role: string;
  email: string;
  phone: string;
  isPrimary: boolean;
}

export interface Company {
  id: string;
  code: string;
  name: string;
  legalName?: string;
  industry: string;
  companyType: CompanyType;
  tier: CompanyTier;
  website: string;
  headquarters: string;
  locations: string[];
  contacts: CompanyContact[];
  status: CompanyStatus;
  activeDrivesCount: number;
  totalHiredCount: number;
  averageCtcLpa: number;
  highestCtcLpa: number;
  relationshipStatus: "NEW" | "LONG_STANDING" | "OCCASIONAL" | "ON_HOLD";
  notes?: string;
  createdAt: string;
  updatedAt: string;
  timeline: AuditEntry[];
}

// ==========================================
// 3. Job Drives
// ==========================================

export type DriveStatus =
  | "DRAFT"
  | "UPCOMING"
  | "OPEN"
  | "CLOSED"
  | "COMPLETED"
  | "CANCELLED";

export type DriveType =
  | "ON_CAMPUS"
  | "OFF_CAMPUS"
  | "VIRTUAL"
  | "POOLED";

export interface JobDrive {
  id: string;
  code: string;
  title: string;
  companyId: string;
  companyName: string;
  companyTier: CompanyTier;
  driveType: DriveType;
  driveDate: string;
  applicationDeadline: string;
  location: string;
  academicYear: string;
  batchGraduationYear: number;
  positionsCount: number;
  eligibleStudentsCount: number;
  applicantsCount: number;
  shortlistedCount: number;
  interviewsCount: number;
  offersCount: number;
  status: DriveStatus;
  description: string;
  guidelines?: string;
  createdAt: string;
  updatedAt: string;
  timeline: AuditEntry[];
}

// ==========================================
// 4. Job Positions
// ==========================================

export type PositionStatus = "OPEN" | "CLOSED" | "CANCELLED" | "FILLED";

export type EmploymentType = "FULL_TIME" | "INTERNSHIP" | "INTERN_PLUS_FTE";

export interface Position {
  id: string;
  driveId: string;
  driveCode: string;
  companyId: string;
  companyName: string;
  title: string;
  departmentFunction: string;
  employmentType: EmploymentType;
  location: string;
  vacancies: number;
  ctcLpa: number;
  baseSalaryLpa: number;
  variableLpa?: number;
  stipendMonthly?: number;
  bondMonths?: number;
  requiredSkills: string[];
  minCgpa: number;
  maxBacklogs: number;
  minAttendancePercent?: number;
  targetPrograms: string[];
  targetDepartments: string[];
  graduationYear: number;
  status: PositionStatus;
  description?: string;
  responsibilities?: string[];
  createdAt: string;
}

// ==========================================
// 5. Eligibility Rules & Snapshot
// ==========================================

export type EligibilityRuleType =
  | "PROGRAM"
  | "GRADUATION_YEAR"
  | "MIN_CGPA"
  | "MAX_BACKLOGS"
  | "MIN_ATTENDANCE"
  | "SKILLS"
  | "DEGREE";

export interface RuleEvaluationResult {
  rule: EligibilityRuleType;
  ruleName: string;
  required: string | number | string[];
  actual: string | number | string[];
  passed: boolean;
  message: string;
}

export type EligibilityStatus =
  | "ELIGIBLE"
  | "INELIGIBLE"
  | "CONDITIONALLY_ELIGIBLE"
  | "PENDING_REVIEW";

export interface EligibilitySnapshot {
  studentId: string;
  studentName: string;
  rollNumber: string;
  driveId: string;
  positionId: string;
  status: EligibilityStatus;
  rules: RuleEvaluationResult[];
  isOverridden?: boolean;
  overrideReason?: string;
  overriddenBy?: string;
  overriddenAt?: string;
  evaluatedAt: string;
}

// ==========================================
// 6. Applications & Shortlisting
// ==========================================

export type ApplicationStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "SHORTLISTED"
  | "REJECTED"
  | "WITHDRAWN"
  | "SELECTED";

export interface Application {
  id: string;
  applicationCode: string;
  driveId: string;
  driveName: string;
  positionId: string;
  positionTitle: string;
  companyId: string;
  companyName: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  department: string;
  cgpa: number;
  appliedDate: string;
  status: ApplicationStatus;
  currentStage: InterviewStage | "APPLICATION" | "OFFER" | "OUTCOME";
  eligibilityStatus: EligibilityStatus;
  rejectionReason?: string;
  resumeVersion?: string;
  internalNotes?: string;
  timeline: AuditEntry[];
}

// ==========================================
// 7. Interviews & Evaluations
// ==========================================

export type InterviewStage =
  | "SCREENING"
  | "APTITUDE"
  | "TECHNICAL"
  | "MANAGERIAL"
  | "HR"
  | "FINAL";

export type InterviewStatus =
  | "SCHEDULED"
  | "COMPLETED"
  | "RESCHEDULED"
  | "CANCELLED"
  | "NO_SHOW";

export interface InterviewEvaluation {
  technicalRating: number; // 1 to 5
  technicalSkillsRating?: number;
  communicationRating: number; // 1 to 5
  problemSolvingRating: number; // 1 to 5
  roleFitRating: number; // 1 to 5
  overallRecommendation: "STRONG_HIRE" | "HIRE" | "BORDERLINE" | "NO_HIRE";
  strengths?: string;
  areasOfImprovement?: string;
  evaluatedBy?: string;
  evaluatedAt?: string;
  notes?: string;
}

export interface Interview {
  id: string;
  interviewCode: string;
  applicationId: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  companyId: string;
  companyName: string;
  positionId: string;
  positionTitle: string;
  stage: InterviewStage;
  roundNumber: number;
  date: string;
  time: string;
  durationMinutes: number;
  mode: "ONLINE" | "IN_PERSON";
  locationOrMeetingUrl: string;
  interviewerName: string;
  interviewerEmail?: string;
  status: InterviewStatus;
  evaluation?: InterviewEvaluation;
  notes?: string;
  timeline: AuditEntry[];
}

// ==========================================
// 8. Offers & Acceptance
// ==========================================

export type OfferStatus =
  | "DRAFT"
  | "RELEASED"
  | "ACCEPTED"
  | "DECLINED"
  | "EXPIRED"
  | "WITHDRAWN";

export interface Offer {
  id: string;
  offerCode: string;
  applicationId: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  companyId: string;
  companyName: string;
  positionId: string;
  positionTitle: string;
  employmentType: EmploymentType;
  location: string;
  ctcLpa: number;
  baseSalaryLpa: number;
  variableLpa?: number;
  stipendMonthly?: number;
  offerDate: string;
  responseDeadline: string;
  joiningDate: string;
  status: OfferStatus;
  responseNotes?: string;
  releasedBy: string;
  timeline: AuditEntry[];
}

// ==========================================
// 9. Placement Outcomes
// ==========================================

export type PlacementStatus =
  | "NOT_PLACED"
  | "IN_PROCESS"
  | "PLACED"
  | "WITHDRAWN"
  | "DEFERRED";

export interface PlacementOutcome {
  id: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  department: string;
  graduationYear: number;
  companyId: string;
  companyName: string;
  positionId: string;
  positionTitle: string;
  offerId: string;
  ctcLpa: number;
  joiningDate: string;
  placementYear: string;
  status: PlacementStatus;
  confirmedAt: string;
  confirmedBy: string;
  notes?: string;
  timeline: AuditEntry[];
}

// ==========================================
// 10. Dashboard & Reports
// ==========================================

export interface DepartmentPlacementStat {
  department: string;
  totalStudents: number;
  placedStudents: number;
  placementRate: number;
  averageCtcLpa: number;
  highestCtcLpa: number;
}

export interface PackageDistributionBucket {
  range: string;
  minLpa: number;
  maxLpa: number;
  count: number;
  percentage: number;
}

export interface FunnelMetric {
  stage: string;
  count: number;
  percentage: number;
}

export interface PlacementDashboardSummary {
  activeCompaniesCount: number;
  openDrivesCount: number;
  eligibleStudentsCount: number;
  applicationsCount: number;
  shortlistedCount: number;
  interviewsCount: number;
  offersCount: number;
  placedStudentsCount: number;
  placementRate: number;
  offerRate: number;
  applicationConversionRate: number;
  shortlistRate: number;
  averagePackageLpa: number;
  highestPackageLpa: number;
  medianPackageLpa: number;
  departmentStats: DepartmentPlacementStat[];
  packageDistribution: PackageDistributionBucket[];
  funnelMetrics: FunnelMetric[];
  operationalQueues: {
    upcomingDrivesCount: number;
    eligibilityReviewsCount: number;
    pendingApplicationsCount: number;
    interviewsTodayCount: number;
    offersAwaitingResponseCount: number;
    recentPlacementsCount: number;
  };
  recentActivities: {
    id: string;
    title: string;
    description: string;
    timestamp: string;
    type: "DRIVE" | "APPLICATION" | "SHORTLIST" | "INTERVIEW" | "OFFER" | "PLACEMENT";
    href: string;
  }[];
}

export type PlacementReportType =
  | "SUMMARY"
  | "DEPARTMENT"
  | "COMPANY"
  | "PACKAGES"
  | "STATUS";

export interface PlacementReportFilter {
  reportType: PlacementReportType;
  department?: string;
  program?: string;
  graduationYear?: number;
  companyId?: string;
  status?: string;
}

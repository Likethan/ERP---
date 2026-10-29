/**
 * CampusOS Attendance Management Domain Types
 * Canonical types for Attendance Policies, Sessions, Records, Student & Course Summaries,
 * Leaves, Corrections, Analytics, and Reports.
 */

// ==========================================
// 1. Status & Core Enums
// ==========================================

export type AttendanceStatus = "PRESENT" | "ABSENT" | "LATE" | "EXCUSED";

export type AttendanceSessionStatus =
  "SCHEDULED" | "OPEN" | "COMPLETED" | "CANCELLED";

export type AttendanceRiskLevel = "HEALTHY" | "WARNING" | "CRITICAL";

export type LeaveType =
  "MEDICAL" | "ON_DUTY" | "CASUAL" | "SPORTS" | "ACADEMIC";

export type AttendanceLeaveStatus =
  "DRAFT" | "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";

export type AttendanceCorrectionStatus =
  "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";

export type SessionType = "THEORY" | "LAB" | "TUTORIAL" | "SEMINAR";

// ==========================================
// 2. Attendance Policy Types
// ==========================================

export interface AttendancePolicy {
  id: string;
  name: string;
  departmentId: string;
  departmentName: string;
  academicYear: string;
  minimumPercentage: number; // e.g. 75%
  warningThreshold: number; // e.g. 80%
  criticalThreshold: number; // e.g. 65%
  includeExcusedInTotal: boolean;
  lateArrivalWeight: number; // e.g. 0.5 (half present) or 1.0 (full present) or 0
  requireApprovalForCorrections: boolean;
  maxLeaveDaysConsecutive: number;
  status: "ACTIVE" | "INACTIVE";
}

// ==========================================
// 3. Attendance Session Types
// ==========================================

export interface AttendanceSession {
  id: string;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  section: string;
  department: string;
  facultyId: string;
  facultyName: string;
  date: string; // YYYY-MM-DD
  startTime: string; // e.g. "09:30 AM"
  endTime: string; // e.g. "10:30 AM"
  room: string;
  sessionType: SessionType;
  status: AttendanceSessionStatus;
  totalStudents: number;
  presentCount: number;
  absentCount: number;
  lateCount: number;
  excusedCount: number;
  attendancePercentage: number;
  topicCovered?: string;
  remarks?: string;
  createdAt: string;
  submittedAt?: string;
}

// ==========================================
// 4. Attendance Record Types
// ==========================================

export interface AttendanceRecord {
  id: string;
  sessionId: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  section: string;
  status: AttendanceStatus;
  remarks?: string;
  markedAt: string;
  markedBy: string;
}

// ==========================================
// 5. Student & Course Attendance Summaries
// ==========================================

export interface AttendanceCourseSummary {
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  section: string;
  facultyName: string;
  totalSessions: number;
  presentCount: number;
  absentCount: number;
  lateCount: number;
  excusedCount: number;
  percentage: number;
  riskLevel: AttendanceRiskLevel;
  studentsBelowThresholdCount?: number;
  studentsAtRiskCount?: number;
  averageAttendance?: number;
}

export interface AttendanceWeeklyTrend {
  period: string; // e.g. "Week 1", "Week 2"
  percentage: number;
  present: number;
  total: number;
}

export interface AttendanceStudentSummary {
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  department: string;
  semester: number;
  section: string;
  totalSessions: number;
  attendedSessions: number;
  presentCount: number;
  absentCount: number;
  lateCount: number;
  excusedCount: number;
  percentage: number;
  riskLevel: AttendanceRiskLevel;
  courseSummaries: AttendanceCourseSummary[];
  trend: AttendanceWeeklyTrend[];
}

export interface LowAttendanceAlertItem {
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  department: string;
  semester: number;
  section: string;
  courseCode: string;
  courseName: string;
  attendancePercentage: number;
  requiredPercentage: number;
  sessionsAttended: number;
  totalSessions: number;
  sessionsNeededToRecover: number;
  riskLevel: AttendanceRiskLevel;
}

// ==========================================
// 6. Leave Request Types
// ==========================================

export interface AttendanceLeave {
  id: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  department: string;
  program: string;
  section: string;
  leaveType: LeaveType;
  startDate: string;
  endDate: string;
  totalDays: number;
  reason: string;
  supportingDocUrl?: string;
  supportingDocName?: string;
  status: AttendanceLeaveStatus;
  requestedAt: string;
  reviewedBy?: string;
  reviewedAt?: string;
  rejectionReason?: string;
}

// ==========================================
// 7. Attendance Correction Types
// ==========================================

export interface CorrectionAuditStep {
  timestamp: string;
  action: string;
  actor: string;
  details?: string;
}

export interface AttendanceCorrection {
  id: string;
  recordId: string;
  sessionId: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  courseCode: string;
  courseName: string;
  sessionDate: string;
  originalStatus: AttendanceStatus;
  requestedStatus: AttendanceStatus;
  reason: string;
  requestedBy: string;
  requestedRole: "FACULTY" | "STUDENT" | "HOD";
  requestedAt: string;
  reviewedBy?: string;
  reviewedAt?: string;
  status: AttendanceCorrectionStatus;
  auditTimeline: CorrectionAuditStep[];
}

// ==========================================
// 8. Operations Dashboard Summary
// ==========================================

export interface AttendanceSummary {
  overallAttendancePercentage: number;
  totalSessionsConducted: number;
  todaySessionsCount: number;
  todaySessionsCompleted: number;
  todaySessionsPending: number;
  studentsBelowThresholdCount: number;
  studentsAtRiskCount: number;
  pendingLeaveRequestsCount: number;
  pendingCorrectionsCount: number;
  lowAttendanceCoursesCount: number;
  departmentBreakdown: {
    department: string;
    percentage: number;
    studentCount: number;
  }[];
  semesterBreakdown: {
    semester: number;
    percentage: number;
    studentCount: number;
  }[];
}

// ==========================================
// 9. Report Types
// ==========================================

export type AttendanceReportType =
  | "STUDENT"
  | "COURSE"
  | "DEPARTMENT"
  | "SEMESTER"
  | "LOW_ATTENDANCE"
  | "FACULTY_SESSION";

export interface AttendanceReportFilter {
  reportType: AttendanceReportType;
  startDate?: string;
  endDate?: string;
  department?: string;
  program?: string;
  semester?: number;
  section?: string;
  courseCode?: string;
  facultyName?: string;
  riskLevel?: AttendanceRiskLevel;
}

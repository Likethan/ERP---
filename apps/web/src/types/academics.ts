/**
 * CampusOS Academic Management Domain Types
 * Canonical types for Subjects, Curricula, Course Offerings, Faculty Allocations,
 * Student Enrollments, Timetable Scheduling, and Conflict Analytics.
 */

// ==========================================
// 1. Subject Types
// ==========================================

export type SubjectType =
  | "THEORY"
  | "PRACTICAL"
  | "LAB"
  | "PROJECT"
  | "INTERNSHIP"
  | "SEMINAR"
  | "ELECTIVE"
  | "OTHER";

export type SubjectStatus = "DRAFT" | "ACTIVE" | "INACTIVE" | "ARCHIVED";

export type SubjectCategory =
  | "CORE"
  | "PROFESSIONAL_ELECTIVE"
  | "OPEN_ELECTIVE"
  | "BASIC_SCIENCES"
  | "HUMANITIES"
  | "ENGINEERING_SCIENCES"
  | "MANDATORY_NON_CREDIT";

export interface AcademicSubject {
  id: string;
  code: string;
  name: string;
  shortName: string;
  departmentId: string;
  departmentName: string;
  credits: number;
  lectureHours: number;
  tutorialHours: number;
  practicalHours: number;
  type: SubjectType;
  category: SubjectCategory;
  description?: string;
  syllabusUrl?: string;
  prerequisites?: string[];
  status: SubjectStatus;
  curriculumCount?: number;
  offeringsCount?: number;
}

// ==========================================
// 2. Curriculum & Versioning Types
// ==========================================

export type CurriculumStatus =
  | "DRAFT"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "PUBLISHED"
  | "RETIRED";

export interface CurriculumSubject {
  id: string;
  subjectId: string;
  subjectCode: string;
  subjectName: string;
  credits: number;
  type: SubjectType;
  category: SubjectCategory;
  lectureHours: number;
  tutorialHours: number;
  practicalHours: number;
  isElective?: boolean;
  electiveGroupId?: string;
}

export interface ElectiveGroup {
  id: string;
  name: string;
  code: string;
  minSelect: number;
  maxSelect: number;
  subjects: CurriculumSubject[];
}

export interface CurriculumSemester {
  semesterNumber: number;
  totalCredits: number;
  subjects: CurriculumSubject[];
  electiveGroups?: ElectiveGroup[];
}

export interface CurriculumVersionHistory {
  version: string;
  date: string;
  author: string;
  notes: string;
  status: CurriculumStatus;
}

export interface CurriculumScheme {
  id: string;
  programId: string;
  programName: string;
  programCode: string;
  department: string;
  regulation: string; // e.g. "R-2024", "R-2025", "R-2026"
  version: string;    // e.g. "v1.0", "v2.1"
  academicYear: string;
  effectiveDate: string;
  totalCredits: number;
  totalSemesters: number;
  status: CurriculumStatus;
  isActiveVersion: boolean;
  semesters: CurriculumSemester[];
  versionHistory: CurriculumVersionHistory[];
}

// ==========================================
// 3. Course Offering & Faculty Allocation Types
// ==========================================

export type CourseOfferingStatus =
  | "PLANNED"
  | "OPEN"
  | "ACTIVE"
  | "COMPLETED"
  | "CANCELLED";

export type FacultyAssignmentRole =
  | "PRIMARY_INSTRUCTOR"
  | "CO_INSTRUCTOR"
  | "LAB_INSTRUCTOR";

export interface CourseFacultyAssignment {
  id: string;
  facultyId: string;
  facultyName: string;
  employeeCode: string;
  email: string;
  role: FacultyAssignmentRole;
  assignedWeeklyHours: number;
  status: "CONFIRMED" | "TENTATIVE";
}

export interface CourseOfferingDetail {
  id: string;
  subjectId: string;
  subjectCode: string;
  subjectName: string;
  programId: string;
  programName: string;
  department: string;
  academicYear: string;
  semester: number;
  section: string;
  credits: number;
  type: SubjectType;
  lectureHours: number;
  labHours: number;
  facultyAssignments: CourseFacultyAssignment[];
  enrolledCount: number;
  maxCapacity: number;
  status: CourseOfferingStatus;
  syllabusCoveragePercentage?: number;
}

// ==========================================
// 4. Student Course Enrollment Types
// ==========================================

export type CourseEnrollmentStatus =
  | "PENDING"
  | "ENROLLED"
  | "DROPPED"
  | "COMPLETED"
  | "WITHDRAWN";

export interface StudentCourseEnrollmentRecord {
  id: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  department: string;
  academicYear: string;
  semester: number;
  section: string;
  courseOfferingId: string;
  subjectCode: string;
  subjectName: string;
  credits: number;
  isElective: boolean;
  electiveGroup?: string;
  status: CourseEnrollmentStatus;
  enrolledDate: string;
  attendanceRate?: number;
}

// ==========================================
// 5. Timetable & Conflict Engine Types
// ==========================================

export type DayOfWeek =
  | "MONDAY"
  | "TUESDAY"
  | "WEDNESDAY"
  | "THURSDAY"
  | "FRIDAY"
  | "SATURDAY";

export interface MasterTimeSlot {
  id: string;
  periodNumber: number;
  startTime: string; // "08:30 AM"
  endTime: string;   // "09:20 AM"
  label: string;     // "Period 1"
  isBreak?: boolean;
}

export interface ScheduledTimetableEntry {
  id: string;
  courseOfferingId: string;
  subjectCode: string;
  subjectName: string;
  facultyId: string;
  facultyName: string;
  department: string;
  semester: number;
  section: string;
  roomNumber: string;
  building: string;
  day: DayOfWeek;
  timeSlotId: string;
  startTime: string;
  endTime: string;
  entryType: "THEORY" | "LAB" | "TUTORIAL" | "SEMINAR";
}

export type TimetableConflictType =
  | "FACULTY_CONFLICT"
  | "SECTION_CONFLICT"
  | "ROOM_CONFLICT";

export interface TimetableConflict {
  id: string;
  conflictType: TimetableConflictType;
  severity: "ERROR" | "WARNING";
  title: string;
  description: string;
  conflictingEntryIds: string[];
  day: DayOfWeek;
  timeSlot: string;
  resourceName: string; // Faculty Name, Room number, or Section
}

// ==========================================
// 6. Academic Operations Aggregates
// ==========================================

export interface AcademicOperationsSummary {
  activeAcademicYear: string;
  currentSemester: number;
  totalDepartments: number;
  totalPrograms: number;
  totalSections: number;
  activeSubjectsCount: number;
  activeOfferingsCount: number;
  enrolledStudentsCount: number;
  assignedFacultyCount: number;
  unassignedOfferingsCount: number;
  timetableConflictsCount: number;
  activeCurriculaCount: number;
}

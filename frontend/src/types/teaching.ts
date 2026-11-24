export type TeachingMethod =
  | "CHALK_AND_BOARD"
  | "POWERPOINT_ICT"
  | "LAB_DEMONSTRATION"
  | "GROUP_DISCUSSION"
  | "PROBLEM_SOLVING"
  | "SEMINAR_PRESENTATION";

export type LessonPlanStatus = "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";

export interface LessonPlanUnit {
  id: string;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  section: string;
  unitNumber: number;
  unitTitle: string;
  plannedHours: number;
  completedHours: number;
  topics: string[];
  learningOutcomes: string;
  status: LessonPlanStatus;
  completionPercentage: number;
  lastUpdated: string;
}

export interface ClassDiaryEntry {
  id: string;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  section: string;
  facultyId: string;
  facultyName: string;
  date: string;
  timeSlot: string;
  periodNumber: number;
  unitNumber: number;
  unitTitle: string;
  topicsCovered: string;
  teachingMethod: TeachingMethod;
  studentsPresent: number;
  totalStudents: number;
  attendancePercentage: number;
  remarks: string;
  verifiedByHod: boolean;
  createdAt: string;
}

export type MaterialFileType =
  "PDF" | "DOCX" | "PPT" | "LINK" | "VIDEO" | "CODE";

export interface CourseStudyMaterial {
  id: string;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  section: string;
  unitNumber: number;
  title: string;
  description: string;
  materialType: MaterialFileType;
  fileUrl: string;
  fileName: string;
  fileSize: string;
  uploadedByFacultyId: string;
  uploadedByFacultyName: string;
  uploadedAt: string;
  downloadCount: number;
}

export type AssignmentStatus = "DRAFT" | "PUBLISHED" | "CLOSED";
export type SubmissionFormat = "PDF" | "DOCX" | "ZIP" | "CODE" | "TEXT";
export type SubmissionStatus =
  "SUBMITTED" | "EVALUATED" | "RESUBMISSION_REQUESTED";

export interface CourseAssignment {
  id: string;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  section: string;
  title: string;
  description: string;
  unitNumber: number;
  assignedDate: string;
  dueDate: string;
  maxMarks: number;
  weightagePercent: number;
  submissionFormat: SubmissionFormat;
  allowLateSubmission: boolean;
  lateSubmissionDeadline?: string;
  latePenaltyPercent?: number;
  status: AssignmentStatus;
  totalSubmissions: number;
  totalEnrolled: number;
  evaluatedCount: number;
  averageScore?: number;
  createdByFacultyId: string;
  createdByFacultyName: string;
}

export interface AssignmentSubmission {
  id: string;
  assignmentId: string;
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  studentId: string;
  studentName: string;
  studentRoll: string;
  submittedAt: string;
  isLate: boolean;
  submissionFileUrl?: string;
  submissionFileName?: string;
  submissionText?: string;
  status: SubmissionStatus;
  marksObtained?: number;
  maxMarks: number;
  feedback?: string;
  evaluatedByFacultyId?: string;
  evaluatedByFacultyName?: string;
  evaluatedAt?: string;
}

export type FacultyLeaveType =
  "CASUAL" | "MEDICAL" | "ON_DUTY" | "EARNED" | "SPECIAL_CASUAL";

export type FacultyLeaveStatus =
  "PENDING_HOD" | "APPROVED" | "REJECTED" | "CANCELLED";

export interface FacultyLeaveApplication {
  id: string;
  facultyId: string;
  facultyName: string;
  employeeCode: string;
  department: string;
  leaveType: FacultyLeaveType;
  startDate: string;
  endDate: string;
  totalDays: number;
  reason: string;
  substituteFacultyId: string;
  substituteFacultyName: string;
  substituteClassesArranged: boolean;
  status: FacultyLeaveStatus;
  hodRemarks?: string;
  appliedAt: string;
}

export interface FacultyLeaveBalance {
  leaveType: FacultyLeaveType;
  label: string;
  allocatedDays: number;
  consumedDays: number;
  availableDays: number;
}

/**
 * CampusOS People Domain Types
 * Canonical types for Students, Faculty, Staff, Guardians, Documents, Milestones, and Workload.
 */

// ==========================================
// 1. Common & Shared Types
// ==========================================

export type Gender = "Male" | "Female" | "Other";

export interface AddressInfo {
  street: string;
  city: string;
  state: string;
  pincode: string;
  country?: string;
}

// ==========================================
// 2. Student & Guardian Types
// ==========================================

export type StudentStatus =
  | "ACTIVE"
  | "ADMITTED"
  | "SUSPENDED"
  | "GRADUATED"
  | "ON_LEAVE"
  | "WITHDRAWN";

export type AdmissionQuota = "MERIT" | "MANAGEMENT" | "SPORTS" | "GOVERNMENT";

export type GuardianRelationType =
  | "FATHER"
  | "MOTHER"
  | "GUARDIAN"
  | "SIBLING"
  | "EMERGENCY_CONTACT"
  | "OTHER";

export interface GuardianRecord {
  id: string;
  name: string;
  relation: GuardianRelationType;
  relationLabel?: string;
  phone: string;
  email: string;
  occupation: string;
  annualIncome?: string;
  isPrimary: boolean;
  isEmergencyContact: boolean;
  address?: AddressInfo;
}

export type DocumentCategory =
  | "IDENTITY"
  | "ACADEMIC"
  | "ADMISSION"
  | "FINANCIAL"
  | "PLACEMENT"
  | "MEDICAL"
  | "CERTIFICATES"
  | "OTHER";

export type DocumentVerificationStatus =
  | "MISSING"
  | "UPLOADED"
  | "UNDER_REVIEW"
  | "VERIFIED"
  | "REJECTED"
  | "EXPIRED";

export interface PersonDocument {
  id: string;
  name: string;
  category: DocumentCategory;
  fileSize: string;
  mimeType?: string;
  fileUrl?: string;
  uploadedAt: string;
  uploadedBy: string;
  status: DocumentVerificationStatus;
  verifiedAt?: string;
  verifiedBy?: string;
  rejectionReason?: string;
  expiryDate?: string;
}

export type MilestoneCategory =
  | "ADMISSION"
  | "ENROLLMENT"
  | "SEMESTER_PROGRESSION"
  | "ACHIEVEMENT"
  | "INTERNSHIP"
  | "PLACEMENT"
  | "GRADUATION";

export type MilestoneStatus = "COMPLETED" | "IN_PROGRESS" | "UPCOMING";

export interface AcademicMilestone {
  id: string;
  title: string;
  category: MilestoneCategory;
  date: string;
  semester?: number;
  description: string;
  status: MilestoneStatus;
  awardedBy?: string;
  certificateRef?: string;
}

// ==========================================
// 3. Faculty, Workload & Research Types
// ==========================================

export type FacultyStatus = "ACTIVE" | "ON_LEAVE" | "SABBATICAL" | "RESIGNED";

export type WorkloadAllocationStatus = "UNDER_ALLOCATED" | "BALANCED" | "HIGH_ALLOCATION";

export interface FacultyCourseAssignment {
  id: string;
  code: string;
  name: string;
  semester: number;
  section: string;
  studentCount: number;
  lectureHours: number;
  labHours: number;
  credits: number;
}

export interface LabDesignationItem {
  id: string;
  labName: string;
  courseCode: string;
  courseName: string;
  section: string;
  dayOfWeek: string;
  timeSlot: string;
  roomNumber: string;
  weeklyHours: number;
  batchCapacity: number;
}

export type PublicationType =
  | "JOURNAL"
  | "CONFERENCE"
  | "BOOK_CHAPTER"
  | "PATENT"
  | "WORKSHOP"
  | "OTHER";

export type PublicationStatus = "DRAFT" | "SUBMITTED" | "ACCEPTED" | "PUBLISHED";

export interface FacultyPublication {
  id: string;
  title: string;
  publicationType: PublicationType;
  venueName: string; // Journal or Conference name
  publicationYear: number;
  authors: string[];
  doi?: string;
  status: PublicationStatus;
  citationCount?: number;
  url?: string;
  abstractSummary?: string;
}

export interface FacultyWorkloadSummary {
  facultyId: string;
  academicYear: string;
  semester: number;
  totalAssignedHours: number;
  lectureHours: number;
  labHours: number;
  preparationHours: number;
  weeklyTargetHours: number;
  status: WorkloadAllocationStatus;
  assignments: FacultyCourseAssignment[];
  labDesignations: LabDesignationItem[];
}

// ==========================================
// 4. Non-Teaching Staff & Shift Types
// ==========================================

export type StaffStatus = "ACTIVE" | "ON_LEAVE" | "RESIGNED";

export type StaffShiftType = "MORNING" | "GENERAL" | "EVENING" | "NIGHT" | "CUSTOM";

export interface StaffShiftItem {
  id: string;
  shiftCode: string;
  shiftName: string;
  shiftType: StaffShiftType;
  startTime: string; // e.g. "08:00 AM"
  endTime: string;   // e.g. "04:30 PM"
  assignedStaffCount: number;
  department: string;
  description?: string;
}

export type StaffLeaveType =
  | "CASUAL"
  | "SICK"
  | "EARNED"
  | "DUTY"
  | "MATERNITY"
  | "PATERNITY"
  | "COMPENSATORY";

export type StaffLeaveStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";

export interface StaffLeaveRequest {
  id: string;
  staffId: string;
  staffName: string;
  department: string;
  leaveType: StaffLeaveType;
  startDate: string;
  endDate: string;
  totalDays: number;
  reason: string;
  status: StaffLeaveStatus;
  requestedAt: string;
  reviewedBy?: string;
  reviewedAt?: string;
  reviewRemarks?: string;
}

// ==========================================
// 5. People Hub & Aggregation Metrics
// ==========================================

export interface PeopleSummaryMetrics {
  totalStudents: number;
  activeStudents: number;
  recentlyAdmittedStudents: number;
  graduatingStudents: number;
  totalFaculty: number;
  activeFaculty: number;
  phdFacultyCount: number;
  totalStaff: number;
  activeStaff: number;
  staffOnDutyToday: number;
  pendingLeaveApprovals: number;
  pendingDocumentVerifications: number;
  totalDepartments: number;
  totalPrograms: number;
}

export interface DepartmentPeopleDistribution {
  departmentId: string;
  departmentName: string;
  departmentCode: string;
  studentCount: number;
  facultyCount: number;
  staffCount: number;
  hodName: string;
}

export interface UnifiedPersonSearchResult {
  id: string;
  name: string;
  personType: "STUDENT" | "FACULTY" | "STAFF";
  code: string; // Roll number or Employee Code
  email: string;
  phone: string;
  department: string;
  designationOrProgram: string;
  status: string;
  avatarUrl?: string;
  href: string;
}

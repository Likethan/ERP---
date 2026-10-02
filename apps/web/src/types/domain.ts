/**
 * CampusOS Unified Domain Types & View Models
 * "One Campus. One System. One Source of Truth."
 */

export * from "@campusos/types";
export * from "./people";
export * from "./campus";
export * from "./infrastructure";
export type { EventCategory, EventStatus, NotificationItem } from "./campus";
import {
  GuardianRecord,
  PersonDocument,
  AcademicMilestone,
  FacultyWorkloadSummary,
  LabDesignationItem,
  FacultyPublication,
  StaffShiftItem,
  StaffLeaveRequest,
} from "./people";

// Additional frontend domain entities and view-models
export type RoleName =
  | "SUPER_ADMIN"
  | "ADMIN"
  | "PRINCIPAL"
  | "HOD"
  | "FACULTY"
  | "ACCOUNTS"
  | "PLACEMENT_OFFICER"
  | "STUDENT"
  | "PARENT"
  | "STAFF"
  | "WARDEN"
  | "TRANSPORT_OFFICER"
  | "FACILITY_OFFICER";

export interface DemoPersona {
  id: string;
  name: string;
  email: string;
  role: RoleName;
  roleTitle: string;
  department?: string;
  avatarInitials: string;
  description: string;
  permissions: string[];
}

export interface StudentComprehensiveDetail {
  id: string;
  rollNumber: string;
  registrationNumber: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  gender: string;
  dateOfBirth: string;
  bloodGroup: string;
  status: "ACTIVE" | "ADMITTED" | "SUSPENDED" | "GRADUATED" | "ON_LEAVE" | "WITHDRAWN";
  admissionDate: string;
  program: {
    id: string;
    code: string;
    name: string;
    department: string;
  };
  academicYear: string;
  currentSemester: number;
  section: string;
  batch: string;
  quota: "MERIT" | "MANAGEMENT" | "SPORTS" | "GOVERNMENT";
  address: {
    street: string;
    city: string;
    state: string;
    pincode: string;
  };
  guardian: {
    name: string;
    relation: string;
    phone: string;
    email: string;
    occupation: string;
  };
  academicStats: {
    cgpa: number;
    totalCreditsEarned: number;
    backlogs: number;
    rank: number;
  };
  attendanceSummary: {
    overallPercentage: number;
    totalClasses: number;
    attendedClasses: number;
    status: "EXCELLENT" | "SATISFACTORY" | "CRITICAL";
  };
  financeSummary: {
    totalBilled: number;
    totalPaid: number;
    pendingDue: number;
    status: "CLEAR" | "PENDING_DUES" | "SCHOLARSHIP_HOLD";
  };
  placementSummary: {
    isEligible: boolean;
    appliedDrives: number;
    interviewsScheduled: number;
    offersReceived: number;
    highestPackageLPA?: number;
  };
  hostel?: {
    hostelName: string;
    block: string;
    roomNumber: string;
    bed: string;
  };
  transport?: {
    routeName: string;
    routeCode: string;
    stopName: string;
    busNumber: string;
  };
  enrolledCourses: Array<{
    id: string;
    code: string;
    title: string;
    faculty: string;
    credits: number;
    attendanceRate: number;
    internalMarks: number;
  }>;
  recentActivity: Array<{
    id: string;
    action: string;
    timestamp: string;
    domain: string;
    actor: string;
  }>;
  documents: Array<{
    id: string;
    name: string;
    category: string;
    uploadDate: string;
    fileSize: string;
    verified: boolean;
  }>;
  guardians?: GuardianRecord[];
  documentsVault?: PersonDocument[];
  milestones?: AcademicMilestone[];
}

export interface FacultyDetailView {
  id: string;
  employeeCode: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  designation: string;
  department: string;
  qualification: string;
  specialization: string;
  joiningDate: string;
  status: "ACTIVE" | "ON_LEAVE" | "SABBATICAL" | "RESIGNED";
  teachingLoadHours: number;
  assignedSubjects: Array<{
    id: string;
    code: string;
    name: string;
    semester: number;
    section: string;
    studentCount: number;
  }>;
  todayClasses: Array<{
    time: string;
    subject: string;
    room: string;
    section: string;
    attendanceMarked: boolean;
  }>;
  stats: {
    coursesCount: number;
    totalStudents: number;
    averageAttendance: number;
    pendingCorrections: number;
  };
  workloadSummary?: FacultyWorkloadSummary;
  labDesignations?: LabDesignationItem[];
  publications?: FacultyPublication[];
}

export interface StaffDetailView {
  id: string;
  employeeCode: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  department: string;
  role: string;
  designation?: string;
  employmentType?: "PERMANENT" | "CONTRACT" | "PROBATION";
  joiningDate: string;
  status: "ACTIVE" | "ON_LEAVE" | "RESIGNED";
  shift?: StaffShiftItem;
  leaveBalance?: {
    casual: number;
    sick: number;
    earned: number;
  };
  leaves?: StaffLeaveRequest[];
}

export interface CourseOfferingDetail {
  id: string;
  subjectCode: string;
  subjectName: string;
  credits: number;
  department: string;
  academicYear: string;
  semester: number;
  section: string;
  primaryFaculty: {
    id: string;
    name: string;
    email: string;
  };
  studentEnrollmentCount: number;
  status: "ACTIVE" | "COMPLETED" | "DRAFT";
  schedule: Array<{
    day: string;
    time: string;
    room: string;
  }>;
}

export interface GlobalSearchResultItem {
  id: string;
  title: string;
  subtitle: string;
  category:
    | "Student"
    | "Faculty"
    | "Staff"
    | "Course"
    | "Curriculum"
    | "Offering"
    | "Attendance"
    | "Examination"
    | "Assessment"
    | "Drive"
    | "Placement"
    | "Company"
    | "Offer"
    | "Application"
    | "Interview"
    | "Invoice"
    | "Finance"
    | "Payment"
    | "Receipt"
    | "Scholarship"
    | "Document"
    | "Event"
    | "Campus"
    | "Club"
    | "Announcement"
    | "Infrastructure";
  href: string;
  badge?: string;
}

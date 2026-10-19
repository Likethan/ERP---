/**
 * CampusOS Core Shared Type Definitions
 * "One Campus. One System. One Source of Truth."
 */

export type UUID = string;

/**
 * Supported User Roles in CampusOS
 */
export enum UserRole {
  SUPER_ADMIN = "SUPER_ADMIN",
  PRINCIPAL = "PRINCIPAL",
  HOD = "HOD",
  FACULTY = "FACULTY",
  ACCOUNTS = "ACCOUNTS",
  PLACEMENT_OFFICER = "PLACEMENT_OFFICER",
  STUDENT = "STUDENT",
  PARENT = "PARENT",
  STAFF = "STAFF",
  WARDEN = "WARDEN",
  TRANSPORT_OFFICER = "TRANSPORT_OFFICER",
  FACILITY_OFFICER = "FACILITY_OFFICER",
}

/**
 * Core Domains within the CampusOS Modular Monolith
 */
export enum DomainName {
  CORE = "core",
  PEOPLE = "people",
  ACADEMICS = "academics",
  ATTENDANCE = "attendance",
  EXAMINATION = "examination",
  FINANCE = "finance",
  PLACEMENT = "placement",
  CAMPUS = "campus",
  INFRASTRUCTURE = "infrastructure",
  DOCUMENTS = "documents",
  INTELLIGENCE = "intelligence",
}

/**
 * Standard Tenant Context for multi-tenancy isolation
 */
export interface TenantContext {
  tenantId: UUID;
  institutionCode: string;
  name: string;
  isActive: boolean;
}

/**
 * Standard API Envelope for REST responses
 */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string | { code?: string; message: string; details?: unknown };
  meta?: {
    timestamp?: string;
    requestId?: string;
    [key: string]: unknown;
  };
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  page: number;
  pageSize?: number;
  page_size?: number;
  totalRecords?: number;
  total_records?: number;
  totalPages?: number;
  total_pages?: number;
  hasNext?: boolean;
  has_next?: boolean;
  hasPrev?: boolean;
  has_prev?: boolean;
}

/**
 * Standard Paginated API Envelope
 */
export interface PaginatedResponse<T> {
  success: true;
  data: T[];
  pagination: PaginationMeta;
  meta?: {
    timestamp: string;
    requestId?: string;
  };
}

/**
 * Standard API Error Detail
 */
export interface ApiErrorDetail {
  field?: string;
  message: string;
  code?: string;
}

/**
 * Standard API Error Envelope for all failed REST responses
 */
export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: ApiErrorDetail[];
    requestId?: string;
    timestamp: string;
  };
}

/**
 * Health Check Payload
 */
export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy";
  service: string;
  version: string;
  timestamp: string;
  environment: string;
}

/**
 * Lifecycle state machines across domains
 */
export enum StudentLifecycleStatus {
  APPLIED = "APPLIED",
  ADMITTED = "ADMITTED",
  ACTIVE = "ACTIVE",
  SUSPENDED = "SUSPENDED",
  ON_LEAVE = "ON_LEAVE",
  GRADUATED = "GRADUATED",
  WITHDRAWN = "WITHDRAWN",
  ALUMNI = "ALUMNI",
}

export enum AttendanceRecordStatus {
  PRESENT = "PRESENT",
  ABSENT = "ABSENT",
  LATE = "LATE",
  EXCUSED = "EXCUSED",
  ON_LEAVE = "ON_LEAVE",
  ON_DUTY = "ON_DUTY",
}

export enum AttendanceSessionStatus {
  SCHEDULED = "SCHEDULED",
  OPEN = "OPEN",
  MARKED = "MARKED",
  SUBMITTED = "SUBMITTED",
  LOCKED = "LOCKED",
  CANCELLED = "CANCELLED",
}

export enum LeaveRequestStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  CANCELLED = "CANCELLED",
}

export enum CorrectionRequestStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
}

export enum ExamPublicationStatus {
  DRAFT = "DRAFT",
  REVIEW = "REVIEW",
  APPROVED = "APPROVED",
  PUBLISHED = "PUBLISHED",
}

export enum InvoiceStatus {
  DRAFT = "DRAFT",
  ISSUED = "ISSUED",
  PARTIALLY_PAID = "PARTIALLY_PAID",
  PAID = "PAID",
  OVERDUE = "OVERDUE",
  CANCELLED = "CANCELLED",
}

export enum PaymentStatus {
  INITIATED = "INITIATED",
  PENDING = "PENDING",
  SUCCESS = "SUCCESS",
  FAILED = "FAILED",
  REVERSED = "REVERSED",
  CANCELLED = "CANCELLED",
  REFUNDED = "REFUNDED",
  PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED",
}

export enum PlacementApplicationStatus {
  APPLIED = "APPLIED",
  ELIGIBLE = "ELIGIBLE",
  INELIGIBLE = "INELIGIBLE",
  SHORTLISTED = "SHORTLISTED",
  IN_SELECTION = "IN_SELECTION",
  OFFERED = "OFFERED",
  REJECTED = "REJECTED",
  WITHDRAWN = "WITHDRAWN",
}

export enum HostelAllocationStatus {
  ALLOCATED = "ALLOCATED",
  VACATED = "VACATED",
  CANCELLED = "CANCELLED",
}

/**
 * Authentication and IAM Interfaces
 */
export interface AuthRoleInfo {
  id: UUID;
  name: string;
  displayName: string;
  campusId?: UUID | null;
  departmentId?: UUID | null;
}

export interface AuthTenantInfo {
  id: UUID;
  code: string;
  name: string;
}

export interface AuthenticatedUser {
  id: UUID;
  email: string;
  first_name: string;
  last_name: string;
  name?: string;
  role?: string;
  status: "INVITED" | "ACTIVE" | "SUSPENDED" | "LOCKED" | "DISABLED";
  roles: Array<{
    id: UUID;
    name: string;
    display_name: string;
    campus_id?: UUID | null;
    department_id?: UUID | null;
  }>;
  permissions: string[];
  tenant?: {
    id: UUID;
    code: string;
    name: string;
  } | null;
}

/**
 * Core Institution & Academic Structure Interfaces
 */
export interface Institution {
  id: UUID;
  code: string;
  legal_name: string;
  short_name: string;
  website?: string | null;
  contact_email: string;
  contact_phone: string;
  address_line1: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  default_timezone: string;
  currency_code: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Campus {
  id: UUID;
  tenant_id: UUID;
  code: string;
  name: string;
  address: string;
  city: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: UUID;
  tenant_id: UUID;
  campus_id?: UUID | null;
  code: string;
  name: string;
  department_type: string;
  hod_user_id?: UUID | null;
  hod_name?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Program {
  id: UUID;
  tenant_id: UUID;
  department_id: UUID;
  department_name?: string | null;
  code: string;
  name: string;
  degree_level: string;
  duration_years: string | number;
  total_semesters: number;
  required_credits: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Regulation {
  id: UUID;
  tenant_id: UUID;
  code: string;
  title: string;
  effective_year: number;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AcademicYear {
  id: UUID;
  tenant_id: UUID;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

export interface Semester {
  id: UUID;
  tenant_id: UUID;
  academic_year_id: UUID;
  name: string;
  semester_number: number;
  term_type: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Batch {
  id: UUID;
  tenant_id: UUID;
  program_id: UUID;
  regulation_id: UUID;
  name: string;
  admission_year: number;
  graduation_year: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Section {
  id: UUID;
  tenant_id: UUID;
  program_id: UUID;
  batch_id: UUID;
  semester_id: UUID;
  name: string;
  capacity: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * People Domain Interfaces: Students, Faculty, Staff
 */
export type Student = StudentSummary;

export interface StudentSummary {
  id: UUID;
  user_id: UUID;
  tenant_id: UUID;
  admission_number: string;
  registration_number?: string | null;
  roll_number?: string | null;
  first_name: string;
  last_name: string;
  email: string;
  gender: string;
  status: string;
  program_id: UUID;
  program_name?: string | null;
  program_code?: string | null;
  batch_id: UUID;
  batch_name?: string | null;
  current_semester_id?: UUID | null;
  current_section_id?: UUID | null;
  current_section_name?: string | null;
  created_at: string;
}

export interface StudentEnrollmentHistory {
  id: UUID;
  academic_year_id: UUID;
  semester_id: UUID;
  section_id: UUID;
  roll_number_snapshot?: string | null;
  status: string;
  start_date: string;
  end_date?: string | null;
}

export interface StudentStatusHistory {
  id: UUID;
  from_status: string;
  to_status: string;
  reason: string;
  authorized_by_user_id: UUID;
  effective_date: string;
  created_at: string;
}

export interface StudentDetail {
  id: UUID;
  user_id: UUID;
  tenant_id: UUID;
  admission_number: string;
  registration_number?: string | null;
  roll_number?: string | null;
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string | null;
  date_of_birth: string;
  gender: string;
  blood_group?: string | null;
  status: string;
  admission_date: string;
  expected_graduation_date: string;
  actual_graduation_date?: string | null;
  program_id: UUID;
  program_name?: string | null;
  program_code?: string | null;
  batch_id: UUID;
  batch_name?: string | null;
  current_semester_id?: UUID | null;
  current_section_id?: UUID | null;
  current_section_name?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  enrollment_history: StudentEnrollmentHistory[];
  status_history: StudentStatusHistory[];
  created_at: string;
  updated_at: string;
}

export interface Faculty {
  id: UUID;
  user_id: UUID;
  tenant_id: UUID;
  employee_code: string;
  department_id: UUID;
  department_name?: string | null;
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string | null;
  designation: string;
  highest_qualification: string;
  specialization?: string | null;
  joining_date: string;
  is_hod: boolean;
  employment_status: string;
  created_at: string;
  updated_at: string;
}

export interface Staff {
  id: UUID;
  user_id: UUID;
  tenant_id: UUID;
  employee_code: string;
  department_id?: UUID | null;
  department_name?: string | null;
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string | null;
  designation: string;
  employment_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Academics Management Engine Interfaces
 */
export interface Subject {
  id: UUID;
  tenant_id: UUID;
  department_id: UUID;
  department_name?: string | null;
  code: string;
  name: string;
  credits: number;
  lecture_hours: number;
  tutorial_hours: number;
  practical_hours: number;
  subject_type: "THEORY" | "PRACTICAL" | "LAB" | "PROJECT" | "ELECTIVE" | "SEMINAR" | "INTERNSHIP" | string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CurriculumSubject {
  id: UUID;
  curriculum_id: UUID;
  subject_id: UUID;
  subject_code?: string | null;
  subject_name?: string | null;
  semester_number: number;
  category: "CORE" | "ELECTIVE" | "PROFESSIONAL_ELECTIVE" | "OPEN_ELECTIVE" | "LAB" | "PROJECT" | "INTERNSHIP" | "FOUNDATION" | string;
  is_mandatory: boolean;
  elective_group?: string | null;
  credits: number;
  lecture_hours: number;
  tutorial_hours: number;
  practical_hours: number;
}

export interface CurriculumScheme {
  id: UUID;
  tenant_id: UUID;
  program_id: UUID;
  program_name?: string | null;
  program_code?: string | null;
  regulation_id: UUID;
  regulation_code?: string | null;
  name: string;
  version: number;
  status: "DRAFT" | "REVIEW" | "APPROVED" | "PUBLISHED" | "RETIRED" | string;
  total_credits: number;
  description?: string | null;
  is_locked: boolean;
  subjects_count: number;
  created_at: string;
  updated_at: string;
}

export interface CurriculumDetail extends CurriculumScheme {
  subjects: CurriculumSubject[];
}

export interface Classroom {
  id: UUID;
  tenant_id: UUID;
  campus_id?: UUID | null;
  campus_name?: string | null;
  building: string;
  room_number: string;
  capacity: number;
  room_type: "CLASSROOM" | "LAB" | "SEMINAR_HALL" | "AUDITORIUM" | "WORKSHOP" | string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TimeSlot {
  id: UUID;
  tenant_id: UUID;
  name: string;
  slot_number: number;
  start_time: string;
  end_time: string;
  slot_type: "LECTURE" | "LAB" | "BREAK" | string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CourseOffering {
  id: UUID;
  tenant_id: UUID;
  subject_id: UUID;
  subject_code?: string | null;
  subject_name?: string | null;
  subject_credits?: number | null;
  academic_year_id: UUID;
  academic_year_name?: string | null;
  semester_id: UUID;
  semester_name?: string | null;
  section_id: UUID;
  section_name?: string | null;
  program_name?: string | null;
  status: "PLANNED" | "OPEN" | "ACTIVE" | "COMPLETED" | "CANCELLED" | string;
  max_capacity: number;
  enrolled_count: number;
  primary_faculty_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CourseFacultyAssignment {
  id: UUID;
  course_offering_id: UUID;
  faculty_id: UUID;
  faculty_name?: string | null;
  faculty_employee_code?: string | null;
  role: "PRIMARY" | "CO_FACULTY" | "LAB_INSTRUCTOR" | "TEACHING_ASSISTANT" | string;
  start_date: string;
  end_date?: string | null;
  is_active: boolean;
}

export interface CourseOfferingDetail extends CourseOffering {
  faculty_assignments: CourseFacultyAssignment[];
}

export interface CourseEnrollment {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  student_name?: string | null;
  student_roll_number?: string | null;
  student_admission_number?: string | null;
  course_offering_id: UUID;
  enrollment_type: "REGULAR" | "ELECTIVE" | "REPEAT" | "AUDIT" | string;
  status: "ENROLLED" | "DROPPED" | "WITHDRAWN" | "COMPLETED" | "FAILED" | string;
  enrollment_date: string;
  dropped_date?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TimetableEntry {
  id: UUID;
  tenant_id: UUID;
  course_offering_id: UUID;
  subject_code?: string | null;
  subject_name?: string | null;
  section_id: UUID;
  section_name?: string | null;
  academic_year_id: UUID;
  semester_id: UUID;
  faculty_id?: UUID | null;
  faculty_name?: string | null;
  room_id?: UUID | null;
  room_name?: string | null;
  time_slot_id: UUID;
  time_slot_name?: string | null;
  time_slot_start?: string | null;
  time_slot_end?: string | null;
  day_of_week: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TimetableGridCell {
  entry_id: UUID;
  course_offering_id: UUID;
  subject_code: string;
  subject_name: string;
  faculty_name?: string | null;
  room_name?: string | null;
}

export interface TimetableGridDay {
  day_number: number;
  day_name: string;
  slots: Record<string, TimetableGridCell | null>;
}

export interface TimetableSectionGrid {
  section_id: UUID;
  section_name: string;
  academic_year_id: UUID;
  semester_id: UUID;
  time_slots: TimeSlot[];
  days: TimetableGridDay[];
}

/**
 * Attendance Management Engine Interfaces
 */
export interface AttendancePolicy {
  id: UUID;
  tenant_id: UUID;
  name: string;
  department_id?: UUID | null;
  program_id?: UUID | null;
  academic_year_id?: UUID | null;
  semester_id?: UUID | null;
  course_offering_id?: UUID | null;
  minimum_percentage: number;
  warning_threshold_percentage: number;
  critical_threshold_percentage: number;
  condonation_percentage: number;
  late_grace_minutes: number;
  late_weight: number;
  excused_counts_as_present: boolean;
  on_leave_counts_as_present: boolean;
  exclude_excused_from_total: boolean;
  effective_from?: string | null;
  effective_to?: string | null;
  status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AttendanceSession {
  id: UUID;
  tenant_id: UUID;
  course_offering_id: UUID;
  course_code?: string | null;
  course_name?: string | null;
  section_id: UUID;
  section_name?: string | null;
  faculty_id: UUID;
  faculty_name?: string | null;
  academic_year_id: UUID;
  semester_id: UUID;
  session_date: string;
  period_number: number;
  session_type: string;
  status: AttendanceSessionStatus | string;
  topic?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  room_id?: UUID | null;
  room_name?: string | null;
  timetable_slot_id?: UUID | null;
  total_enrolled: number;
  total_present: number;
  total_absent: number;
  total_late: number;
  total_excused: number;
  total_on_leave: number;
  submitted_at?: string | null;
  locked_at?: string | null;
  locked_by_user_id?: UUID | null;
  created_at: string;
  updated_at: string;
}

export interface AttendanceRecord {
  id: UUID;
  session_id: UUID;
  student_id: UUID;
  student_roll_number?: string | null;
  student_admission_number?: string | null;
  student_name?: string | null;
  status: AttendanceRecordStatus | string;
  remarks?: string | null;
  recorded_by_user_id: UUID;
  has_approved_leave?: boolean;
  created_at: string;
  updated_at: string;
}

export interface AttendanceRosterStudentItem {
  student_id: UUID;
  roll_number?: string | null;
  admission_number: string;
  student_name: string;
  enrollment_status: string;
  current_status?: string | null;
  remarks?: string | null;
  has_approved_leave: boolean;
  leave_reason?: string | null;
}

export interface AttendanceSessionDetail {
  session: AttendanceSession;
  roster: AttendanceRosterStudentItem[];
  records: AttendanceRecord[];
}

export interface StudentCourseAttendanceSummary {
  course_offering_id: UUID;
  subject_code: string;
  subject_name: string;
  credits: number;
  faculty_name?: string | null;
  total_conducted: number;
  attended_sessions: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  excused_count: number;
  leave_count: number;
  attendance_percentage: number;
  minimum_required_percentage: number;
  status: "NORMAL" | "WARNING" | "CRITICAL" | string;
}

export interface StudentOverallAttendanceSummary {
  student_id: UUID;
  student_name: string;
  admission_number: string;
  roll_number?: string | null;
  program_name?: string | null;
  section_name?: string | null;
  total_conducted_sessions: number;
  total_attended_sessions: number;
  overall_percentage: number;
  minimum_required_percentage: number;
  status: "NORMAL" | "WARNING" | "CRITICAL" | string;
  courses: StudentCourseAttendanceSummary[];
  recent_records: AttendanceRecord[];
  alerts: AttendanceAlert[];
}

export interface CourseOfferingStudentAttendanceItem {
  student_id: UUID;
  student_name: string;
  admission_number: string;
  roll_number?: string | null;
  total_conducted: number;
  attended_sessions: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  excused_count: number;
  leave_count: number;
  attendance_percentage: number;
  status: "NORMAL" | "WARNING" | "CRITICAL" | string;
}

export interface CourseOfferingAttendanceSummary {
  course_offering_id: UUID;
  subject_code: string;
  subject_name: string;
  section_name: string;
  faculty_name?: string | null;
  total_sessions_conducted: number;
  total_enrolled_students: number;
  average_attendance_percentage: number;
  students_below_minimum: number;
  minimum_percentage: number;
  students: CourseOfferingStudentAttendanceItem[];
}

export interface StudentLeaveRequest {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  student_name?: string | null;
  student_roll_number?: string | null;
  student_admission_number?: string | null;
  leave_type: string;
  start_date: string;
  end_date: string;
  days_count: number;
  reason: string;
  proof_storage_key?: string | null;
  status: LeaveRequestStatus | string;
  reviewed_by_user_id?: UUID | null;
  reviewed_by_name?: string | null;
  reviewed_at?: string | null;
  review_notes?: string | null;
  created_at: string;
}

export interface AttendanceCorrectionRequest {
  id: UUID;
  tenant_id: UUID;
  attendance_record_id: UUID;
  session_id: UUID;
  session_date: string;
  course_code?: string | null;
  course_name?: string | null;
  student_id: UUID;
  student_name?: string | null;
  student_roll_number?: string | null;
  previous_status: string;
  requested_status: string;
  reason: string;
  requested_by_user_id: UUID;
  requested_by_name?: string | null;
  approved_by_user_id?: UUID | null;
  approved_by_name?: string | null;
  approval_status: CorrectionRequestStatus | string;
  approval_notes?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface AttendanceAlert {
  id: UUID;
  student_id: UUID;
  student_name?: string | null;
  student_roll_number?: string | null;
  course_offering_id?: UUID | null;
  course_name?: string | null;
  alert_type: string;
  severity: "INFO" | "WARNING" | "CRITICAL" | string;
  attendance_percentage?: number | null;
  threshold_percentage?: number | null;
  message: string;
  is_resolved: boolean;
  resolved_at?: string | null;
  created_at: string;
}

export interface LowAttendanceStudentItem {
  student_id: UUID;
  student_name: string;
  admission_number: string;
  roll_number?: string | null;
  program_name?: string | null;
  section_name?: string | null;
  course_offering_id: UUID;
  course_code: string;
  course_name: string;
  total_conducted: number;
  attended_sessions: number;
  attendance_percentage: number;
  threshold_percentage: number;
  status: "WARNING" | "CRITICAL" | string;
}

export interface AttendanceDashboard {
  today_sessions_count: number;
  today_sessions_marked: number;
  today_sessions_pending: number;
  total_students_low_attendance: number;
  average_attendance_percentage: number;
  pending_leave_requests_count: number;
  pending_corrections_count: number;
  recent_sessions: AttendanceSession[];
}

// =============================================================================
// STEP 7: EXAMINATION & ASSESSMENT ENGINE TYPES
// =============================================================================

export enum AssessmentType {
  INTERNAL = "INTERNAL",
  ASSIGNMENT = "ASSIGNMENT",
  QUIZ = "QUIZ",
  LAB = "LAB",
  PRACTICAL = "PRACTICAL",
  MODEL_EXAM = "MODEL_EXAM",
  MIDTERM = "MIDTERM",
  END_SEMESTER = "END_SEMESTER",
  PROJECT = "PROJECT",
  VIVA = "VIVA",
}

export enum AssessmentStatus {
  DRAFT = "DRAFT",
  CONFIGURED = "CONFIGURED",
  OPEN = "OPEN",
  MARKS_ENTRY = "MARKS_ENTRY",
  UNDER_REVIEW = "UNDER_REVIEW",
  FINALIZED = "FINALIZED",
  PUBLISHED = "PUBLISHED",
}

export enum ExamScheduleStatus {
  SCHEDULED = "SCHEDULED",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  CANCELLED = "CANCELLED",
  POSTPONED = "POSTPONED",
}

export enum ExamEligibilityStatus {
  ELIGIBLE = "ELIGIBLE",
  CONDONATION_REQUIRED = "CONDONATION_REQUIRED",
  DETAINED_ATTENDANCE = "DETAINED_ATTENDANCE",
  DETAINED_FEES = "DETAINED_FEES",
  DETAINED_ACADEMIC = "DETAINED_ACADEMIC",
  EXEMPTED = "EXEMPTED",
}

export enum StudentMarkStatus {
  PRESENT = "PRESENT",
  ABSENT = "ABSENT",
  NOT_ATTEMPTED = "NOT_ATTEMPTED",
  WITHHELD = "WITHHELD",
  MALPRACTICE = "MALPRACTICE",
}

export enum SemesterResultStatus {
  PASS = "PASS",
  FAIL = "FAIL",
  ABSENT = "ABSENT",
  WITHHELD = "WITHHELD",
  INCOMPLETE = "INCOMPLETE",
}

export enum ResultPublicationStatus {
  DRAFT = "DRAFT",
  UNDER_REVIEW = "UNDER_REVIEW",
  FINALIZED = "FINALIZED",
  PUBLISHED = "PUBLISHED",
}

export interface GradeScaleItem {
  id: UUID;
  grade_scale_id: UUID;
  grade_letter: string;
  grade_point: number;
  min_mark_percent: number;
  max_mark_percent: number;
  is_passing: boolean;
  description?: string | null;
}

export interface GradeScale {
  id: UUID;
  tenant_id: UUID;
  name: string;
  description?: string | null;
  is_default: boolean;
  items: GradeScaleItem[];
  created_at: string;
  updated_at: string;
}

export interface ExamTerm {
  id: UUID;
  tenant_id: UUID;
  academic_year_id: UUID;
  academic_year_name?: string | null;
  semester_id: UUID;
  semester_name?: string | null;
  name: string;
  exam_type: string;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Assessment {
  id: UUID;
  tenant_id: UUID;
  course_offering_id: UUID;
  course_code?: string | null;
  course_name?: string | null;
  section_name?: string | null;
  exam_term_id?: UUID | null;
  exam_term_name?: string | null;
  title: string;
  assessment_type: AssessmentType | string;
  sequence: number;
  max_marks: number;
  passing_marks: number;
  weightage_percent: number;
  description?: string | null;
  status: AssessmentStatus | string;
  is_finalized: boolean;
  finalized_at?: string | null;
  total_enrolled: number;
  total_marks_entered: number;
  created_at: string;
  updated_at: string;
}

export interface CourseAssessmentStructure {
  course_offering_id: UUID;
  course_code: string;
  course_name: string;
  total_weightage_percent: number;
  is_weightage_valid: boolean;
  assessments: Assessment[];
}

export interface ExamSchedule {
  id: UUID;
  tenant_id: UUID;
  assessment_id: UUID;
  assessment_title?: string | null;
  course_offering_id: UUID;
  course_code?: string | null;
  course_name?: string | null;
  section_name?: string | null;
  exam_term_id?: UUID | null;
  exam_date: string;
  start_time: string;
  end_time: string;
  room_id?: UUID | null;
  room_identifier: string;
  invigilator_faculty_id?: UUID | null;
  invigilator_name?: string | null;
  status: ExamScheduleStatus | string;
  created_at: string;
  updated_at: string;
}

export interface ExamConflictCheck {
  has_conflict: boolean;
  conflict_type?: "ROOM_CONFLICT" | "STUDENT_CONFLICT" | "INVIGILATOR_CONFLICT" | string | null;
  conflicting_schedules: ExamSchedule[];
  message?: string | null;
}

export interface ExamEligibility {
  id: UUID;
  tenant_id: UUID;
  exam_term_id: UUID;
  course_offering_id: UUID;
  course_code?: string | null;
  course_name?: string | null;
  student_id: UUID;
  student_name?: string | null;
  student_roll_number?: string | null;
  student_admission_number?: string | null;
  eligibility_status: ExamEligibilityStatus | string;
  attendance_percentage?: number | null;
  minimum_required_percentage?: number | null;
  reason?: string | null;
  is_overridden: boolean;
  override_reason?: string | null;
  evaluated_at: string;
}

export interface StudentMark {
  id: UUID;
  tenant_id: UUID;
  assessment_id: UUID;
  student_id: UUID;
  student_name?: string | null;
  student_roll_number?: string | null;
  student_admission_number?: string | null;
  marks_obtained?: number | null;
  status: StudentMarkStatus | string;
  is_absent: boolean;
  moderated_marks?: number | null;
  remarks?: string | null;
  is_finalized: boolean;
  finalized_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssessmentMarksRoster {
  assessment: Assessment;
  roster: StudentMark[];
  total_students: number;
  total_entered: number;
  total_absent: number;
  average_marks?: number | null;
  highest_marks?: number | null;
  lowest_marks?: number | null;
}

export interface MarkCorrection {
  id: UUID;
  tenant_id: UUID;
  mark_id: UUID;
  assessment_id: UUID;
  assessment_title?: string | null;
  student_id: UUID;
  student_name?: string | null;
  student_roll_number?: string | null;
  old_marks?: number | null;
  new_marks?: number | null;
  old_status: string;
  new_status: string;
  reason: string;
  requested_by_user_id: UUID;
  requested_by_name?: string | null;
  approved_by_user_id?: UUID | null;
  approved_by_name?: string | null;
  approval_status: CorrectionRequestStatus | string;
  approval_notes?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface SemesterResult {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  student_name?: string | null;
  student_roll_number?: string | null;
  student_admission_number?: string | null;
  course_offering_id: UUID;
  course_code?: string | null;
  course_name?: string | null;
  credits?: number | null;
  exam_term_id: UUID;
  exam_term_name?: string | null;
  internal_marks: number;
  external_marks: number;
  total_marks: number;
  grade_letter: string;
  grade_point: number;
  credits_earned: number;
  result_status: SemesterResultStatus | string;
  publication_status: ResultPublicationStatus | string;
  finalized_at?: string | null;
  published_at?: string | null;
  created_at: string;
}

export interface StudentSemesterTranscript {
  student_id: UUID;
  student_name: string;
  student_roll_number?: string | null;
  student_admission_number: string;
  program_name?: string | null;
  semester_name?: string | null;
  exam_term_id: UUID;
  exam_term_name: string;
  results: SemesterResult[];
  total_credits_registered: number;
  total_credits_earned: number;
  semester_gpa?: number | null;
  overall_status: string;
}

export interface ExaminationDashboard {
  active_terms_count: number;
  total_assessments_configured: number;
  assessments_pending_marks: number;
  assessments_finalized: number;
  upcoming_exam_schedules_count: number;
  results_awaiting_publication_count: number;
  total_published_results_count: number;
  pending_mark_corrections_count: number;
  recent_assessments: Assessment[];
  upcoming_schedules: ExamSchedule[];
}

// ============================================================================
// Step 8: Finance, Fees & Billing Engine Types
// ============================================================================

export type FeeStructureStatus = "DRAFT" | "APPROVED" | "ACTIVE" | "RETIRED";
export type PaymentMode =
  | "CASH"
  | "BANK_TRANSFER"
  | "UPI"
  | "CARD"
  | "CHEQUE"
  | "DD"
  | "NEFT_RTGS"
  | "ONLINE_GATEWAY";
export type ConcessionType = "MERIT" | "NEED_BASED" | "SIBLING" | "STAFF_WARD" | "SPORTS" | "SPECIAL";
export type AdjustmentType = "CREDIT" | "DEBIT";
export type RefundStatus = "REQUESTED" | "APPROVED" | "PROCESSED" | "REJECTED" | "CANCELLED";

export interface FeeCategory {
  id: UUID;
  tenant_id: UUID;
  code: string;
  name: string;
  description?: string | null;
  is_refundable: boolean;
  is_active: boolean;
  created_at: string;
}

export interface FeeStructureItem {
  id: UUID;
  category_id: UUID;
  category_code?: string | null;
  category_name?: string | null;
  name: string;
  amount: number | string;
  is_optional: boolean;
  sequence: number;
}

export interface FeeStructure {
  id: UUID;
  tenant_id: UUID;
  program_id: UUID;
  program_name?: string | null;
  academic_year_id: UUID;
  academic_year_name?: string | null;
  semester_id?: UUID | null;
  semester_name?: string | null;
  batch_id?: UUID | null;
  quota_type: string;
  name: string;
  status: FeeStructureStatus | string;
  version: number;
  total_amount: number | string;
  items: FeeStructureItem[];
  created_at: string;
}

export interface StudentFeeAssignment {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  student_name?: string | null;
  fee_structure_id: UUID;
  fee_structure_name?: string | null;
  academic_year_id: UUID;
  semester_id?: UUID | null;
  status: string;
  assigned_date: string;
  remarks?: string | null;
  total_amount?: number | string;
  created_at: string;
}

export interface InvoiceLineItem {
  id: UUID;
  category_id: UUID;
  category_name?: string | null;
  description: string;
  amount: number | string;
  waived_amount: number | string;
}

export interface PaymentAllocationItem {
  id: UUID;
  payment_id: UUID;
  invoice_id: UUID;
  invoice_number?: string | null;
  allocated_amount: number | string;
  allocated_at: string;
}

export interface Invoice {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  student_name?: string | null;
  student_admission_number?: string | null;
  academic_year_id: UUID;
  semester_id?: UUID | null;
  invoice_number: string;
  issue_date?: string | null;
  due_date: string;
  currency: string;
  gross_amount: number | string;
  concession_amount: number | string;
  adjustment_amount: number | string;
  net_payable: number | string;
  paid_amount: number | string;
  balance_amount: number | string;
  status: InvoiceStatus | string;
  remarks?: string | null;
  is_overdue: boolean;
  items: InvoiceLineItem[];
  created_at: string;
  updated_at?: string;
}

export interface PaymentTransaction {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  student_name?: string | null;
  payment_number: string;
  transaction_reference: string;
  payment_mode: PaymentMode | string;
  gateway_provider?: string | null;
  gateway_transaction_id?: string | null;
  payment_date: string;
  amount: number | string;
  currency: string;
  status: PaymentStatus | string;
  received_by_user_id?: UUID | null;
  remarks?: string | null;
  receipt_id?: UUID | null;
  receipt_number?: string | null;
  allocations: PaymentAllocationItem[];
  created_at: string;
}

export interface Receipt {
  id: UUID;
  tenant_id: UUID;
  receipt_number: string;
  payment_id: UUID;
  payment_number?: string | null;
  student_id: UUID;
  student_name?: string | null;
  student_admission_number?: string | null;
  issued_at: string;
  amount_paid: number | string;
  payment_mode: string;
  transaction_reference: string;
  currency: string;
  institution_legal_name?: string | null;
  institution_address?: string | null;
  created_at: string;
}

export interface StudentFeeConcession {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  student_name?: string | null;
  academic_year_id: UUID;
  academic_year_name?: string | null;
  concession_name: string;
  concession_type: ConcessionType | string;
  amount: number | string;
  percentage?: number | string | null;
  status: string;
  authorized_by_user_id?: UUID | null;
  authorized_at?: string | null;
  remarks?: string | null;
  created_at: string;
}

export interface FinancialAdjustment {
  id: UUID;
  tenant_id: UUID;
  invoice_id: UUID;
  invoice_number?: string | null;
  adjustment_type: AdjustmentType | string;
  amount: number | string;
  reason: string;
  requested_by_user_id?: UUID | null;
  approved_by_user_id?: UUID | null;
  status: string;
  created_at: string;
}

export interface RefundTransaction {
  id: UUID;
  tenant_id: UUID;
  payment_id: UUID;
  payment_number?: string | null;
  student_id: UUID;
  student_name?: string | null;
  refund_amount: number | string;
  currency: string;
  status: RefundStatus | string;
  reason: string;
  requested_by_user_id?: UUID | null;
  approved_by_user_id?: UUID | null;
  approved_at?: string | null;
  processed_at?: string | null;
  refund_mode?: string | null;
  refund_reference?: string | null;
  created_at: string;
}

export interface FinanceDashboard {
  total_billed: number | string;
  total_collected: number | string;
  total_outstanding: number | string;
  total_overdue: number | string;
  active_fee_structures_count: number;
  pending_payments_count: number;
  pending_refunds_count: number;
  approved_scholarships_count: number;
  recent_invoices: Invoice[];
  recent_payments: PaymentTransaction[];
}

export interface StudentFinancialSummary {
  student_id: UUID;
  student_name?: string | null;
  admission_number?: string | null;
  total_invoiced: number | string;
  total_paid: number | string;
  total_outstanding: number | string;
  total_overdue: number | string;
  active_scholarships_count: number;
  invoices: Invoice[];
  payments: PaymentTransaction[];
  receipts: Receipt[];
}

// =============================================================================
// STEP 10: CAMPUS EVENTS, CLUBS, COMMUNICATION & NOTIFICATION ENGINE
// =============================================================================

export interface EventCategory {
  id: UUID;
  tenant_id: UUID;
  code: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EventVenue {
  id: UUID;
  tenant_id: UUID;
  campus_id: UUID;
  name: string;
  code: string;
  building: string;
  floor?: string | null;
  capacity: number;
  location_description?: string | null;
  status: "ACTIVE" | "MAINTENANCE" | "INACTIVE" | string;
  created_at: string;
  updated_at: string;
}

export type EventStatus =
  | "DRAFT"
  | "PUBLISHED"
  | "REGISTRATION_OPEN"
  | "REGISTRATION_CLOSED"
  | "ONGOING"
  | "COMPLETED"
  | "CANCELLED"
  | "ARCHIVED";

export type EventVisibility =
  | "PUBLIC"
  | "INSTITUTION"
  | "CAMPUS"
  | "DEPARTMENT"
  | "PROGRAM"
  | "SECTION"
  | "CLUB"
  | "PRIVATE";

export interface CampusEvent {
  id: UUID;
  tenant_id: UUID;
  campus_id: UUID;
  category_id?: UUID | null;
  category_name?: string | null;
  title: string;
  slug: string;
  description?: string | null;
  organizer_type: string;
  organizer_id?: UUID | null;
  organizer_name?: string | null;
  department_id?: UUID | null;
  club_id?: UUID | null;
  start_at: string;
  end_at: string;
  registration_open_at?: string | null;
  registration_close_at?: string | null;
  venue_id?: UUID | null;
  venue_name?: string | null;
  venue_details?: EventVenue | null;
  capacity?: number | null;
  status: EventStatus;
  visibility: EventVisibility;
  requires_registration: boolean;
  requires_attendance: boolean;
  target_filter_json?: Record<string, unknown> | null;
  created_by_user_id?: UUID | null;
  registered_count: number;
  attended_count: number;
  user_registration_status?: string | null;
  user_registration_id?: UUID | null;
  created_at: string;
  updated_at: string;
}

export interface EventRegistration {
  id: UUID;
  tenant_id: UUID;
  event_id: UUID;
  student_id: UUID;
  registration_code: string;
  registered_at: string;
  status: "REGISTERED" | "WAITLISTED" | "CONFIRMED" | "CANCELLED" | "ATTENDED" | "NO_SHOW" | string;
  cancelled_at?: string | null;
  cancellation_reason?: string | null;
  attended: boolean;
  student_name?: string | null;
  student_roll_number?: string | null;
  student_email?: string | null;
  event_title?: string | null;
  created_at: string;
}

export interface EventAttendance {
  id: UUID;
  tenant_id: UUID;
  event_id: UUID;
  registration_id?: UUID | null;
  student_id: UUID;
  checked_in_at: string;
  checked_out_at?: string | null;
  attendance_status: "PRESENT" | "LATE" | "EXCUSED" | "LEFT_EARLY" | string;
  marked_by_user_id?: UUID | null;
  verification_method: "MANUAL" | "QR" | "NFC" | "IMPORT" | string;
  remarks?: string | null;
  student_name?: string | null;
  student_roll_number?: string | null;
}

export interface EventQRToken {
  event_id: UUID;
  qr_token: string;
  expires_at: string;
  valid_duration_seconds: number;
}

export interface Club {
  id: UUID;
  tenant_id: UUID;
  campus_id?: UUID | null;
  code: string;
  name: string;
  slug: string;
  category: string;
  description?: string | null;
  logo_document_id?: UUID | null;
  faculty_advisor_id?: UUID | null;
  faculty_advisor_name?: string | null;
  student_lead_id?: UUID | null;
  student_lead_name?: string | null;
  status: "DRAFT" | "PENDING_APPROVAL" | "ACTIVE" | "SUSPENDED" | "ARCHIVED" | string;
  is_active: boolean;
  members_count: number;
  events_count: number;
  user_membership_status?: string | null;
  user_membership_role?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClubMembership {
  id: UUID;
  tenant_id: UUID;
  club_id: UUID;
  student_id: UUID;
  role: "MEMBER" | "PRESIDENT" | "VICE_PRESIDENT" | "SECRETARY" | "TREASURER" | "EVENT_COORDINATOR" | "OTHER" | string;
  status: "PENDING" | "ACTIVE" | "REJECTED" | "SUSPENDED" | "LEFT" | string;
  joined_at?: string | null;
  left_at?: string | null;
  rejection_reason?: string | null;
  student_name?: string | null;
  student_roll_number?: string | null;
  student_email?: string | null;
  approved_by_name?: string | null;
  created_at: string;
}

export interface AnnouncementAudience {
  target_type:
    | "ALL_USERS"
    | "ALL_STUDENTS"
    | "ALL_FACULTY"
    | "ALL_STAFF"
    | "CAMPUS"
    | "DEPARTMENT"
    | "PROGRAM"
    | "ACADEMIC_YEAR"
    | "SEMESTER"
    | "SECTION"
    | "CLUB"
    | "INDIVIDUAL_USERS"
    | string;
  target_id?: UUID | null;
  filter_metadata?: Record<string, unknown> | null;
}

export interface Announcement {
  id: UUID;
  tenant_id: UUID;
  title: string;
  summary?: string | null;
  content: string;
  priority: "LOW" | "NORMAL" | "HIGH" | "URGENT";
  status: "DRAFT" | "SCHEDULED" | "PUBLISHED" | "EXPIRED" | "ARCHIVED" | "CANCELLED" | string;
  publish_at: string;
  expires_at?: string | null;
  is_pinned: boolean;
  created_by_user_id: UUID;
  created_by_name?: string | null;
  published_by_name?: string | null;
  published_at?: string | null;
  audiences: AnnouncementAudience[];
  estimated_recipients?: number;
  created_at: string;
  updated_at: string;
}

export interface AudiencePreview {
  total_recipients: number;
  students_count: number;
  faculty_count: number;
  staff_count: number;
  sample_recipients: Array<{
    name: string;
    email: string;
    role: string;
  }>;
}

export interface NotificationItem {
  id: UUID;
  tenant_id: UUID;
  recipient_user_id: UUID;
  type: string;
  title: string;
  message: string;
  priority: "LOW" | "NORMAL" | "HIGH" | "URGENT";
  action_url?: string | null;
  source_module: string;
  source_entity_type?: string | null;
  source_entity_id?: UUID | null;
  channel: string;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationPreference {
  category: string;
  channel: string;
  is_enabled: boolean;
  is_mandatory: boolean;
}

export interface CampusDashboardStats {
  upcoming_events_count: number;
  open_registrations_count: number;
  registered_participants_count: number;
  active_clubs_count: number;
  pending_club_requests_count: number;
  published_announcements_count: number;
  unread_notifications_count: number;
  events_this_month_count: number;
}

// ============================================================================
// PLACEMENT & CAREER ENGINE TYPES
// ============================================================================

export type CompanyTier = "DREAM" | "SUPER_DREAM" | "TIER_1" | "TIER_2" | "MASS" | string;
export type CompanyType = "PRODUCT" | "SERVICE" | "STARTUP" | "MNC" | "PSU" | "GOVT" | string;
export type CompanyStatus = "PROSPECT" | "ACTIVE" | "INACTIVE" | "BLACKLISTED" | "ARCHIVED" | string;

export interface CompanyContact {
  id: UUID;
  company_id: UUID;
  name: string;
  email: string;
  phone?: string | null;
  designation?: string | null;
  is_primary: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Company {
  id: UUID;
  tenant_id: UUID;
  name: string;
  legal_name?: string | null;
  industry: string;
  company_type: CompanyType;
  tier: CompanyTier;
  website?: string | null;
  description?: string | null;
  headquarters_location?: string | null;
  status: CompanyStatus;
  created_at: string;
  updated_at: string;
}

export interface CompanyDetail extends Company {
  contacts: CompanyContact[];
}

export interface EligibilityRule {
  id: UUID;
  job_position_id: UUID;
  rule_type: string;
  operator: string;
  value_json: unknown;
  metadata_json?: unknown | null;
  is_required: boolean;
  sequence: number;
  created_at: string;
  updated_at: string;
}

export interface JobPosition {
  id: UUID;
  job_drive_id: UUID;
  title: string;
  description?: string | null;
  employment_type: "FULL_TIME" | "PART_TIME" | "INTERNSHIP" | "INTERNSHIP_TO_FULL_TIME" | string;
  work_location?: string | null;
  vacancy_count: number;
  salary_min?: number | null;
  salary_max?: number | null;
  currency: string;
  ctc: number;
  skills_json?: string[] | null;
  qualification?: string | null;
  experience_requirement?: string | null;
  joining_date?: string | null;
  status: "OPEN" | "CLOSED" | "ON_HOLD" | "CANCELLED" | string;
  created_at: string;
  updated_at: string;
}

export interface JobPositionDetail extends JobPosition {
  eligibility_rules: EligibilityRule[];
}

export interface JobDrive {
  id: UUID;
  tenant_id: UUID;
  company_id: UUID;
  academic_year_id: UUID;
  drive_code: string;
  title: string;
  description?: string | null;
  application_open_at: string;
  application_close_at: string;
  drive_date: string;
  location?: string | null;
  mode: "ON_CAMPUS" | "OFF_CAMPUS" | "VIRTUAL" | "HYBRID" | string;
  status:
    | "DRAFT"
    | "PUBLISHED"
    | "APPLICATIONS_OPEN"
    | "APPLICATIONS_CLOSED"
    | "SHORTLISTING"
    | "INTERVIEWING"
    | "OFFERS"
    | "CLOSED"
    | "CANCELLED"
    | string;
  created_by_user_id?: UUID | null;
  created_at: string;
  updated_at: string;
}

export interface JobDriveDetail extends JobDrive {
  company?: Company | null;
  positions: JobPositionDetail[];
}

export interface RuleEvaluationResult {
  rule_type: string;
  expected: unknown;
  actual: unknown;
  passed: boolean;
  message?: string | null;
}

export interface EligibilityEvaluation {
  student_id: UUID;
  job_position_id: UUID;
  is_eligible: boolean;
  evaluated_at: string;
  rule_results: RuleEvaluationResult[];
  source_data_snapshot: {
    cgpa?: number;
    backlogs?: number;
    attendance_pct?: number;
    fee_cleared?: boolean;
    program_code?: string;
    department_code?: string;
    [key: string]: unknown;
  };
}

export interface StudentPlacementProfile {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  career_objective?: string | null;
  preferred_locations_json?: string[] | null;
  preferred_roles_json?: string[] | null;
  skills_json?: string[] | null;
  certifications_json?: Array<Record<string, unknown>> | null;
  portfolio_url?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
  resume_document_id?: UUID | null;
  availability_status: "AVAILABLE" | "OPTED_OUT" | "PLACED" | "HIGHER_STUDIES" | string;
  profile_completion_percentage: number;
  created_at: string;
  updated_at: string;
}

export interface PlacementApplication {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  job_position_id: UUID;
  eligibility_snapshot_id?: UUID | null;
  application_number: string;
  status:
    | "APPLIED"
    | "SHORTLISTED"
    | "IN_REVIEW"
    | "REJECTED"
    | "WITHDRAWN"
    | "INTERVIEWING"
    | "SELECTED"
    | "OFFERED"
    | "ACCEPTED"
    | "DECLINED"
    | string;
  applied_at: string;
  withdrawn_at?: string | null;
  withdrawal_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationHistory {
  id: UUID;
  application_id: UUID;
  from_status: string;
  to_status: string;
  reason?: string | null;
  changed_by_user_id?: UUID | null;
  changed_at: string;
}

export interface InterviewRound {
  id: UUID;
  job_position_id: UUID;
  name: string;
  description?: string | null;
  sequence: number;
  round_type: "APTITUDE" | "TECHNICAL" | "CODING" | "GROUP_DISCUSSION" | "MANAGERIAL" | "HR" | "FINAL" | "OTHER" | string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface InterviewSchedule {
  id: UUID;
  interview_round_id: UUID;
  application_id: UUID;
  scheduled_at: string;
  duration_minutes: number;
  location?: string | null;
  meeting_url?: string | null;
  interviewer?: string | null;
  status: "SCHEDULED" | "COMPLETED" | "RESCHEDULED" | "CANCELLED" | "NO_SHOW" | string;
  created_at: string;
  updated_at: string;
}

export interface InterviewEvaluation {
  id: UUID;
  interview_schedule_id: UUID;
  evaluated_by_user_id?: UUID | null;
  evaluated_at: string;
  result: "PASS" | "FAIL" | "ON_HOLD" | "PENDING" | "NO_SHOW" | string;
  score?: number | null;
  feedback?: string | null;
  internal_notes?: string | null;
  recommendation?: "STRONG_HIRE" | "HIRE" | "NO_HIRE" | string | null;
  created_at: string;
  updated_at: string;
}

export interface PlacementOffer {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  job_position_id: UUID;
  company_id: UUID;
  placement_application_id: UUID;
  offer_number: string;
  offer_date: string;
  designation: string;
  ctc: number;
  currency: string;
  work_location?: string | null;
  joining_date?: string | null;
  employment_type: string;
  offer_expiry_date: string;
  document_id?: UUID | null;
  status: "DRAFT" | "ISSUED" | "ACCEPTED" | "DECLINED" | "EXPIRED" | "WITHDRAWN" | "CANCELLED" | string;
  accepted_at?: string | null;
  declined_at?: string | null;
  decline_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlacementOutcome {
  id: UUID;
  tenant_id: UUID;
  student_id: UUID;
  academic_year_id: UUID;
  outcome: "PLACED" | "NOT_PLACED" | "HIGHER_STUDIES" | "ENTREPRENEURSHIP" | "OTHER" | string;
  accepted_offer_id?: UUID | null;
  company_id?: UUID | null;
  designation?: string | null;
  ctc?: number | null;
  remarks?: string | null;
  recorded_at: string;
  recorded_by_user_id?: UUID | null;
  created_at: string;
  updated_at: string;
}

export interface PlacementAnalyticsSummary {
  total_eligible_students: number;
  registered_students: number;
  placed_students: number;
  placement_percentage: number;
  total_offers: number;
  unique_companies_count: number;
  highest_ctc: number;
  average_ctc: number;
  median_ctc: number;
  tier_distribution: Record<string, number>;
  department_stats: Array<{
    department_id?: UUID;
    department_name: string;
    eligible_count: number;
    placed_count: number;
    placement_pct: number;
    average_ctc: number;
  }>;
  top_recruiters: Array<{
    company_name: string;
    tier: string;
    offers_count: number;
    highest_ctc: number;
  }>;
}

// ============================================================================
// INFRASTRUCTURE MANAGEMENT DOMAIN TYPES
// ============================================================================

export enum HostelStatus {
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  UNDER_MAINTENANCE = "UNDER_MAINTENANCE",
  CLOSED = "CLOSED",
}

export enum HostelType {
  BOYS = "BOYS",
  GIRLS = "GIRLS",
  MIXED = "MIXED",
  STAFF = "STAFF",
  GUEST = "GUEST",
}

export enum RoomType {
  SINGLE = "SINGLE",
  DOUBLE = "DOUBLE",
  TRIPLE = "TRIPLE",
  FOUR_SHARING = "FOUR_SHARING",
  DORMITORY = "DORMITORY",
}

export enum RoomStatus {
  AVAILABLE = "AVAILABLE",
  PARTIALLY_OCCUPIED = "PARTIALLY_OCCUPIED",
  FULL = "FULL",
  MAINTENANCE = "MAINTENANCE",
  BLOCKED = "BLOCKED",
}

export enum BedStatus {
  AVAILABLE = "AVAILABLE",
  ALLOCATED = "ALLOCATED",
  MAINTENANCE = "MAINTENANCE",
  BLOCKED = "BLOCKED",
}

export enum AllocationStatus {
  PENDING = "PENDING",
  ALLOCATED = "ALLOCATED",
  TRANSFER_REQUESTED = "TRANSFER_REQUESTED",
  TRANSFERRED = "TRANSFERRED",
  VACATED = "VACATED",
  CANCELLED = "CANCELLED",
}

export enum LeaveStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  CANCELLED = "CANCELLED",
  COMPLETED = "COMPLETED",
}

export enum ComplaintCategory {
  ELECTRICAL = "ELECTRICAL",
  PLUMBING = "PLUMBING",
  CLEANING = "CLEANING",
  FURNITURE = "FURNITURE",
  ROOM = "ROOM",
  WIFI = "WIFI",
  SAFETY = "SAFETY",
  WATER = "WATER",
  FOOD = "FOOD",
  OTHER = "OTHER",
}

export enum ComplaintStatus {
  OPEN = "OPEN",
  ASSIGNED = "ASSIGNED",
  IN_PROGRESS = "IN_PROGRESS",
  RESOLVED = "RESOLVED",
  CLOSED = "CLOSED",
  REJECTED = "REJECTED",
}

export enum ComplaintPriority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum RouteStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  SUSPENDED = "SUSPENDED",
}

export enum StopStatus {
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  TEMPORARILY_CLOSED = "TEMPORARILY_CLOSED",
}

export enum VehicleType {
  BUS = "BUS",
  MINI_BUS = "MINI_BUS",
  VAN = "VAN",
  CAR = "CAR",
  OTHER = "OTHER",
}

export enum VehicleStatus {
  ACTIVE = "ACTIVE",
  AVAILABLE = "AVAILABLE",
  MAINTENANCE = "MAINTENANCE",
  INACTIVE = "INACTIVE",
  RETIRED = "RETIRED",
}

export enum DriverStatus {
  ACTIVE = "ACTIVE",
  ON_LEAVE = "ON_LEAVE",
  SUSPENDED = "SUSPENDED",
  INACTIVE = "INACTIVE",
}

export enum TransportAllocationStatus {
  PENDING = "PENDING",
  ACTIVE = "ACTIVE",
  SUSPENDED = "SUSPENDED",
  CANCELLED = "CANCELLED",
  EXPIRED = "EXPIRED",
}

export enum FacilityStatus {
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  UNDER_MAINTENANCE = "UNDER_MAINTENANCE",
  CLOSED = "CLOSED",
  RESERVED = "RESERVED",
}

export enum FacilityType {
  ACADEMIC_BLOCK = "ACADEMIC_BLOCK",
  CLASSROOM_BLOCK = "CLASSROOM_BLOCK",
  LABORATORY = "LABORATORY",
  LIBRARY = "LIBRARY",
  AUDITORIUM = "AUDITORIUM",
  SEMINAR_HALL = "SEMINAR_HALL",
  SPORTS_FACILITY = "SPORTS_FACILITY",
  SPORTS_COMPLEX = "SPORTS_COMPLEX",
  CAFETERIA = "CAFETERIA",
  ADMINISTRATIVE_OFFICE = "ADMINISTRATIVE_OFFICE",
  ADMINISTRATIVE = "ADMINISTRATIVE",
  HOSTEL = "HOSTEL",
  PARKING_AREA = "PARKING_AREA",
}

export enum MaintenanceStatus {
  REQUESTED = "REQUESTED",
  ASSIGNED = "ASSIGNED",
  IN_PROGRESS = "IN_PROGRESS",
  ON_HOLD = "ON_HOLD",
  RESOLVED = "RESOLVED",
  CLOSED = "CLOSED",
  CANCELLED = "CANCELLED",
}

export enum MaintenancePriority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

// ----------------------------------------------------------------------------
// Entity Interfaces
// ----------------------------------------------------------------------------

export interface HostelBed {
  id: UUID;
  roomId: UUID;
  bedNumber: string;
  status: BedStatus;
  studentId?: UUID | null;
  studentName?: string | null;
  studentRollNumber?: string | null;
  allocatedAt?: string | null;
}

export interface HostelRoom {
  id: UUID;
  hostelId: UUID;
  hostelName: string;
  blockId: string;
  blockName: string;
  floor: number;
  roomNumber: string;
  roomType: RoomType;
  capacity: number;
  occupied: number;
  available: number;
  gender: "MALE" | "FEMALE" | "ANY";
  status: RoomStatus;
  beds?: HostelBed[];
}

export interface HostelFloor {
  floorNumber: number;
  name: string;
  totalRooms: number;
  rooms?: HostelRoom[];
}

export interface HostelBlock {
  id: string;
  name: string;
  hostelId: UUID;
  floorsCount: number;
  roomsCount: number;
  totalBeds: number;
  occupiedBeds: number;
  floors?: HostelFloor[];
}

export interface Hostel {
  id: UUID;
  name: string;
  code: string;
  campusId: UUID;
  campusName: string;
  type: HostelType;
  gender: "BOYS" | "GIRLS" | "MIXED";
  wardenId?: UUID | null;
  wardenName: string;
  wardenPhone: string;
  wardenEmail: string;
  totalBlocks: number;
  totalRooms: number;
  totalBeds: number;
  occupiedBeds: number;
  availableBeds: number;
  occupancyPercentage: number;
  status: HostelStatus;
  blocks?: HostelBlock[];
  createdAt: string;
  updatedAt: string;
}

export interface AllocationHistoryEntry {
  id: UUID;
  action: string;
  description: string;
  timestamp: string;
  performedBy: string;
}

export interface HostelAllocation {
  id: UUID;
  studentId: UUID;
  studentName: string;
  registerNumber: string;
  programId?: string;
  programCode: string;
  programName: string;
  departmentCode: string;
  year: number;
  semester: number;
  hostelId: UUID;
  hostelName: string;
  blockId: string;
  blockName: string;
  floor: number;
  roomId: UUID;
  roomNumber: string;
  bedId: UUID;
  bedNumber: string;
  allocatedDate: string;
  expectedEndDate?: string | null;
  vacatedDate?: string | null;
  status: AllocationStatus;
  financeRefId?: string | null;
  remarks?: string | null;
  history?: AllocationHistoryEntry[];
  createdAt: string;
  updatedAt: string;
}

export interface HostelLeave {
  id: UUID;
  studentId: UUID;
  studentName: string;
  registerNumber: string;
  hostelId: UUID;
  hostelName: string;
  roomNumber: string;
  startDate: string;
  endDate: string;
  reason: string;
  destination: string;
  emergencyContact: {
    name: string;
    relationship: string;
    phone: string;
  };
  approvalStatus: LeaveStatus;
  approvedBy?: string | null;
  approvedAt?: string | null;
  remarks?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface HostelComplaint {
  id: UUID;
  ticketNumber: string;
  studentId: UUID;
  studentName: string;
  registerNumber: string;
  hostelId: UUID;
  hostelName: string;
  roomNumber: string;
  category: ComplaintCategory;
  priority: ComplaintPriority;
  title: string;
  description: string;
  status: ComplaintStatus;
  assignedStaffId?: UUID | null;
  assignedStaffName?: string | null;
  slaTargetHours: number;
  slaBreached: boolean;
  resolutionNotes?: string | null;
  resolvedAt?: string | null;
  closedAt?: string | null;
  attachments?: Array<{ name: string; url: string; size: string }>;
  activityTimeline?: Array<{
    id: UUID;
    action: string;
    status: ComplaintStatus;
    timestamp: string;
    actor: string;
    notes?: string;
  }>;
  createdAt: string;
  updatedAt: string;
}

export interface TransportStop {
  id: UUID;
  routeId: UUID;
  routeName: string;
  routeCode: string;
  name: string;
  code: string;
  sequence: number;
  pickupTime: string;
  dropTime: string;
  landmark?: string;
  studentCount: number;
  status: StopStatus;
}

export interface VehicleServiceRecord {
  id: UUID;
  serviceDate: string;
  serviceType: string;
  mileageKm: number;
  costInr: number;
  nextServiceDate: string;
  vendorName: string;
  status: "COMPLETED" | "SCHEDULED" | "OVERDUE";
  notes?: string;
}

export interface TransportVehicle {
  id: UUID;
  registrationNumber: string;
  vehicleNumber: string;
  type: VehicleType;
  makeModel: string;
  make?: string;
  model?: string;
  capacity: number;
  currentRouteId?: UUID | null;
  currentRouteCode?: string | null;
  currentRouteName?: string | null;
  assignedDriverId?: UUID | null;
  assignedDriverName?: string | null;
  fuelType: "DIESEL" | "EV" | "CNG" | "PETROL";
  insurancePolicyNumber: string;
  insuranceValidUntil: string;
  insuranceExpiry?: string;
  fitnessCertificateValidUntil: string;
  fitnessExpiry?: string;
  pollutionCertificateValidUntil: string;
  lastServiceDate: string;
  nextServiceDate: string;
  status: VehicleStatus;
  services?: VehicleServiceRecord[];
  documents?: Array<{ id: string; title: string; category: string; expiryDate?: string }>;
}

export interface TransportDriver {
  id: UUID;
  staffId?: UUID;
  name: string;
  employeeId: string;
  phone: string;
  email?: string;
  emergencyContact?: string;
  licenseNumber: string;
  licenseType: string;
  licenseExpiry: string;
  licenseStatus: "VALID" | "EXPIRING_SOON" | "EXPIRED";
  assignedVehicleId?: UUID | null;
  assignedVehicleNumber?: string | null;
  assignedRouteId?: UUID | null;
  assignedRouteCode?: string | null;
  assignedRouteName?: string | null;
  experienceYears: number;
  joiningDate: string;
  status: DriverStatus;
  assignmentsHistory?: Array<{
    vehicleNumber: string;
    routeCode: string;
    startDate: string;
    endDate?: string | null;
  }>;
}

export interface TransportRoute {
  id: UUID;
  routeCode: string;
  name: string;
  campusId: UUID;
  campusName: string;
  startPoint: string;
  endPoint: string;
  stopsCount: number;
  stops?: TransportStop[];
  vehicleId?: UUID | null;
  vehicleNumber?: string | null;
  driverId?: UUID | null;
  driverName?: string | null;
  driverPhone?: string | null;
  capacity: number;
  allocatedStudents: number;
  utilizationPercentage: number;
  morningDeparture: string;
  morningStartTime?: string;
  eveningReturn: string;
  eveningReturnTime?: string;
  status: RouteStatus;
}

export interface TransportAllocation {
  id: UUID;
  studentId: UUID;
  studentName: string;
  registerNumber: string;
  programCode: string;
  departmentCode: string;
  routeId: UUID;
  routeCode: string;
  routeName: string;
  stopId: UUID;
  stopName: string;
  vehicleId: UUID;
  vehicleNumber: string;
  academicYear: string;
  semester: number;
  allocatedDate: string;
  status: TransportAllocationStatus;
  seatNumber?: string | null;
  feeStatus?: "PAID" | "PENDING" | "WAIVED" | string | null;
  financeFeeRefId?: string | null;
  createdAt: string;
}

export interface FacilityEquipment {
  id: UUID;
  name: string;
  code: string;
  quantity: number;
  condition: "EXCELLENT" | "GOOD" | "FAIR" | "NEEDS_REPAIR";
  lastInspectedDate: string;
}

export interface Facility {
  id: UUID;
  name: string;
  code: string;
  campusId: UUID;
  campusName: string;
  building: string;
  floor: number | string;
  type: FacilityType;
  capacity: number;
  status: FacilityStatus;
  managerName: string;
  managerEmail: string;
  managerPhone: string;
  departmentCode?: string | null;
  connectedEventsCount?: number;
  activeWorkOrdersCount?: number;
  equipment?: FacilityEquipment[];
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface MaintenanceHistoryEntry {
  id: UUID;
  fromStatus: MaintenanceStatus;
  toStatus: MaintenanceStatus;
  timestamp: string;
  changedBy: string;
  notes?: string;
}

export interface MaintenanceRequest {
  id: UUID;
  workOrderNumber: string;
  assetOrFacilityId: string;
  assetOrFacilityName: string;
  category: "ELECTRICAL" | "PLUMBING" | "CIVIL" | "HVAC" | "IT_EQUIPMENT" | "CARPENTRY" | "TRANSPORT_VEHICLE" | "OTHER";
  sourceType: "HOSTEL" | "ROOM" | "FACILITY" | "VEHICLE" | "EQUIPMENT" | "CAMPUS";
  location: string;
  reportedBy: {
    userId: string;
    name: string;
    role: string;
    phone?: string;
  };
  assignedTo?: {
    staffId: string;
    name: string;
    department: string;
    phone: string;
  } | null;
  priority: MaintenancePriority;
  title: string;
  description: string;
  estimatedCostInr: number;
  actualCostInr?: number | null;
  status: MaintenanceStatus;
  slaTargetHours: number;
  isSlaBreached: boolean;
  resolutionSummary?: string | null;
  resolvedAt?: string | null;
  closedAt?: string | null;
  history?: MaintenanceHistoryEntry[];
  createdAt: string;
  updatedAt: string;
}

export interface InfrastructureDashboardSummary {
  totalHostels: number;
  totalBeds: number;
  occupiedBeds: number;
  availableBeds: number;
  hostelOccupancyPercentage: number;
  activeTransportRoutes: number;
  activeVehicles: number;
  studentsUsingTransport: number;
  openComplaints: number;
  openMaintenanceRequests: number;
  criticalMaintenance: number;
  facilitiesRequiringAttention: number;
}

export interface InfrastructureReportData {
  hostelSummary: {
    totalHostels: number;
    totalBeds: number;
    occupiedBeds: number;
    availableBeds: number;
    hostelWiseStats: Array<{
      hostelName: string;
      code: string;
      totalBeds: number;
      occupiedBeds: number;
      occupancyPercentage: number;
    }>;
    programWiseAllocations: Array<{
      programCode: string;
      studentCount: number;
      percentage: number;
    }>;
    monthlyLeaveTrends: Array<{
      month: string;
      leaveRequests: number;
      approved: number;
    }>;
    complaintDistribution: Array<{
      category: string;
      count: number;
      resolvedRate: number;
    }>;
  };
  transportSummary: {
    routeUtilization: Array<{
      routeCode: string;
      routeName: string;
      capacity: number;
      allocated: number;
      utilizationPercentage: number;
    }>;
    vehicleFleetStatus: Array<{
      status: string;
      count: number;
    }>;
    stopWiseStudentDistribution: Array<{
      stopName: string;
      routeCode: string;
      studentCount: number;
    }>;
  };
  facilitiesSummary: {
    totalFacilities: number;
    facilitiesByType: Array<{
      type: string;
      count: number;
    }>;
    facilityMaintenanceFrequency: Array<{
      facilityName: string;
      maintenanceCount: number;
      openCount: number;
    }>;
  };
  maintenanceSummary: {
    openRequests: number;
    inProgressRequests: number;
    resolvedRequests: number;
    criticalRequests: number;
    averageResolutionHours: number;
    totalMaintenanceCostInr: number;
    priorityDistribution: Array<{
      priority: string;
      count: number;
    }>;
    categoryDistribution: Array<{
      category: string;
      count: number;
    }>;
  };
}

// ============================================================================
// MODULE 9: DOCUMENTS & DIGITAL RECORDS DOMAIN TYPES
// ============================================================================

export enum DocumentStatus {
  REQUIRED = "REQUIRED",
  MISSING = "MISSING",
  UPLOADED = "UPLOADED",
  UNDER_REVIEW = "UNDER_REVIEW",
  VERIFIED = "VERIFIED",
  REJECTED = "REJECTED",
  EXPIRED = "EXPIRED",
  ARCHIVED = "ARCHIVED",
  REVOKED = "REVOKED",
}

export enum DocumentCategoryCode {
  IDENTITY = "IDENTITY",
  ACADEMIC = "ACADEMIC",
  ADMISSION = "ADMISSION",
  FINANCIAL = "FINANCIAL",
  PLACEMENT = "PLACEMENT",
  HOSTEL = "HOSTEL",
  TRANSPORT = "TRANSPORT",
  MEDICAL = "MEDICAL",
  ADMINISTRATIVE = "ADMINISTRATIVE",
  CERTIFICATE = "CERTIFICATE",
  OTHER = "OTHER",
}

export enum CertificateType {
  BONAFIDE = "BONAFIDE",
  COURSE_COMPLETION = "COURSE_COMPLETION",
  TRANSFER = "TRANSFER",
  CONDUCT = "CONDUCT",
  CHARACTER = "CHARACTER",
  ATTENDANCE = "ATTENDANCE",
  INTERNSHIP = "INTERNSHIP",
  PLACEMENT = "PLACEMENT",
  PARTICIPATION = "PARTICIPATION",
  OTHER = "OTHER",
}

export enum CertificateTemplateStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  ARCHIVED = "ARCHIVED",
}

export enum CertificateRequestStatus {
  DRAFT = "DRAFT",
  SUBMITTED = "SUBMITTED",
  UNDER_REVIEW = "UNDER_REVIEW",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  ISSUED = "ISSUED",
  CANCELLED = "CANCELLED",
}

export enum IssuedCertificateStatus {
  ISSUED = "ISSUED",
  REVOKED = "REVOKED",
}

export enum InstitutionalRecordStatus {
  ACTIVE = "ACTIVE",
  EXPIRED = "EXPIRED",
  ARCHIVED = "ARCHIVED",
  REVOKED = "REVOKED",
}

export enum ConfidentialityLevel {
  PUBLIC = "PUBLIC",
  INTERNAL = "INTERNAL",
  CONFIDENTIAL = "CONFIDENTIAL",
  RESTRICTED = "RESTRICTED",
}

export enum DocumentOwnerType {
  STUDENT = "STUDENT",
  FACULTY = "FACULTY",
  STAFF = "STAFF",
  INSTITUTION = "INSTITUTION",
  DEPARTMENT = "DEPARTMENT",
}

export enum DocumentExpiryStatus {
  EXPIRED = "EXPIRED",
  EXPIRING_7_DAYS = "EXPIRING_7_DAYS",
  EXPIRING_30_DAYS = "EXPIRING_30_DAYS",
  EXPIRING_90_DAYS = "EXPIRING_90_DAYS",
  VALID = "VALID",
  NO_EXPIRY = "NO_EXPIRY",
}

export enum VerificationPriority {
  LOW = "LOW",
  NORMAL = "NORMAL",
  HIGH = "HIGH",
  URGENT = "URGENT",
}

export interface VerificationChecklistItem {
  id: string;
  label: string;
  checked: boolean;
  required: boolean;
  notes?: string;
}

export interface DocumentTimelineItem {
  id: string;
  action: string;
  description: string;
  performedBy: string;
  role?: string;
  timestamp: string;
  notes?: string;
}

export interface DocumentMetadata {
  documentNumber?: string;
  issuingAuthority?: string;
  issueDate?: string;
  expiryDate?: string;
  placeOfIssue?: string;
  verifiedBy?: string;
  rejectionReason?: string;
  notes?: string;
  tags?: string[];
}

export interface DocumentItem {
  id: string;
  name: string;
  category: DocumentCategoryCode;
  documentType: string;
  ownerType: DocumentOwnerType;
  ownerId: string;
  ownerName: string;
  ownerRollNumber?: string;
  ownerDepartment?: string;
  program?: string;
  academicYear?: string;
  semester?: number;
  status: DocumentStatus;
  uploadedAt: string;
  verifiedAt?: string;
  verifiedBy?: string;
  rejectionReason?: string;
  expiryDate?: string;
  issueDate?: string;
  documentNumber?: string;
  issuingAuthority?: string;
  confidentiality: ConfidentialityLevel;
  fileSize: string;
  fileType: string;
  fileUrl?: string;
  priority?: VerificationPriority;
  assignedReviewerId?: string;
  assignedReviewerName?: string;
  verificationChecklist?: VerificationChecklistItem[];
  activityTimeline: DocumentTimelineItem[];
  relatedRecord?: {
    entityType: "STUDENT" | "FACULTY" | "STAFF" | "PROGRAM" | "DEPARTMENT" | "ADMISSION" | "PLACEMENT" | "HOSTEL" | "TRANSPORT" | "FINANCE" | "CAMPUS";
    entityId: string;
    label: string;
  };
}

export interface DocumentCategoryAuditItem {
  id: string;
  action: string;
  performedBy: string;
  timestamp: string;
  details?: string;
}

export interface DocumentCategory {
  id: string;
  name: string;
  code: DocumentCategoryCode;
  description: string;
  required: boolean;
  applicableRoles: string[];
  applicablePrograms?: string[];
  applicableDocumentTypes: string[];
  verificationRequired: boolean;
  expiryRequired: boolean;
  isActive: boolean;
  totalDocuments?: number;
  verifiedDocuments?: number;
  pendingDocuments?: number;
  rejectedDocuments?: number;
  auditHistory?: DocumentCategoryAuditItem[];
}

export interface CertificateTemplateField {
  id: string;
  name: string;
  label: string;
  type: "TEXT" | "NUMBER" | "DATE" | "SYSTEM_VARIABLE";
  required: boolean;
  systemVariableMapping?: string;
  defaultValue?: string;
}

export interface CertificateTemplateVersion {
  version: string;
  publishedAt: string;
  publishedBy: string;
  changelog: string;
}

export interface CertificateTemplateAuditItem {
  id: string;
  action: string;
  performedBy: string;
  timestamp: string;
  notes?: string;
}

export interface CertificateTemplate {
  id: string;
  templateName: string;
  certificateType: CertificateType;
  description: string;
  applicableAudience: ("STUDENT" | "FACULTY" | "STAFF" | "ALL")[];
  status: CertificateTemplateStatus;
  version: string;
  fields: CertificateTemplateField[];
  createdDate: string;
  lastUpdated: string;
  usageCount: number;
  versionHistory: CertificateTemplateVersion[];
  activity: CertificateTemplateAuditItem[];
}

export interface CertificateValidationCheck {
  id: string;
  title: string;
  passed: boolean;
  details: string;
}

export interface CertificateRequestTimelineItem {
  id: string;
  status: CertificateRequestStatus;
  title: string;
  performedBy: string;
  timestamp: string;
  notes?: string;
}

export interface CertificateRequest {
  id: string;
  requestId: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  program: string;
  department: string;
  certificateType: CertificateType;
  templateId: string;
  templateName: string;
  purpose: string;
  requestedDate: string;
  requiredByDate?: string;
  status: CertificateRequestStatus;
  reviewerId?: string;
  reviewerName?: string;
  reviewedAt?: string;
  rejectionReason?: string;
  issuedCertificateId?: string;
  issuedDate?: string;
  financeReferenceId?: string;
  validationChecks: CertificateValidationCheck[];
  timeline: CertificateRequestTimelineItem[];
}

export interface IssuedCertificate {
  id: string;
  certificateNumber: string;
  certificateType: CertificateType;
  recipientId: string;
  recipientName: string;
  recipientRollNumber: string;
  recipientProgram: string;
  recipientDepartment: string;
  templateId: string;
  templateVersion: string;
  issuingAuthority: string;
  issueDate: string;
  status: IssuedCertificateStatus;
  qrVerificationUrl: string;
  digitalSignatureHash: string;
  revokedDate?: string;
  revocationReason?: string;
  downloadUrl?: string;
}

export interface InstitutionalRecordAuditItem {
  id: string;
  action: string;
  performedBy: string;
  timestamp: string;
  details?: string;
}

export interface InstitutionalRecord {
  id: string;
  recordName: string;
  code: string;
  category: string;
  ownerDepartment: string;
  confidentiality: ConfidentialityLevel;
  status: InstitutionalRecordStatus;
  createdDate: string;
  validUntil?: string;
  issuingAuthority?: string;
  referenceNumber?: string;
  description?: string;
  fileType?: string;
  fileSize?: string;
  relatedDocumentIds?: string[];
  relatedDocuments?: {
    id: string;
    name: string;
    fileType: string;
    fileSize: string;
  }[];
  activity: InstitutionalRecordAuditItem[];
}

export interface DocumentsDashboardSummary {
  totalDocuments: number;
  verifiedDocuments: number;
  pendingVerification: number;
  rejectedDocuments: number;
  missingDocuments: number;
  expiringDocuments: number;
  certificateRequests: number;
  pendingCertificateRequests: number;
  verificationRate: number;
  rejectionRate: number;
  averageVerificationHours: number;
  documentsUploadedThisMonth: number;
  certificatesIssuedThisMonth: number;
  categoryDistribution: {
    category: string;
    count: number;
    percentage: number;
  }[];
  expiryBreakdown: {
    expired: number;
    expiring7Days: number;
    expiring30Days: number;
    expiring90Days: number;
    valid: number;
    noExpiry: number;
  };
}

// ============================================================================
// 10. INTELLIGENCE & AI ASSISTANT DOMAIN TYPES
// ============================================================================

export enum AIMessageRole {
  USER = "USER",
  ASSISTANT = "ASSISTANT",
  SYSTEM = "SYSTEM",
  TOOL = "TOOL",
}

export enum AIMessageStatus {
  QUEUED = "QUEUED",
  PROCESSING = "PROCESSING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
}

export enum AIResponseBlockType {
  TEXT = "TEXT",
  METRIC = "METRIC",
  TABLE = "TABLE",
  CHART = "CHART",
  LIST = "LIST",
  TIMELINE = "TIMELINE",
  INSIGHT = "INSIGHT",
  WARNING = "WARNING",
  RECOMMENDATION = "RECOMMENDATION",
  SOURCE = "SOURCE",
  ACTION = "ACTION",
}

export enum IntelligenceDomain {
  ALL = "ALL",
  ACADEMICS = "ACADEMICS",
  ATTENDANCE = "ATTENDANCE",
  EXAMINATIONS = "EXAMINATIONS",
  FINANCE = "FINANCE",
  PLACEMENT = "PLACEMENT",
  CAMPUS = "CAMPUS",
  INFRASTRUCTURE = "INFRASTRUCTURE",
  DOCUMENTS = "DOCUMENTS",
  PEOPLE = "PEOPLE",
}

export enum InsightType {
  ACADEMIC = "ACADEMIC",
  ATTENDANCE = "ATTENDANCE",
  EXAMINATION = "EXAMINATION",
  FINANCE = "FINANCE",
  PLACEMENT = "PLACEMENT",
  CAMPUS = "CAMPUS",
  INFRASTRUCTURE = "INFRASTRUCTURE",
  DOCUMENT = "DOCUMENT",
  STUDENT = "STUDENT",
}

export enum InsightPriority {
  INFO = "INFO",
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum InsightStatus {
  NEW = "NEW",
  REVIEWED = "REVIEWED",
  DISMISSED = "DISMISSED",
  ACTIONED = "ACTIONED",
}

export enum AlertType {
  ATTENDANCE = "ATTENDANCE",
  ACADEMIC = "ACADEMIC",
  EXAMINATION = "EXAMINATION",
  FINANCE = "FINANCE",
  PLACEMENT = "PLACEMENT",
  INFRASTRUCTURE = "INFRASTRUCTURE",
  DOCUMENT = "DOCUMENT",
  SYSTEM = "SYSTEM",
}

export enum AlertSeverity {
  INFO = "INFO",
  WARNING = "WARNING",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum AlertStatus {
  OPEN = "OPEN",
  ACKNOWLEDGED = "ACKNOWLEDGED",
  RESOLVED = "RESOLVED",
  DISMISSED = "DISMISSED",
}

export enum AIActivityStatus {
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  CANCELLED = "CANCELLED",
}

export enum AIToolPermission {
  ALL = "ALL",
  STUDENT = "STUDENT",
  FACULTY = "FACULTY",
  HOD = "HOD",
  ACCOUNTS = "ACCOUNTS",
  PLACEMENT_OFFICER = "PLACEMENT_OFFICER",
  ADMIN = "ADMIN",
}

export interface AIResponseBlock {
  type: AIResponseBlockType;
  title?: string;
  content?: string;
  metrics?: {
    label: string;
    value: string | number;
    change?: string;
    trend?: "up" | "down" | "neutral";
  }[];
  table?: {
    headers: string[];
    rows: (string | number)[][];
  };
  chart?: {
    type: "bar" | "line" | "pie" | "donut";
    labels: string[];
    datasets: {
      name: string;
      data: number[];
      color?: string;
    }[];
  };
  list?: string[];
  timeline?: {
    time: string;
    title: string;
    description?: string;
  }[];
  actions?: {
    label: string;
    href?: string;
    actionId?: string;
    variant?: "primary" | "secondary" | "danger";
  }[];
}

export interface AISource {
  name: string;
  domain: IntelligenceDomain | string;
  href: string;
  description: string;
}

export interface AIExplainability {
  dataSources: string[];
  filtersApplied: string[];
  timePeriod: string;
  calculationUsed: string;
  threshold?: string;
  result: string;
}

export interface AIMessage {
  id: string;
  conversationId: string;
  role: AIMessageRole;
  status: AIMessageStatus;
  content: string;
  timestamp: string;
  blocks?: AIResponseBlock[];
  sources?: AISource[];
  suggestedActions?: {
    label: string;
    href: string;
  }[];
  explainability?: AIExplainability;
}

export interface AIConversation {
  id: string;
  title: string;
  domain: IntelligenceDomain;
  isPinned: boolean;
  isArchived: boolean;
  isSaved: boolean;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  lastMessageSnippet: string;
}

export interface AIQueryContext {
  studentId?: string;
  departmentId?: string;
  programId?: string;
  semester?: number;
  courseId?: string;
  eventId?: string;
  hostelId?: string;
  routeId?: string;
  documentId?: string;
  role?: string;
  userName?: string;
}

export interface AIQuery {
  query: string;
  domain?: IntelligenceDomain;
  context?: AIQueryContext;
  conversationId?: string;
}

export interface AIResponse {
  id: string;
  query: string;
  reply: string;
  blocks: AIResponseBlock[];
  sources: AISource[];
  explainability: AIExplainability;
  suggestedActions: {
    label: string;
    href: string;
  }[];
  executionTimeMs: number;
  toolName?: string;
}

export interface AITool {
  name: string;
  domain: IntelligenceDomain;
  description: string;
  permissionRequirement: AIToolPermission;
  status: "ACTIVE" | "MAINTENANCE" | "DEPRECATED";
  lastUsed: string;
  executionCount: number;
  parameters?: {
    name: string;
    type: string;
    required: boolean;
    description: string;
  }[];
}

export interface AIToolExecution {
  id: string;
  toolName: string;
  timestamp: string;
  user: string;
  role: string;
  durationMs: number;
  status: "SUCCESS" | "FAILED";
  inputParameters: Record<string, any>;
  recordsReturned: number;
}

export interface Insight {
  id: string;
  title: string;
  type: InsightType;
  domain: IntelligenceDomain;
  priority: InsightPriority;
  status: InsightStatus;
  summary: string;
  affectedRecordCount: number;
  affectedRecords?: {
    id: string;
    name: string;
    type: string;
    href: string;
  }[];
  detectedAt: string;
  recommendedAction: string;
  recommendedActionHref?: string;
  evidence?: {
    metric: string;
    value: string;
    baseline?: string;
  }[];
  methodology?: string;
  relatedDomainHref?: string;
  isSaved?: boolean;
  activityTimeline?: {
    action: string;
    actor: string;
    timestamp: string;
    notes?: string;
  }[];
}

export interface Alert {
  id: string;
  title: string;
  type: AlertType;
  domain: IntelligenceDomain;
  severity: AlertSeverity;
  status: AlertStatus;
  detectedAt: string;
  affectedCount: number;
  affectedRecords?: {
    id: string;
    name: string;
    type: string;
    href: string;
  }[];
  sourceDomain: string;
  reason: string;
  recommendedAction: string;
  recommendedActionHref?: string;
  acknowledgedAt?: string | null;
  acknowledgedBy?: string | null;
  resolvedAt?: string | null;
  resolvedBy?: string | null;
  activityTimeline?: {
    action: string;
    actor: string;
    timestamp: string;
    notes?: string;
  }[];
}

export interface SavedInsight {
  id: string;
  title: string;
  type: "AI_RESPONSE" | "INSIGHT" | "ANALYTICS_VIEW" | "REPORT";
  domain: IntelligenceDomain;
  savedAt: string;
  ownerName: string;
  ownerRole: string;
  lastAccessedAt: string;
  contentSnippet: string;
  href: string;
}

export interface AnalyticsQuery {
  domain: IntelligenceDomain;
  metric: string;
  dimension: string;
  timeRange: string;
  filters?: Record<string, string | number>;
}

export interface AnalyticsResult {
  query: AnalyticsQuery;
  title: string;
  summary: string;
  chartType: "bar" | "line" | "pie" | "donut" | "table";
  labels: string[];
  datasets: {
    name: string;
    data: number[];
    color?: string;
  }[];
  tableData?: {
    headers: string[];
    rows: (string | number)[][];
  };
}

export interface AIActivity {
  id: string;
  timestamp: string;
  userName: string;
  userRole: string;
  query: string;
  domain: IntelligenceDomain;
  toolsInvoked: string[];
  resultSummary: string;
  durationMs: number;
  status: AIActivityStatus;
  dataSources: string[];
  contextSummary?: string;
}

export interface IntelligenceOverviewSummary {
  activeInsights: number;
  criticalAlerts: number;
  studentsRequiringAttention: number;
  attendanceRiskCases: number;
  academicRiskCases: number;
  financeRiskCases: number;
  placementOpportunities: number;
  infrastructureIssues: number;
  totalQueriesRun: number;
  averageQueryDurationMs: number;
  domainSummaries: Record<
    string,
    {
      healthScore: number;
      status: "EXCELLENT" | "GOOD" | "ATTENTION" | "CRITICAL";
      summary: string;
      activeAlerts: number;
      primaryMetric: string;
    }
  >;
}

export interface StudentIntelligenceProfile {
  studentId: string;
  studentName: string;
  rollNumber: string;
  department: string;
  program: string;
  semester: number;
  attendanceRisk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  attendancePercentage: number;
  academicTrend: "IMPROVING" | "STABLE" | "DECLINING";
  cgpa: number;
  failedSubjectsCount: number;
  financeStatus: "CLEAR" | "PENDING" | "OVERDUE";
  outstandingBalance: number;
  placementReadiness: "NOT_ELIGIBLE" | "PREPARING" | "READY" | "PLACED";
  documentCompletionRate: number;
  missingDocumentsCount: number;
  campusEngagement: "LOW" | "MODERATE" | "HIGH" | "VERY_HIGH";
  clubMemberships: number;
  eventParticipations: number;
  recommendedActions: string[];
}

export interface DepartmentHealthSummary {
  departmentId: string;
  departmentName: string;
  studentCount: number;
  facultyCount: number;
  avgAttendance: number;
  avgCgpa: number;
  placementRate: number;
  feeCollectionRate: number;
  campusEngagementScore: number;
  documentCompletionRate: number;
  openComplaintsCount: number;
  status: "EXCELLENT" | "GOOD" | "ATTENTION" | "CRITICAL";
}

export interface CampusHealthMetric {
  domain: IntelligenceDomain;
  label: string;
  currentValue: string | number;
  targetValue: string | number;
  trend: "up" | "down" | "neutral";
  trendDescription: string;
  alertCount: number;
  healthScore: number;
  status: "EXCELLENT" | "GOOD" | "ATTENTION" | "CRITICAL";
}

/**
 * Workflow and Automation Engine Types
 */
export type WorkflowStatus = "DRAFT" | "ACTIVE" | "PAUSED" | "ARCHIVED";
export type WorkflowTriggerType = "SCHEDULE" | "EVENT" | "MANUAL";
export type ExecutionStatus = "QUEUED" | "RUNNING" | "WAITING" | "SUCCEEDED" | "FAILED" | "CANCELLED";
export type ExecutionStepStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED" | "SKIPPED";

export interface WorkflowTriggerDefinition {
  trigger_type: WorkflowTriggerType;
  event_type?: string | null;
  cron_expression?: string | null;
  interval_seconds?: number | null;
  schedule_time?: string | null;
  days_of_week?: number[] | null;
  config?: Record<string, unknown>;
}

export interface WorkflowStepDefinition {
  id: string;
  name: string;
  step_type: "CONDITION" | "ACTION" | "NOTIFICATION" | "WAIT";
  condition?: Record<string, unknown> | null;
  action_type?: string | null;
  parameters?: Record<string, unknown>;
  next_step_id?: string | null;
  on_failure_step_id?: string | null;
}

export interface WorkflowVersion {
  id: UUID;
  workflow_id: UUID;
  version: number;
  is_active: boolean;
  change_summary?: string | null;
  trigger_definition: WorkflowTriggerDefinition;
  steps_definition: WorkflowStepDefinition[];
  created_at: string;
}

export interface Workflow {
  id: UUID;
  tenant_id: UUID;
  name: string;
  description?: string | null;
  domain: string;
  status: WorkflowStatus;
  is_system: boolean;
  active_version: number;
  current_version_id?: UUID | null;
  created_by?: UUID | null;
  updated_by?: UUID | null;
  created_at: string;
  updated_at: string;
  versions?: WorkflowVersion[];
}

export interface WorkflowExecutionStep {
  id: UUID;
  step_id: string;
  step_type: string;
  action_type?: string | null;
  status: ExecutionStepStatus;
  started_at: string;
  completed_at?: string | null;
  attempt_count: number;
  input_data?: Record<string, unknown> | null;
  output_data?: Record<string, unknown> | null;
  error_message?: string | null;
}

export interface WorkflowExecution {
  id: UUID;
  tenant_id: UUID;
  workflow_id: UUID;
  workflow_version_id: UUID;
  trigger_type: WorkflowTriggerType;
  trigger_reference?: string | null;
  idempotency_key?: string | null;
  status: ExecutionStatus;
  started_at: string;
  completed_at?: string | null;
  attempt_count: number;
  max_retries: number;
  correlation_id?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  steps?: WorkflowExecutionStep[];
}

export interface WorkflowOperationalMetrics {
  active_workflows: number;
  paused_workflows: number;
  draft_workflows: number;
  archived_workflows: number;
  executions_today: number;
  successful_executions: number;
  failed_executions: number;
  dead_letter_count: number;
  queue_depth: number;
}

// ============================================================================
// Step 18 — Enterprise Reporting & Analytics Types
// ============================================================================

export type ReportStatus = "DRAFT" | "ACTIVE" | "ARCHIVED";
export type ReportVisibility = "PRIVATE" | "ROLE" | "TENANT" | "SYSTEM";
export type ReportExecutionStatus = "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED" | "EXPIRED";
export type ReportExportFormat = "CSV" | "XLSX" | "PDF" | "JSON";

export interface FilterCondition {
  field: string;
  operator: string;
  value?: unknown;
}

export interface DateRangeFilter {
  preset?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface AcademicPeriodFilter {
  academic_year_id?: UUID | null;
  semester_id?: UUID | null;
  department_id?: UUID | null;
  program_id?: UUID | null;
}

export interface QuerySpecification {
  dataset: string;
  dimensions?: string[];
  measures: string[];
  filters?: FilterCondition[];
  date_range?: DateRangeFilter | null;
  academic_period?: AcademicPeriodFilter | null;
  sort_by?: string | null;
  sort_desc?: boolean;
  limit?: number;
  offset?: number;
}

export interface ReportVersion {
  id: UUID;
  version_number: number;
  change_summary?: string | null;
  query_spec_json: QuerySpecification;
  is_active: boolean;
  created_at: string;
}

export interface ReportDefinition {
  id: UUID;
  tenant_id?: UUID | null;
  name: string;
  code: string;
  description?: string | null;
  domain: string;
  category: string;
  status: ReportStatus;
  visibility: ReportVisibility;
  is_system: boolean;
  allowed_roles: string[];
  active_version: number;
  active_version_id?: UUID | null;
  created_at: string;
  updated_at: string;
  versions?: ReportVersion[];
}

export interface ReportExecution {
  id: UUID;
  tenant_id: UUID;
  report_id?: UUID | null;
  report_version_id?: UUID | null;
  requested_by_user_id?: UUID | null;
  status: ReportExecutionStatus;
  row_count: number;
  execution_time_ms: number;
  error_code?: string | null;
  error_message?: string | null;
  correlation_id: string;
  is_snapshot: boolean;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export interface ReportExport {
  id: UUID;
  tenant_id: UUID;
  execution_id: UUID;
  export_format: ReportExportFormat;
  storage_key: string;
  filename: string;
  mime_type: string;
  file_size_bytes: number;
  download_count: number;
  expires_at: string;
  created_at: string;
  download_url?: string | null;
}

export interface SavedReport {
  id: UUID;
  tenant_id: UUID;
  user_id: UUID;
  report_id?: UUID | null;
  name: string;
  description?: string | null;
  query_spec_json: QuerySpecification;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChartSeries {
  name: string;
  data: (number | string)[];
  color?: string | null;
}

export interface AnalyticsTableData {
  headers: string[];
  rows: (number | string)[][];
  total_rows?: number;
}

export interface SourceProvenance {
  dataset: string;
  measures: string[];
  dimensions: string[];
  reporting_period: string;
  generated_at: string;
  data_as_of: string;
  tenant_id: string;
}

export interface AnalyticsQueryResult {
  query: QuerySpecification;
  title: string;
  summary: string;
  chart_type: string;
  labels: string[];
  datasets: ChartSeries[];
  table_data: AnalyticsTableData;
  provenance: SourceProvenance;
  cached?: boolean;
}

/**
 * ============================================================================
 * Step 19: Enterprise Data Governance, Privacy & Compliance Layer Types
 * ============================================================================
 */

export enum DataClassificationLevel {
  PUBLIC = "PUBLIC",
  INTERNAL = "INTERNAL",
  CONFIDENTIAL = "CONFIDENTIAL",
  RESTRICTED = "RESTRICTED",
  SENSITIVE = "SENSITIVE",
}

export enum MaskingStrategy {
  NONE = "NONE",
  FULL_MASK = "FULL_MASK",
  PARTIAL_MASK = "PARTIAL_MASK",
  EMAIL_MASK = "EMAIL_MASK",
  PHONE_MASK = "PHONE_MASK",
  IDENTIFIER_MASK = "IDENTIFIER_MASK",
  REDACT = "REDACT",
  HASH = "HASH",
}

export enum GovernancePolicyCategory {
  DATA_CLASSIFICATION = "DATA_CLASSIFICATION",
  RETENTION = "RETENTION",
  ACCESS = "ACCESS",
  EXPORT = "EXPORT",
  PRIVACY = "PRIVACY",
  ARCHIVAL = "ARCHIVAL",
  DELETION = "DELETION",
  DOCUMENT = "DOCUMENT",
  REPORTING = "REPORTING",
  AI = "AI",
}

export enum GovernancePolicyStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  SUSPENDED = "SUSPENDED",
  RETIRED = "RETIRED",
}

export enum RetentionAction {
  RETAIN = "RETAIN",
  ARCHIVE = "ARCHIVE",
  ANONYMIZE = "ANONYMIZE",
  DELETE = "DELETE",
  REVIEW = "REVIEW",
}

export enum RetentionUnit {
  DAYS = "DAYS",
  MONTHS = "MONTHS",
  YEARS = "YEARS",
  PERMANENT = "PERMANENT",
}

export enum RetentionTriggerEvent {
  CREATION = "CREATION",
  COMPLETION = "COMPLETION",
  GRADUATION = "GRADUATION",
  EXPIRATION = "EXPIRATION",
  DEACTIVATION = "DEACTIVATION",
  TERMINATION = "TERMINATION",
  FY_CLOSE = "FY_CLOSE",
  CONTRACT_EXPIRY = "CONTRACT_EXPIRY",
  CASE_CLOSURE = "CASE_CLOSURE",
}

export enum HoldStatus {
  ACTIVE = "ACTIVE",
  RELEASED = "RELEASED",
  EXPIRED = "EXPIRED",
}

export enum PrivacyRequestType {
  ACCESS = "ACCESS",
  EXPORT = "EXPORT",
  CORRECTION = "CORRECTION",
  RESTRICTION = "RESTRICTION",
  DELETION = "DELETION",
  REVIEW = "REVIEW",
}

export enum PrivacyRequestStatus {
  SUBMITTED = "SUBMITTED",
  UNDER_REVIEW = "UNDER_REVIEW",
  IDENTITY_VERIFICATION_REQUIRED = "IDENTITY_VERIFICATION_REQUIRED",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED",
  CANCELLED = "CANCELLED",
}

export enum AccessReviewStatus {
  OPEN = "OPEN",
  IN_REVIEW = "IN_REVIEW",
  COMPLETED = "COMPLETED",
  EXPIRED = "EXPIRED",
}

export enum AccessReviewDecisionType {
  PENDING = "PENDING",
  RETAIN = "RETAIN",
  REVOKE = "REVOKE",
  MODIFY = "MODIFY",
  ESCALATE = "ESCALATE",
}

export interface ClassificationTier {
  level: DataClassificationLevel;
  name: string;
  description: string;
  sensitivity_rank: number;
  export_requires_approval: boolean;
  requires_masking_in_logs: boolean;
  ai_visibility_allowed: boolean;
}

export interface SensitiveFieldInfo {
  entity: string;
  field: string;
  classification: DataClassificationLevel;
  masking_strategy: MaskingStrategy;
  export_allowed: boolean;
  log_visibility: boolean;
  ai_visibility: boolean;
  allowed_roles: string[];
}

export interface GovernancePolicyModel {
  id: UUID;
  tenant_id: UUID;
  name: string;
  code: string;
  category: GovernancePolicyCategory;
  description?: string | null;
  status: GovernancePolicyStatus;
  is_system_default: boolean;
  active_version_id?: UUID | null;
  created_by_user_id?: UUID | null;
  updated_by_user_id?: UUID | null;
  created_at: string;
  updated_at: string;
  active_version?: GovernancePolicyVersionModel | null;
}

export interface GovernancePolicyVersionModel {
  id: UUID;
  tenant_id: UUID;
  policy_id: UUID;
  version_number: number;
  status: GovernancePolicyStatus;
  rules_json: Record<string, unknown> | unknown[];
  change_summary?: string | null;
  effective_from: string;
  effective_until?: string | null;
  created_by_user_id?: UUID | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RetentionPolicyModel {
  id: UUID;
  tenant_id: UUID;
  policy_id?: UUID | null;
  name: string;
  resource_type: string;
  retention_period: number;
  retention_unit: RetentionUnit;
  trigger_event: RetentionTriggerEvent;
  action: RetentionAction;
  archive_after_days?: number | null;
  delete_after_days?: number | null;
  legal_hold_behavior: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RetentionDecisionResult {
  resource_id: UUID;
  resource_type: string;
  policy_id?: UUID | null;
  decision: RetentionAction | "NONE";
  eligible_at?: string | null;
  is_blocked: boolean;
  blocked_reason?: string | null;
  active_holds: string[];
  dependency_blocks: string[];
}

export interface GovernanceHoldModel {
  id: UUID;
  tenant_id: UUID;
  name: string;
  case_reference?: string | null;
  target_entity_type: string;
  target_entity_id?: UUID | null;
  reason: string;
  status: HoldStatus;
  expires_at?: string | null;
  created_by_user_id?: UUID | null;
  released_by_user_id?: UUID | null;
  released_at?: string | null;
  release_reason?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PrivacyRequestModel {
  id: UUID;
  tenant_id: UUID;
  request_number: string;
  request_type: PrivacyRequestType;
  status: PrivacyRequestStatus;
  data_subject_type: string;
  data_subject_id: UUID;
  requested_by_user_id: UUID;
  reviewed_by_user_id?: UUID | null;
  description?: string | null;
  evidence_notes?: string | null;
  rejection_reason?: string | null;
  target_domains: string[];
  export_storage_key?: string | null;
  export_expires_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PrivacyRequestActionModel {
  id: UUID;
  tenant_id: UUID;
  request_id: UUID;
  action_type: string;
  domain: string;
  entity_type: string;
  entity_id?: UUID | null;
  status: string;
  blocked_reason?: string | null;
  performed_by_user_id?: UUID | null;
  performed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AccessReviewModel {
  id: UUID;
  tenant_id: UUID;
  title: string;
  description?: string | null;
  review_type: string;
  status: AccessReviewStatus;
  due_date: string;
  reviewer_user_id?: UUID | null;
  completed_at?: string | null;
  total_items?: number;
  decided_items?: number;
  created_at: string;
  updated_at: string;
}

export interface AccessReviewItemModel {
  id: UUID;
  tenant_id: UUID;
  review_id: UUID;
  user_id: UUID;
  role_id?: UUID | null;
  permission_name?: string | null;
  decision: AccessReviewDecisionType;
  decision_notes?: string | null;
  decided_by_user_id?: UUID | null;
  decided_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface GovernanceSummaryMetrics {
  active_policies_count: number;
  active_holds_count: number;
  open_privacy_requests_count: number;
  open_access_reviews_count: number;
  records_approaching_retention_count: number;
  blocked_deletions_count: number;
  sensitive_fields_registered_count: number;
  classification_tiers_count: number;
}

// ----------------------------------------------------------------------------
// Step 35: Enterprise Product Readiness, Tenant Acceptance & Go-Live Orchestration
// ----------------------------------------------------------------------------

export enum OnboardingLifecycleState {
  DRAFT = "DRAFT",
  PROVISIONING = "PROVISIONING",
  CONFIGURATION = "CONFIGURATION",
  DATA_VALIDATION = "DATA_VALIDATION",
  INTEGRATION_VALIDATION = "INTEGRATION_VALIDATION",
  USER_ACCEPTANCE_TESTING = "USER_ACCEPTANCE_TESTING",
  READINESS_REVIEW = "READINESS_REVIEW",
  APPROVED_FOR_GO_LIVE = "APPROVED_FOR_GO_LIVE",
  LIVE = "LIVE",
  BLOCKED = "BLOCKED",
  REJECTED = "REJECTED",
  ON_HOLD = "ON_HOLD",
  ROLLBACK_IN_PROGRESS = "ROLLBACK_IN_PROGRESS",
  SUSPENDED = "SUSPENDED",
  CLOSED = "CLOSED",
}

export enum ChecklistCategory {
  PLATFORM_SETUP = "PLATFORM_SETUP",
  IDENTITY_ACCESS = "IDENTITY_ACCESS",
  ACADEMIC_CONFIG = "ACADEMIC_CONFIG",
  FINANCE = "FINANCE",
  DATA_MIGRATION = "DATA_MIGRATION",
  INTEGRATIONS_COMMS = "INTEGRATIONS_COMMS",
  SECURITY_OPERATIONS = "SECURITY_OPERATIONS",
}

export enum ChecklistStatus {
  NOT_STARTED = "NOT_STARTED",
  IN_PROGRESS = "IN_PROGRESS",
  PASSED = "PASSED",
  FAILED = "FAILED",
  BLOCKED = "BLOCKED",
  WAIVED = "WAIVED",
}

export enum VerificationMethod {
  AUTOMATED = "AUTOMATED",
  MANUAL_REVIEW = "MANUAL_REVIEW",
  ATTESTATION = "ATTESTATION",
  INTEGRATION_PROBE = "INTEGRATION_PROBE",
}

export enum MigrationJobStatus {
  PENDING = "PENDING",
  SCHEMA_VALIDATED = "SCHEMA_VALIDATED",
  DRY_RUN_COMPLETED = "DRY_RUN_COMPLETED",
  IMPORTING = "IMPORTING",
  RECONCILED = "RECONCILED",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
}

export enum UATScenarioStatus {
  UNVERIFIED = "UNVERIFIED",
  PASSED = "PASSED",
  FAILED = "FAILED",
  BLOCKED = "BLOCKED",
}

export enum DefectSeverity {
  CRITICAL = "CRITICAL",
  MAJOR = "MAJOR",
  MINOR = "MINOR",
  NONE = "NONE",
}

export enum ApprovalRole {
  INSTITUTION_OWNER = "INSTITUTION_OWNER",
  DATA_MIGRATION_OWNER = "DATA_MIGRATION_OWNER",
  TECHNICAL_OPERATIONS_REVIEWER = "TECHNICAL_OPERATIONS_REVIEWER",
  SECURITY_REVIEWER = "SECURITY_REVIEWER",
  BUSINESS_ACCEPTANCE_REPRESENTATIVE = "BUSINESS_ACCEPTANCE_REPRESENTATIVE",
  PLATFORM_RELEASE_APPROVER = "PLATFORM_RELEASE_APPROVER",
}

export enum ApprovalDecision {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  INVALIDATED = "INVALIDATED",
}

export interface TenantOnboardingPlanModel {
  id: UUID;
  tenant_id: UUID;
  current_state: OnboardingLifecycleState | string;
  previous_state?: string | null;
  target_go_live_date?: string | null;
  actual_go_live_date?: string | null;
  assigned_lead_email?: string | null;
  state_reason?: string | null;
  rollback_reason?: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface OnboardingChecklistItemModel {
  id: UUID;
  plan_id: UUID;
  tenant_id: UUID;
  item_code: string;
  category: ChecklistCategory | string;
  title: string;
  description: string;
  is_required: boolean;
  verification_method: VerificationMethod | string;
  status: ChecklistStatus | string;
  evidence_ref?: string | null;
  responsible_owner?: string | null;
  completed_at?: string | null;
  verified_at?: string | null;
  blocker_reason?: string | null;
  waiver_reason?: string | null;
  waiver_approved_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReadinessEvaluationResult {
  overall_status: "READY" | "BLOCKED" | "ACTION_REQUIRED" | string;
  can_progress_to_next_stage: boolean;
  current_state: string;
  next_recommended_state?: string | null;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  blocked_checks: number;
  waived_checks: number;
  completed_requirements: string[];
  failed_requirements: string[];
  blocked_requirements: string[];
  missing_evidence: string[];
  outstanding_approvals: string[];
  blocking_reasons: string[];
  recommended_actions: string[];
}

export interface OnboardingMigrationJobModel {
  id: UUID;
  plan_id: UUID;
  tenant_id: UUID;
  domain_name: string;
  source_filename: string;
  source_checksum: string;
  status: MigrationJobStatus | string;
  source_record_count: number;
  accepted_record_count: number;
  rejected_record_count: number;
  duplicate_record_count: number;
  imported_record_count: number;
  reconciliation_diff_count: number;
  failed_batches_count: number;
  unresolved_exceptions_count: number;
  dry_run: boolean;
  validation_findings: Array<Record<string, unknown>>;
  reconciliation_summary: Record<string, unknown>;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OnboardingUATScenarioModel {
  id: UUID;
  plan_id: UUID;
  tenant_id: UUID;
  scenario_code: string;
  module: string;
  title: string;
  expected_outcome: string;
  assigned_tester_email?: string | null;
  status: UATScenarioStatus | string;
  evidence_ref?: string | null;
  defect_severity: DefectSeverity | string;
  defect_description?: string | null;
  retest_notes?: string | null;
  sign_off_by?: string | null;
  sign_off_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OnboardingApprovalModel {
  id: UUID;
  plan_id: UUID;
  tenant_id: UUID;
  role: ApprovalRole | string;
  decision: ApprovalDecision | string;
  approver_id?: UUID | null;
  approver_email?: string | null;
  comments?: string | null;
  rejection_reason?: string | null;
  policy_version: string;
  decision_at?: string | null;
  invalidated_at?: string | null;
  invalidation_reason?: string | null;
  created_at: string;
}

export interface OnboardingHypercareRecordModel {
  id: UUID;
  plan_id: UUID;
  tenant_id: UUID;
  hypercare_start_at: string;
  hypercare_end_at: string;
  assigned_support_lead: string;
  escalation_contacts: Array<Record<string, unknown>>;
  is_active: boolean;
  daily_summaries: Array<Record<string, unknown>>;
  unresolved_issues_count: number;
  auth_failure_count: number;
  api_error_count: number;
  integration_failure_count: number;
  job_failure_count: number;
  exit_criteria_met: boolean;
  handoff_completed_at?: string | null;
  handoff_signoff_by?: string | null;
}

// =============================================================================
// STEP 36: ENTERPRISE CUSTOMER SUPPORT, SERVICE DESK & SLA MANAGEMENT
// =============================================================================

export enum SupportTicketStatus {
  NEW = "NEW",
  TRIAGED = "TRIAGED",
  ASSIGNED = "ASSIGNED",
  IN_PROGRESS = "IN_PROGRESS",
  WAITING_FOR_REQUESTER = "WAITING_FOR_REQUESTER",
  WAITING_FOR_ENGINEERING = "WAITING_FOR_ENGINEERING",
  RESOLVED = "RESOLVED",
  CLOSED = "CLOSED",
  REOPENED = "REOPENED",
  ESCALATED = "ESCALATED",
  ON_HOLD = "ON_HOLD",
  CANCELLED = "CANCELLED",
}

export enum SupportPriority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  URGENT = "URGENT",
}

export enum SupportSeverity {
  SEV_1_CRITICAL = "SEV_1_CRITICAL",
  SEV_2_MAJOR = "SEV_2_MAJOR",
  SEV_3_MODERATE = "SEV_3_MODERATE",
  SEV_4_MINOR = "SEV_4_MINOR",
}

export enum SupportRequestType {
  INCIDENT = "INCIDENT",
  SERVICE_REQUEST = "SERVICE_REQUEST",
  ACCESS_REQUEST = "ACCESS_REQUEST",
  CONFIGURATION_REQUEST = "CONFIGURATION_REQUEST",
  DATA_CORRECTION = "DATA_CORRECTION",
  FEATURE_REQUEST = "FEATURE_REQUEST",
}

export enum SupportCategory {
  ACCOUNT_ACCESS = "ACCOUNT_ACCESS",
  STUDENT_STAFF_ADMIN = "STUDENT_STAFF_ADMIN",
  ACADEMIC_CONFIG = "ACADEMIC_CONFIG",
  ATTENDANCE = "ATTENDANCE",
  EXAMINATIONS = "EXAMINATIONS",
  FINANCE_FEES = "FINANCE_FEES",
  PLACEMENTS = "PLACEMENTS",
  CAMPUS_OPERATIONS = "CAMPUS_OPERATIONS",
  DOCUMENTS_RECORDS = "DOCUMENTS_RECORDS",
  REPORTS_ANALYTICS = "REPORTS_ANALYTICS",
  INTEGRATIONS_APIS = "INTEGRATIONS_APIS",
  AI_FEATURES = "AI_FEATURES",
  PERFORMANCE_AVAILABILITY = "PERFORMANCE_AVAILABILITY",
  DATA_MIGRATION_ONBOARDING = "DATA_MIGRATION_ONBOARDING",
  FEATURE_REQUEST = "FEATURE_REQUEST",
  GENERAL_ASSISTANCE = "GENERAL_ASSISTANCE",
}

export enum RequesterType {
  STUDENT = "STUDENT",
  FACULTY = "FACULTY",
  STAFF = "STAFF",
  INSTITUTION_ADMIN = "INSTITUTION_ADMIN",
  PLATFORM_OPERATOR = "PLATFORM_OPERATOR",
}

export enum SupportMessageType {
  PUBLIC_REPLY = "PUBLIC_REPLY",
  INTERNAL_NOTE = "INTERNAL_NOTE",
}

export enum SupportSlaState {
  ON_TRACK = "ON_TRACK",
  AT_RISK = "AT_RISK",
  BREACHED = "BREACHED",
  PAUSED = "PAUSED",
  MET = "MET",
  UNCONFIGURED = "UNCONFIGURED",
}

export interface SupportTicketMessageModel {
  id: UUID;
  ticket_id: UUID;
  sender_id: UUID;
  sender_email: string;
  sender_name: string;
  sender_role: string;
  message_type: SupportMessageType | string;
  body: string;
  attachments_json: Array<Record<string, unknown>>;
  created_at: string;
}

export interface SupportTicketTimelineModel {
  id: UUID;
  ticket_id: UUID;
  event_type: string;
  actor_id?: UUID | null;
  actor_email?: string | null;
  from_status?: string | null;
  to_status?: string | null;
  summary: string;
  details_json: Record<string, unknown>;
  created_at: string;
}

export interface SupportTicketArticleLinkModel {
  id: UUID;
  ticket_id: UUID;
  article_id: string;
  article_title: string;
  article_url: string;
  relevance_score: number;
  was_helpful?: boolean | null;
  created_at: string;
}

export interface SupportTeamModel {
  id: UUID;
  tenant_id?: UUID | null;
  code: string;
  name: string;
  description?: string | null;
  specialization_modules: string[];
  is_active: boolean;
  is_platform_team: boolean;
  created_at: string;
}

export interface SupportSlaPolicyModel {
  id: UUID;
  tenant_id?: UUID | null;
  name: string;
  description?: string | null;
  service_plan: string;
  priority: SupportPriority | string;
  severity?: SupportSeverity | string | null;
  category?: SupportCategory | string | null;
  response_target_minutes: number;
  resolution_target_minutes: number;
  business_hours_only: boolean;
  escalation_threshold_pct: number;
  is_active: boolean;
  created_at: string;
}

export interface SupportTicketModel {
  id: UUID;
  tenant_id?: UUID | null;
  ticket_number: string;
  requester_id: UUID;
  requester_email: string;
  requester_name: string;
  requester_type: RequesterType | string;
  subject: string;
  category: SupportCategory | string;
  subcategory?: string | null;
  request_type: SupportRequestType | string;
  priority: SupportPriority | string;
  severity: SupportSeverity | string;
  status: SupportTicketStatus | string;
  assigned_team_id?: UUID | null;
  assigned_team_name?: string | null;
  assigned_agent_id?: UUID | null;
  assigned_agent_email?: string | null;
  related_erp_module?: string | null;
  related_incident_id?: string | null;
  related_security_incident_id?: UUID | null;
  response_due_at?: string | null;
  resolution_due_at?: string | null;
  first_response_at?: string | null;
  resolved_at?: string | null;
  closed_at?: string | null;
  sla_response_status: SupportSlaState | string;
  sla_resolution_status: SupportSlaState | string;
  reopen_count: number;
  escalation_level: number;
  csat_rating?: number | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface SupportTicketDetailModel extends SupportTicketModel {
  description: string;
  resolution_summary?: string | null;
  closure_reason?: string | null;
  reopen_reason?: string | null;
  escalation_reason?: string | null;
  cancellation_reason?: string | null;
  csat_feedback?: string | null;
  csat_submitted_at?: string | null;
  attachments_json: Array<Record<string, unknown>>;
  messages: SupportTicketMessageModel[];
  timeline: SupportTicketTimelineModel[];
  kb_links: SupportTicketArticleLinkModel[];
}

export interface SupportAnalyticsMetricsModel {
  total_tickets_created: number;
  total_tickets_resolved: number;
  open_backlog_count: number;
  urgent_priority_count: number;
  average_first_response_minutes: number;
  average_resolution_minutes: number;
  sla_compliance_rate_pct: number;
  escalation_rate_pct: number;
  reopen_rate_pct: number;
  csat_average_score: number;
  csat_response_count: number;
  tickets_by_category: Record<string, number>;
  tickets_by_priority: Record<string, number>;
  tickets_by_status: Record<string, number>;
}

/**
 * Step 37: Enterprise Product Adoption, Training, In-App Guidance & Change Management Types
 */

export enum JourneyStatus {
  DRAFT = "DRAFT",
  PUBLISHED = "PUBLISHED",
  ARCHIVED = "ARCHIVED",
}

export enum StepCompletionCriteria {
  ACTION_COMPLETED = "ACTION_COMPLETED",
  VIEW_RESOURCE = "VIEW_RESOURCE",
  CONFIRM_CHECKLIST = "CONFIRM_CHECKLIST",
  TRAINING_COMPLETED = "TRAINING_COMPLETED",
}

export enum UserJourneyState {
  NOT_STARTED = "NOT_STARTED",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  ABANDONED = "ABANDONED",
}

export enum TrainingProgramStatus {
  DRAFT = "DRAFT",
  PUBLISHED = "PUBLISHED",
  ARCHIVED = "ARCHIVED",
}

export enum TrainingModuleContentType {
  TEXT_INSTRUCTION = "TEXT_INSTRUCTION",
  EXTERNAL_LINK = "EXTERNAL_LINK",
  DOCUMENT_REF = "DOCUMENT_REF",
  VIDEO_LINK = "VIDEO_LINK",
}

export enum TrainingAssignmentStatus {
  ASSIGNED = "ASSIGNED",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  OVERDUE = "OVERDUE",
  EXPIRED = "EXPIRED",
}

export enum GuidanceType {
  TOOLTIP = "TOOLTIP",
  WALKTHROUGH = "WALKTHROUGH",
  MODAL = "MODAL",
  BANNER = "BANNER",
}

export enum GuidanceStatus {
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  EXPIRED = "EXPIRED",
}

export enum UserGuidanceAction {
  SEEN = "SEEN",
  DISMISSED = "DISMISSED",
  COMPLETED = "COMPLETED",
}

export enum ProductAnnouncementCategory {
  FEATURE_RELEASE = "FEATURE_RELEASE",
  WORKFLOW_CHANGE = "WORKFLOW_CHANGE",
  MAINTENANCE = "MAINTENANCE",
  POLICY_UPDATE = "POLICY_UPDATE",
  DEPRECATION = "DEPRECATION",
}

export enum ProductAnnouncementPriority {
  LOW = "LOW",
  NORMAL = "NORMAL",
  HIGH = "HIGH",
  URGENT = "URGENT",
}

export enum ProductAnnouncementStatus {
  DRAFT = "DRAFT",
  SCHEDULED = "SCHEDULED",
  PUBLISHED = "PUBLISHED",
  EXPIRED = "EXPIRED",
  ARCHIVED = "ARCHIVED",
}

export enum AdoptionMilestoneType {
  DISCOVERY = "DISCOVERY",
  FIRST_USE = "FIRST_USE",
  REPEAT_USE = "REPEAT_USE",
  WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED",
}

export enum AdoptionTargetStatus {
  PLANNED = "PLANNED",
  ACTIVE = "ACTIVE",
  EVALUATED = "EVALUATED",
  ARCHIVED = "ARCHIVED",
}

export interface JourneyStepModel {
  id: UUID;
  journey_id: UUID;
  step_order: number;
  step_key: string;
  title: string;
  description?: string | null;
  completion_criteria: StepCompletionCriteria | string;
  route_path?: string | null;
  contextual_resource_url?: string | null;
  estimated_duration_minutes: number;
  is_required: boolean;
  action_event_key?: string | null;
  created_at: string;
}

export interface AdoptionJourneyModel {
  id: UUID;
  tenant_id?: UUID | null;
  code: string;
  title: string;
  description?: string | null;
  target_roles: string[];
  target_department_id?: UUID | null;
  product_version: string;
  status: JourneyStatus | string;
  version: number;
  is_mandatory: boolean;
  created_by_id?: UUID | null;
  published_at?: string | null;
  created_at: string;
  updated_at: string;
  steps: JourneyStepModel[];
}

export interface UserJourneyProgressModel {
  id: UUID;
  tenant_id: UUID;
  user_id: UUID;
  journey_id: UUID;
  journey_version: number;
  status: UserJourneyState | string;
  current_step_order: number;
  completed_step_keys: string[];
  step_progress_json: Record<string, unknown>;
  progress_pct: number;
  started_at: string;
  last_active_at: string;
  completed_at?: string | null;
}

export interface TrainingModuleModel {
  id: UUID;
  program_id: UUID;
  module_order: number;
  module_key: string;
  title: string;
  content_type: TrainingModuleContentType | string;
  content_body?: string | null;
  external_url?: string | null;
  document_id?: UUID | null;
  estimated_duration_minutes: number;
  is_required: boolean;
  created_at: string;
}

export interface TrainingProgramModel {
  id: UUID;
  tenant_id?: UUID | null;
  code: string;
  title: string;
  description?: string | null;
  category: string;
  target_roles: string[];
  target_department_id?: UUID | null;
  version: number;
  status: TrainingProgramStatus | string;
  estimated_duration_minutes: number;
  is_mandatory: boolean;
  completion_rule: string;
  created_by_id?: UUID | null;
  published_at?: string | null;
  created_at: string;
  updated_at: string;
  modules: TrainingModuleModel[];
}

export interface TrainingAssignmentModel {
  id: UUID;
  tenant_id: UUID;
  program_id: UUID;
  user_id: UUID;
  assigned_by_user_id?: UUID | null;
  status: TrainingAssignmentStatus | string;
  due_date?: string | null;
  completed_module_keys: string[];
  module_progress_json: Record<string, unknown>;
  progress_pct: number;
  started_at?: string | null;
  completed_at?: string | null;
  score?: number | null;
  certificate_reference?: string | null;
  created_at: string;
  program?: TrainingProgramModel | null;
}

export interface ContextualGuidanceModel {
  id: UUID;
  tenant_id?: UUID | null;
  guidance_key: string;
  title: string;
  content: string;
  guidance_type: GuidanceType | string;
  route_path: string;
  feature_key?: string | null;
  step_order: number;
  is_mandatory: boolean;
  target_roles: string[];
  status: GuidanceStatus | string;
  version: number;
  expires_at?: string | null;
  document_url?: string | null;
  created_at: string;
}

export interface UserGuidanceStateModel {
  id: UUID;
  tenant_id: UUID;
  user_id: UUID;
  guidance_id: UUID;
  status: UserGuidanceAction | string;
  impressions_count: number;
  last_seen_at: string;
  completed_at?: string | null;
  dismissed_at?: string | null;
}

export interface ProductAnnouncementModel {
  id: UUID;
  tenant_id?: UUID | null;
  announcement_code: string;
  title: string;
  summary?: string | null;
  content: string;
  category: ProductAnnouncementCategory | string;
  priority: ProductAnnouncementPriority | string;
  status: ProductAnnouncementStatus | string;
  effective_at: string;
  expires_at?: string | null;
  requires_acknowledgement: boolean;
  target_roles: string[];
  target_departments: string[];
  feature_flag_key?: string | null;
  doc_link_url?: string | null;
  version: number;
  published_at?: string | null;
  created_by_user_id?: UUID | null;
  created_at: string;
  user_is_read?: boolean;
  user_is_acknowledged?: boolean;
}

export interface UserAnnouncementReceiptModel {
  id: UUID;
  tenant_id: UUID;
  user_id: UUID;
  announcement_id: UUID;
  announcement_version: number;
  is_read: boolean;
  read_at: string;
  is_acknowledged: boolean;
  acknowledged_at?: string | null;
  acknowledgement_notes?: string | null;
}

export interface FeatureAdoptionTargetModel {
  id: UUID;
  tenant_id: UUID;
  feature_key: string;
  feature_name: string;
  target_roles: string[];
  target_adoption_pct: number;
  window_start_date: string;
  window_end_date: string;
  status: AdoptionTargetStatus | string;
  created_at: string;
}

export interface FeatureAdoptionMilestoneModel {
  id: UUID;
  tenant_id: UUID;
  user_id: UUID;
  feature_key: string;
  milestone_type: AdoptionMilestoneType | string;
  metadata_json: Record<string, unknown>;
  recorded_at: string;
}

export interface StepDropoffMetricModel {
  step_key: string;
  step_title: string;
  step_order: number;
  completed_users_count: number;
  dropoff_rate_pct: number;
}

export interface JourneyAdoptionMetricsModel {
  journey_id: UUID;
  journey_code: string;
  journey_title: string;
  total_assigned_or_eligible: number;
  started_count: number;
  completed_count: number;
  completion_rate_pct: number;
  median_duration_minutes?: number | null;
  step_metrics: StepDropoffMetricModel[];
}

export interface TrainingProgramMetricsModel {
  program_id: UUID;
  program_code: string;
  program_title: string;
  total_enrolled: number;
  in_progress_count: number;
  completed_count: number;
  overdue_count: number;
  completion_rate_pct: number;
  average_score?: number | null;
}

export interface AnnouncementReadershipMetricsModel {
  announcement_id: UUID;
  announcement_code: string;
  title: string;
  category: string;
  total_target_users: number;
  read_count: number;
  read_rate_pct: number;
  acknowledged_count: number;
  acknowledgement_rate_pct: number;
}

export interface FeatureRolloutAdoptionMetricsModel {
  feature_key: string;
  feature_name: string;
  target_adoption_pct: number;
  current_adoption_pct: number;
  total_eligible_users: number;
  discovery_count: number;
  first_use_count: number;
  repeat_use_count: number;
  workflow_completed_count: number;
  adoption_status: string;
}

export interface AdoptionSummaryDashboardModel {
  tenant_id: UUID;
  active_journeys_count: number;
  journey_overall_completion_rate: number;
  active_training_programs_count: number;
  training_overall_completion_rate: number;
  overdue_trainings_count: number;
  active_announcements_count: number;
  pending_acknowledgements_count: number;
  tracked_features_count: number;
  top_adopted_features: string[];
  low_adoption_features: string[];
}

// -----------------------------------------------------------------------------
// Step 38: Enterprise Customer Success, Subscription Lifecycle & SaaS Entitlements
// -----------------------------------------------------------------------------

export type SaaSPlanStatus = "DRAFT" | "ACTIVE" | "RETIRED";
export type SaaSBillingInterval = "MONTHLY" | "QUARTERLY" | "ANNUAL";
export type SaaSSubscriptionStatus =
  | "TRIAL_PENDING"
  | "TRIAL_ACTIVE"
  | "ACTIVE"
  | "PAYMENT_OVERDUE"
  | "GRACE_PERIOD"
  | "SUSPENDED"
  | "CANCELLATION_SCHEDULED"
  | "CANCELLED"
  | "EXPIRED";

export type SaaSSubscriptionChangeType = "UPGRADE" | "DOWNGRADE" | "INTERVAL_CHANGE";
export type SaaSSubscriptionChangeStatus = "PENDING_APPROVAL" | "SCHEDULED" | "APPLIED" | "REJECTED" | "CANCELLED";
export type SaaSOverrideType = "MODULE_GATE" | "CAPABILITY" | "QUOTA_LIMIT";
export type SaaSInvoiceStatus = "DRAFT" | "ISSUED" | "PAID" | "PAST_DUE" | "VOID" | "REFUNDED";
export type SaaSPaymentStatus = "PENDING" | "SUCCESS" | "FAILED" | "CANCELLED";
export type CustomerHealthStatus = "HEALTHY" | "GOOD" | "NEEDS_ATTENTION" | "AT_RISK" | "CRITICAL";
export type CustomerNoteType = "GENERAL" | "CALL_LOG" | "RENEWAL_RISK" | "EXPANSION_OPPORTUNITY" | "ESCALATION";

export interface SubscriptionPlanModel {
  id: UUID;
  code: string;
  name: string;
  description: string;
  status: SaaSPlanStatus;
  billing_interval: SaaSBillingInterval;
  currency: string;
  base_price: number;
  trial_eligible: boolean;
  trial_duration_days: number;
  max_active_users: number;
  max_students: number;
  max_faculty: number;
  max_storage_bytes: number;
  max_api_rpm: number;
  max_ai_tokens_monthly: number;
  max_integrations: number;
  included_modules: string[];
  feature_capabilities: Record<string, any>;
  support_tier: string;
  version: number;
  effective_from: string;
  retired_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TenantSubscriptionModel {
  id: UUID;
  tenant_id: UUID;
  plan_id: UUID;
  plan_version: number;
  status: SaaSSubscriptionStatus;
  billing_interval: SaaSBillingInterval;
  currency: string;
  unit_price: number;
  current_period_start: string;
  current_period_end: string;
  trial_started_at?: string | null;
  trial_ends_at?: string | null;
  grace_period_ends_at?: string | null;
  cancellation_effective_at?: string | null;
  cancellation_reason?: string | null;
  auto_renew: boolean;
  payment_method_id?: string | null;
  snapshot_limits_json: Record<string, any>;
  snapshot_modules_json: string[];
  snapshot_features_json: Record<string, any>;
  created_at: string;
  updated_at: string;
  plan?: SubscriptionPlanModel | null;
}

export interface SubscriptionLifecycleHistoryModel {
  id: UUID;
  subscription_id: UUID;
  tenant_id: UUID;
  from_status: string;
  to_status: string;
  reason: string;
  actor_id?: UUID | null;
  actor_email?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface SubscriptionEntitlementOverrideModel {
  id: UUID;
  tenant_id: UUID;
  override_type: SaaSOverrideType;
  target_key: string;
  override_value_json: any;
  reason: string;
  granted_by_id: UUID;
  starts_at: string;
  expires_at: string;
  is_active: boolean;
  created_at: string;
}

export interface EffectiveEntitlementsModel {
  tenant_id: UUID;
  plan_code: string;
  plan_name: string;
  subscription_status: string;
  is_active: boolean;
  is_trial: boolean;
  trial_days_remaining: number;
  enabled_modules: string[];
  feature_capabilities: Record<string, any>;
  resource_limits: Record<string, any>;
  active_overrides: SubscriptionEntitlementOverrideModel[];
}

export interface SubscriptionQuotaStatusModel {
  resource_type: string;
  current_usage: number;
  soft_limit: number;
  hard_limit: number;
  remaining_capacity: number;
  utilization_percentage: number;
  is_exceeded: boolean;
  unit: string;
}

export interface SubscriptionInvoiceModel {
  id: UUID;
  tenant_id: UUID;
  subscription_id: UUID;
  invoice_number: string;
  billing_period_start: string;
  billing_period_end: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  currency: string;
  status: SaaSInvoiceStatus;
  due_date: string;
  paid_at?: string | null;
  line_items_json: Array<Record<string, any>>;
  download_url?: string | null;
  created_at: string;
}

export interface DowngradeImpactPreviewModel {
  can_downgrade_immediately: boolean;
  has_capacity_violations: boolean;
  violations: Array<{
    resource: string;
    current_usage: number;
    target_limit: number;
    excess: number;
    remediation: string;
  }>;
  current_plan: string;
  target_plan: string;
  resource_comparisons: Array<{
    resource: string;
    current_usage: number;
    current_limit: number;
    target_limit: number;
    exceeds: boolean;
  }>;
  removed_modules: string[];
  removed_features: string[];
  recommended_actions: string[];
}

export interface CustomerSuccessHealthSnapshotModel {
  id: UUID;
  tenant_id: UUID;
  health_score: number;
  health_status: CustomerHealthStatus;
  utilization_score: number;
  adoption_score: number;
  support_score: number;
  financial_score: number;
  signals_json: Record<string, any>;
  recommendations: string[];
  calculated_at: string;
}

export interface CustomerSuccessNoteModel {
  id: UUID;
  tenant_id: UUID;
  author_id: UUID;
  author_email: string;
  note_type: CustomerNoteType;
  content: string;
  is_pinned: boolean;
  created_at: string;
}

export interface CustomerSuccessTenantSummaryModel {
  tenant_id: UUID;
  institution_code: string;
  institution_name: string;
  plan_name: string;
  subscription_status: string;
  current_period_end: string;
  days_until_renewal: number;
  health_score: number;
  health_status: CustomerHealthStatus;
  open_critical_tickets: number;
  utilization_pct: number;
  adoption_pct: number;
  requires_attention: boolean;
}

// =============================================================================
// Enterprise Marketplace, App Integrations & Extensibility Ecosystem (Step 39)
// =============================================================================

export enum MarketplaceAppCategory {
  LMS = "LMS",
  PAYMENT_GATEWAY = "PAYMENT_GATEWAY",
  VIDEO_CONFERENCING = "VIDEO_CONFERENCING",
  HARDWARE_IOT = "HARDWARE_IOT",
  GOVERNMENT_EXCHANGE = "GOVERNMENT_EXCHANGE",
  COMMUNICATION = "COMMUNICATION",
  CLOUD_STORAGE = "CLOUD_STORAGE",
  ANALYTICS = "ANALYTICS",
  IDENTITY_PROVIDER = "IDENTITY_PROVIDER",
  LIBRARY_SYSTEM = "LIBRARY_SYSTEM",
  RECRUITMENT = "RECRUITMENT",
  OTHER = "OTHER",
}

export enum MarketplacePublicationStatus {
  DRAFT = "DRAFT",
  IN_REVIEW = "IN_REVIEW",
  APPROVED = "APPROVED",
  PUBLISHED = "PUBLISHED",
  DEPRECATED = "DEPRECATED",
  RETIRED = "RETIRED",
}

export enum MarketplaceConnectionMethod {
  API_KEY = "API_KEY",
  OAUTH2 = "OAUTH2",
  DEVICE_CREDENTIALS = "DEVICE_CREDENTIALS",
  WEBHOOK_ONLY = "WEBHOOK_ONLY",
  CERTIFICATE = "CERTIFICATE",
}

export enum MarketplaceSyncDirection {
  INBOUND = "INBOUND",
  OUTBOUND = "OUTBOUND",
  BIDIRECTIONAL = "BIDIRECTIONAL",
}

export enum MarketplaceConflictPolicy {
  CAMPUSOS_AUTHORITATIVE = "CAMPUSOS_AUTHORITATIVE",
  PROVIDER_AUTHORITATIVE = "PROVIDER_AUTHORITATIVE",
  MANUAL_REVIEW = "MANUAL_REVIEW",
  NEWEST_WINS = "NEWEST_WINS",
}

export enum TenantInstallationStatus {
  NOT_CONNECTED = "NOT_CONNECTED",
  SETUP_PENDING = "SETUP_PENDING",
  AWAITING_AUTHORIZATION = "AWAITING_AUTHORIZATION",
  CONNECTED = "CONNECTED",
  SYNC_PAUSED = "SYNC_PAUSED",
  DEGRADED = "DEGRADED",
  REAUTH_REQUIRED = "REAUTH_REQUIRED",
  DISCONNECT_PENDING = "DISCONNECT_PENDING",
  DISCONNECTED = "DISCONNECTED",
  FAILED = "FAILED",
}

export enum MarketplaceSyncTriggerType {
  MANUAL = "MANUAL",
  SCHEDULED = "SCHEDULED",
  WEBHOOK = "WEBHOOK",
  INITIAL = "INITIAL",
  REPLAY = "REPLAY",
}

export enum MarketplaceSyncRunStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  SUCCESS = "SUCCESS",
  PARTIAL_SUCCESS = "PARTIAL_SUCCESS",
  FAILED = "FAILED",
  CANCELLED = "CANCELLED",
}

export interface MarketplaceAppModel {
  id: UUID;
  code: string;
  name: string;
  category: MarketplaceAppCategory;
  description: string;
  provider_name: string;
  provider_url?: string;
  provider_email?: string;
  icon_url?: string;
  supported_modules: string[];
  required_scopes: string[];
  connection_method: MarketplaceConnectionMethod;
  config_schema: Record<string, any>;
  supported_capabilities: string[];
  documentation_url?: string;
  setup_instructions: string;
  min_platform_version: string;
  required_entitlements: string[];
  publication_status: MarketplacePublicationStatus;
  is_verified: boolean;
  is_featured: boolean;
  deprecation_notice?: string;
  deprecated_at?: string;
  created_at: string;
  updated_at: string;
}

export interface TenantAppInstallationModel {
  id: UUID;
  tenant_id: UUID;
  app_id: UUID;
  app_version_id?: UUID;
  app_code?: string;
  app_name?: string;
  app_category?: string;
  display_name: string;
  status: TenantInstallationStatus;
  connection_method: MarketplaceConnectionMethod;
  enabled_capabilities: string[];
  authorized_scopes: string[];
  configuration: Record<string, any>;
  field_mappings: Record<string, any>;
  sync_direction: MarketplaceSyncDirection;
  conflict_policy: MarketplaceConflictPolicy;
  credential_id?: UUID;
  has_credentials: boolean;
  health_status: string;
  health_details: Record<string, any>;
  last_health_check_at?: string;
  consecutive_failure_count: number;
  last_successful_sync_at?: string;
  last_failure_at?: string;
  last_error_summary?: string;
  connected_at?: string;
  disconnected_at?: string;
  created_at: string;
  updated_at: string;
}

export interface MarketplaceSyncRunModel {
  id: UUID;
  installation_id: UUID;
  trigger_type: MarketplaceSyncTriggerType;
  status: MarketplaceSyncRunStatus;
  records_fetched: number;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_skipped: number;
  records_failed: number;
  error_summary?: string;
  execution_metadata: Record<string, any>;
  started_at: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface IntegrationDataConflictModel {
  id: UUID;
  installation_id: UUID;
  entity_type: string;
  record_identifier: string;
  campusos_payload: Record<string, any>;
  provider_payload: Record<string, any>;
  conflicting_fields: string[];
  applied_resolution: string;
  resolved_payload: Record<string, any>;
  resolved_by_user_id?: UUID;
  resolved_at?: string;
  resolution_notes?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TestConnectivityResultModel {
  success: boolean;
  status: string;
  latency_ms: number;
  message: string;
  details: Record<string, any>;
}

export interface PlatformMarketplaceHealthModel {
  total_catalog_apps: number;
  total_installations: number;
  active_connected_installations: number;
  degraded_installations: number;
  total_sync_runs: number;
  failed_sync_runs: number;
  sync_success_rate: number;
  generated_at: string;
}

// =============================================================================
// Step 40: Enterprise Data Import, Bulk Migration & Reconciliation Types
// =============================================================================

export type ImportJobStatus =
  | "DRAFT"
  | "FILE_UPLOADED"
  | "MAPPING_PENDING"
  | "VALIDATION_RUNNING"
  | "VALIDATION_COMPLETED"
  | "VALIDATION_FAILED"
  | "AWAITING_APPROVAL"
  | "READY_TO_EXECUTE"
  | "EXECUTION_RUNNING"
  | "PARTIALLY_COMPLETED"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "RECONCILIATION_REQUIRED";

export type ImportExecutionPolicy =
  | "VALIDATE_ONLY"
  | "CREATE_NEW"
  | "UPDATE_EXISTING"
  | "UPSERT"
  | "SKIP_CONFLICTS";

export type ImportRecordStatus =
  | "PENDING"
  | "VALID"
  | "INVALID"
  | "CREATED"
  | "UPDATED"
  | "SKIPPED"
  | "FAILED";

export interface ImportTemplateModel {
  id: UUID;
  code: string;
  name: string;
  target_domain: string;
  target_entity: string;
  description?: string | null;
  version: number;
  required_fields: string[];
  optional_fields: string[];
  field_definitions: Record<string, any>;
  supported_matching_keys: string[];
  supported_policies: string[];
  requires_approval_threshold: number;
  is_system_template: boolean;
  is_active: boolean;
  created_at: string;
}

export interface ImportJobModel {
  id: UUID;
  tenant_id: UUID;
  template_id?: UUID | null;
  template_code: string;
  name: string;
  target_domain: string;
  target_entity: string;
  status: ImportJobStatus;
  execution_policy: ImportExecutionPolicy;
  matching_key?: string | null;
  source_filename?: string | null;
  source_file_checksum?: string | null;
  source_file_size_bytes: number;
  source_file_format?: string | null;
  source_record_count: number;
  valid_record_count: number;
  error_record_count: number;
  warning_record_count: number;
  processed_record_count: number;
  created_record_count: number;
  updated_record_count: number;
  skipped_record_count: number;
  failed_record_count: number;
  last_processed_row: number;
  requires_approval: boolean;
  approved_by_id?: UUID | null;
  approved_at?: string | null;
  approval_notes?: string | null;
  rejection_reason?: string | null;
  created_by_id: UUID;
  started_at?: string | null;
  completed_at?: string | null;
  last_error_summary?: string | null;
  reconciliation_status: string;
  reconciliation_diff_count: number;
  reconciliation_summary: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ImportMappingDefinitionModel {
  id: UUID;
  job_id: UUID;
  template_code: string;
  version: number;
  column_mappings: Record<string, string>;
  transformations: Record<string, any>;
  default_values: Record<string, any>;
  is_validated: boolean;
}

export interface ImportValidationSummaryModel {
  job_id: UUID;
  status: string;
  total_records: number;
  valid_records: number;
  error_records: number;
  warning_records: number;
  errors_by_field: Record<string, number>;
  sample_errors: Array<{ row_number: number; errors: any[] }>;
  can_execute: boolean;
  requires_approval: boolean;
}

export interface ImportPreviewModel {
  job_id: UUID;
  execution_policy: string;
  matching_key?: string | null;
  total_source_records: number;
  records_to_create: number;
  records_to_update: number;
  records_to_skip: number;
  records_with_warnings: number;
  records_blocking_execution: number;
  potential_duplicate_matches: number;
  high_impact_summary: string[];
  sample_transformed_records: Array<Record<string, any>>;
}

export interface ImportConflictModel {
  id: UUID;
  job_id: UUID;
  row_number: number;
  matching_key: string;
  matching_value: string;
  existing_entity_id?: UUID | null;
  conflict_type: string;
  source_payload: Record<string, any>;
  existing_payload: Record<string, any>;
  discrepancies_json: Record<string, any>;
  resolution: string;
  resolved_by_id?: UUID | null;
  resolved_at?: string | null;
}

export interface ImportReconciliationModel {
  job_id: UUID;
  reconciliation_status: string;
  source_record_count: number;
  valid_record_count: number;
  created_record_count: number;
  updated_record_count: number;
  skipped_record_count: number;
  failed_record_count: number;
  unaccounted_difference: number;
  is_balanced: boolean;
  discrepancy_details: Record<string, any>;
}

// =============================================================================
// STEP 41: ENTERPRISE RECORDS LIFECYCLE, RETENTION, ARCHIVAL & LEGAL HOLD
// =============================================================================

export type RecordLifecycleState =
  | "ACTIVE"
  | "RETENTION_PENDING"
  | "RETENTION_IN_PROGRESS"
  | "REVIEW_REQUIRED"
  | "ELIGIBLE_FOR_ARCHIVAL"
  | "ARCHIVED"
  | "DISPOSITION_ELIGIBLE"
  | "DISPOSITION_PENDING_APPROVAL"
  | "DISPOSITION_APPROVED"
  | "DISPOSITION_COMPLETED"
  | "LEGAL_HOLD"
  | "REVIEW_BLOCKED";



export type RetentionPolicyStatus = "DRAFT" | "PUBLISHED" | "DEPRECATED" | "ARCHIVED";

export type PolicyScope = "GLOBAL" | "CATEGORY" | "MODULE" | "DEPARTMENT";

export type DispositionMethod = "SECURE_DELETE" | "ANONYMIZE" | "PERMANENT_ARCHIVE" | "REVIEW_ONLY";

export type LegalHoldStatus = "ACTIVE" | "PENDING_RELEASE" | "RELEASED" | "REVOKED";

export type LegalHoldScope = "ALL" | "CATEGORY" | "MODULE" | "DEPARTMENT" | "SPECIFIC_RECORD";

export type ArchivalStatus = "STORED" | "VERIFIED" | "RESTORED" | "CORRUPTED" | "PURGED";

export type DispositionRequestStatus =
  | "DRAFT"
  | "PENDING_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "EXECUTING"
  | "COMPLETED"
  | "FAILED";

export type DispositionItemStatus =
  | "ELIGIBLE"
  | "BLOCKED_HOLD"
  | "BLOCKED_DEPENDENCY"
  | "EXECUTED"
  | "FAILED";

export interface RecordCategoryModel {
  id: UUID;
  tenant_id: UUID;
  code: string;
  name: string;
  description?: string | null;
  confidentiality: string;
  default_retention_years: number;
  statutory_authority?: string | null;
  is_active: boolean;
  metadata_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface RetentionPolicyVersionModel {
  id: UUID;
  tenant_id: UUID;
  policy_id: UUID;
  version_number: number;
  status: RetentionPolicyStatus;
  rules_json: Record<string, any>;
  change_summary?: string | null;
  effective_from: string;
  effective_until?: string | null;
  created_by_user_id?: UUID | null;
  created_at: string;
  updated_at: string;
}

export interface RetentionPolicyModel {
  id: UUID;
  tenant_id: UUID;
  code: string;
  name: string;
  description?: string | null;
  category_code: string;
  scope: PolicyScope;
  scope_target?: string | null;
  retention_duration: number;
  retention_unit: RetentionUnit;
  trigger_event: RetentionTriggerEvent;
  review_required: boolean;
  archive_required: boolean;
  disposition_method: DispositionMethod;
  approval_required: boolean;
  effective_from: string;
  effective_until?: string | null;
  status: RetentionPolicyStatus;
  current_version: number;
  owner_user_id?: UUID | null;
  approved_by_user_id?: UUID | null;
  approved_at?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  versions?: RetentionPolicyVersionModel[];
}

export interface RecordRegistryEntryModel {
  id: UUID;
  tenant_id: UUID;
  record_number: string;
  category_id?: UUID | null;
  category_code: string;
  source_module: string;
  source_record_id: UUID;
  source_reference?: string | null;
  title: string;
  description?: string | null;
  owner_user_id?: UUID | null;
  owner_department_id?: UUID | null;
  responsible_department?: string | null;
  confidentiality_level: string;
  lifecycle_state: RecordLifecycleState;
  policy_id?: UUID | null;
  policy_version?: number | null;
  record_created_at: string;
  retention_start_date?: string | null;
  calculated_review_date?: string | null;
  calculated_eligibility_date?: string | null;
  archived_at?: string | null;
  disposed_at?: string | null;
  is_held: boolean;
  active_hold_count: number;
  storage_reference?: string | null;
  checksum_sha256?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface RecordLifecycleHistoryModel {
  id: UUID;
  tenant_id: UUID;
  record_id: UUID;
  from_state: string;
  to_state: string;
  trigger_action: string;
  reason?: string | null;
  actor_user_id?: UUID | null;
  actor_role?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
}

export interface RecordArchivalRecordModel {
  id: UUID;
  tenant_id: UUID;
  manifest_number: string;
  record_id: UUID;
  archive_location: string;
  archive_storage_key: string;
  original_storage_key?: string | null;
  checksum_sha256: string;
  verified_checksum?: string | null;
  file_size_bytes: number;
  status: ArchivalStatus;
  archived_by_user_id?: UUID | null;
  archived_at: string;
  retrieval_count: number;
  last_retrieved_at?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface RecordLegalHoldModel {
  id: UUID;
  tenant_id: UUID;
  hold_number: string;
  name: string;
  case_reference?: string | null;
  reason: string;
  hold_authority: string;
  scope_type: LegalHoldScope;
  scope_value?: string | null;
  status: LegalHoldStatus;
  owner_user_id?: UUID | null;
  custodians_json?: string[] | null;
  effective_from: string;
  review_date?: string | null;
  released_at?: string | null;
  released_by_user_id?: UUID | null;
  release_reason?: string | null;
  records_count: number;
  metadata_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface RecordDispositionItemModel {
  id: UUID;
  tenant_id: UUID;
  request_id: UUID;
  record_id: UUID;
  status: DispositionItemStatus;
  error_message?: string | null;
  disposed_at?: string | null;
  created_at: string;
  record?: RecordRegistryEntryModel | null;
}

export interface RecordDispositionCertificateModel {
  id: UUID;
  tenant_id: UUID;
  certificate_number: string;
  request_id: UUID;
  disposition_method: string;
  records_disposed_count: number;
  manifest_hash_sha256: string;
  witness_actor_id: UUID;
  approved_by_user_id?: UUID | null;
  disposition_completed_at: string;
  tamper_evident_signature: string;
  summary_json?: Record<string, any> | null;
  created_at: string;
}

export interface RecordDispositionRequestModel {
  id: UUID;
  tenant_id: UUID;
  request_number: string;
  policy_id?: UUID | null;
  policy_version?: number | null;
  category_code?: string | null;
  requested_disposition_method: DispositionMethod;
  status: DispositionRequestStatus;
  records_count: number;
  preview_stats_json?: Record<string, any> | null;
  justification: string;
  requested_by_user_id: UUID;
  reviewed_by_user_id?: UUID | null;
  reviewed_at?: string | null;
  approved_by_user_id?: UUID | null;
  approved_at?: string | null;
  rejection_reason?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  items?: RecordDispositionItemModel[];
  certificate?: RecordDispositionCertificateModel | null;
}

export interface RetentionEvaluationModel {
  record_id: UUID;
  record_number: string;
  current_state: RecordLifecycleState;
  recommended_state: RecordLifecycleState;
  is_held: boolean;
  hold_reasons: string[];
  policy_id?: UUID | null;
  policy_code?: string | null;
  policy_version?: number | null;
  retention_start_date?: string | null;
  calculated_eligibility_date?: string | null;
  is_eligible_for_disposition: boolean;
  is_eligible_for_archival: boolean;
  disposition_method?: string | null;
  has_dependency_block: boolean;
  dependency_reasons: string[];
  evaluation_summary: string;
}

export interface RecordsLifecycleSummaryModel {
  total_records_registered: number;
  active_retention_records: number;
  archived_records: number;
  eligible_for_archival_records: number;
  disposition_eligible_records: number;
  review_required_records: number;
  legal_held_records: number;
  active_legal_holds_count: number;
  pending_disposition_approvals_count: number;
  completed_dispositions_count: number;
  active_retention_policies_count: number;
}

/**
 * Step 42: Enterprise Institutional Knowledge Base, Policy Library & Controlled Knowledge Management Types
 */

export enum KnowledgeCategoryCode {
  INSTITUTIONAL_POLICY = "INSTITUTIONAL_POLICY",
  ACADEMIC_REGULATION = "ACADEMIC_REGULATION",
  STANDARD_OPERATING_PROCEDURE = "STANDARD_OPERATING_PROCEDURE",
  STUDENT_HANDBOOK = "STUDENT_HANDBOOK",
  FACULTY_HANDBOOK = "FACULTY_HANDBOOK",
  DEPARTMENT_GUIDELINE = "DEPARTMENT_GUIDELINE",
  ADMIN_PROCEDURE = "ADMIN_PROCEDURE",
  FINANCE_PROCUREMENT = "FINANCE_PROCUREMENT",
  HR_POLICY = "HR_POLICY",
  CAMPUS_SAFETY = "CAMPUS_SAFETY",
  IT_SECURITY = "IT_SECURITY",
  CIRCULAR_NOTICE = "CIRCULAR_NOTICE",
  ACCREDITATION_QA = "ACCREDITATION_QA",
  TECHNICAL_MANUAL = "TECHNICAL_MANUAL",
}

export enum KnowledgeItemStatus {
  DRAFT = "DRAFT",
  SUBMITTED = "SUBMITTED",
  IN_REVIEW = "IN_REVIEW",
  CHANGES_REQUESTED = "CHANGES_REQUESTED",
  APPROVED = "APPROVED",
  SCHEDULED = "SCHEDULED",
  PUBLISHED = "PUBLISHED",
  SUPERSEDED = "SUPERSEDED",
  RETIRED = "RETIRED",
}

export enum KnowledgeScopeType {
  INSTITUTION = "INSTITUTION",
  CAMPUS = "CAMPUS",
  DEPARTMENT = "DEPARTMENT",
  ROLE = "ROLE",
  RESTRICTED = "RESTRICTED",
}

export enum KnowledgeConfidentiality {
  PUBLIC_INSTITUTION = "PUBLIC_INSTITUTION",
  INTERNAL_ONLY = "INTERNAL_ONLY",
  CONFIDENTIAL_ADMIN = "CONFIDENTIAL_ADMIN",
  RESTRICTED = "RESTRICTED",
}

export enum KnowledgeRelationshipType {
  SUPERSEDES = "SUPERSEDES",
  IMPLEMENTS = "IMPLEMENTS",
  REFERENCES = "REFERENCES",
  DEPENDS_ON = "DEPENDS_ON",
  ANNOUNCES = "ANNOUNCES",
  REQUIRES_ACKNOWLEDGEMENT = "REQUIRES_ACKNOWLEDGEMENT",
}

export enum KnowledgeReviewDecision {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  CHANGES_REQUESTED = "CHANGES_REQUESTED",
  REJECTED = "REJECTED",
}

export enum KnowledgeReviewScheduleType {
  ANNUAL_REVIEW = "ANNUAL_REVIEW",
  EXPIRATION_CHECK = "EXPIRATION_CHECK",
  ACKNOWLEDGEMENT_REMINDER = "ACKNOWLEDGEMENT_REMINDER",
}

export enum KnowledgeReviewScheduleStatus {
  PENDING = "PENDING",
  NOTIFIED = "NOTIFIED",
  OVERDUE = "OVERDUE",
  COMPLETED = "COMPLETED",
  CANCELLED = "CANCELLED",
}

export interface KnowledgeCategoryModel {
  id: UUID;
  tenant_id: UUID;
  code: string;
  name: string;
  description?: string | null;
  is_system: boolean;
  requires_approval: boolean;
  requires_attestation: boolean;
  default_review_months: number;
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeSectionModel {
  id: string;
  title: string;
  level: number;
  content: string;
  order: number;
}

export interface KnowledgeItemDraftUpdateModel {
  title?: string | null;
  summary?: string | null;
  draft_content_markdown?: string | null;
  draft_sections_json?: KnowledgeSectionModel[] | null;
  tags?: string[] | null;
  document_attachment_ids?: string[] | null;
  lock_version: number;
  change_summary?: string | null;
}

export interface KnowledgeDraftValidationResultModel {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  word_count: number;
  sections_count: number;
  sanitized_preview_html: string;
}

export interface KnowledgeItemCreateModel {
  item_code: string;
  title: string;
  summary: string;
  category_code: string;
  scope_type?: KnowledgeScopeType;
  visibility_role?: string | null;
  confidentiality?: KnowledgeConfidentiality;
  campus_id?: UUID | null;
  department_id?: UUID | null;
  responsible_reviewer_id?: UUID | null;
  draft_content_markdown?: string;
  draft_sections_json?: KnowledgeSectionModel[];
  tags?: string[];
  document_attachment_ids?: string[];
  effective_from?: string | null;
  effective_until?: string | null;
  review_by_date?: string | null;
  requires_acknowledgement?: boolean;
  change_summary?: string | null;
}

export interface KnowledgeItemMetadataUpdateModel {
  title?: string | null;
  summary?: string | null;
  category_code?: string | null;
  scope_type?: KnowledgeScopeType | null;
  visibility_role?: string | null;
  confidentiality?: KnowledgeConfidentiality | null;
  campus_id?: UUID | null;
  department_id?: UUID | null;
  responsible_reviewer_id?: UUID | null;
  owner_user_id?: UUID | null;
  effective_from?: string | null;
  effective_until?: string | null;
  review_by_date?: string | null;
  requires_acknowledgement?: boolean | null;
}

export interface KnowledgeItemVersionSummaryModel {
  id: UUID;
  version_number: number;
  title: string;
  summary: string;
  published_at: string;
  effective_from: string;
  effective_until?: string | null;
  author_user_id: UUID;
  published_by_user_id: UUID;
  change_summary?: string | null;
}

export interface KnowledgeReviewStageModel {
  id: UUID;
  item_id: UUID;
  version_number: number;
  stage_order: number;
  stage_name: string;
  reviewer_user_id?: UUID | null;
  reviewer_role?: string | null;
  status: string;
  comments?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface KnowledgeItemModel {
  id: UUID;
  tenant_id: UUID;
  item_code: string;
  title: string;
  summary: string;
  category_id: UUID;
  category_code: string;
  owner_user_id: UUID;
  responsible_reviewer_id?: UUID | null;
  last_edited_by_user_id?: UUID | null;
  campus_id?: UUID | null;
  department_id?: UUID | null;
  scope_type: string;
  visibility_role?: string | null;
  confidentiality: string;
  status: string;
  current_version_number: number;
  current_version_id?: UUID | null;
  lock_version: number;
  draft_content_markdown: string;
  draft_sections_json: Record<string, any>[];
  tags: string[];
  document_attachment_ids: string[];
  change_summary?: string | null;
  effective_from?: string | null;
  effective_until?: string | null;
  review_by_date?: string | null;
  published_at?: string | null;
  superseded_at?: string | null;
  superseded_by_item_id?: UUID | null;
  requires_acknowledgement: boolean;
  search_indexed_at?: string | null;
  search_index_status: string;
  created_at: string;
  updated_at: string;
  versions?: KnowledgeItemVersionSummaryModel[];
  review_stages?: KnowledgeReviewStageModel[];
}

export interface KnowledgeItemVersionDetailModel {
  id: UUID;
  tenant_id: UUID;
  item_id: UUID;
  version_number: number;
  title: string;
  summary: string;
  content_markdown: string;
  sections_json: Record<string, any>[];
  metadata_snapshot: Record<string, any>;
  tags: string[];
  document_attachment_ids: string[];
  author_user_id: UUID;
  reviewer_user_id?: UUID | null;
  approval_decision: string;
  approved_at?: string | null;
  published_by_user_id: UUID;
  published_at: string;
  effective_from: string;
  effective_until?: string | null;
  change_summary?: string | null;
  supersedes_version_id?: UUID | null;
  created_at: string;
}

export interface KnowledgeRelationshipModel {
  id: UUID;
  tenant_id: UUID;
  source_item_id: UUID;
  target_item_id: UUID;
  relationship_type: string;
  description?: string | null;
  created_at: string;
}

export interface KnowledgeAcknowledgementRequirementModel {
  id: UUID;
  tenant_id: UUID;
  item_id: UUID;
  version_number: number;
  target_role?: string | null;
  target_department_id?: UUID | null;
  target_campus_id?: UUID | null;
  deadline_days: number;
  is_mandatory: boolean;
  statement_prompt: string;
  created_at: string;
}

export interface KnowledgeUserAcknowledgementModel {
  id: UUID;
  tenant_id: UUID;
  item_id: UUID;
  version_number: number;
  user_id: UUID;
  acknowledged_at: string;
  ip_address: string;
  user_agent?: string | null;
  statement_confirmed: string;
}

export interface KnowledgeAttestationComplianceReportModel {
  item_id: UUID;
  item_code: string;
  item_title: string;
  version_number: number;
  is_mandatory: boolean;
  deadline_days: number;
  total_required: number;
  total_acknowledged: number;
  compliance_percentage: number;
  acknowledged_users: Array<{
    user_id: string;
    acknowledged_at: string;
    ip_address: string;
  }>;
}

export interface KnowledgeSearchResultItemModel {
  id: UUID;
  item_code: string;
  title: string;
  summary: string;
  category_code: string;
  scope_type: string;
  confidentiality: string;
  status: string;
  current_version_number: number;
  effective_from?: string | null;
  effective_until?: string | null;
  review_by_date?: string | null;
  tags: string[];
  snippet: string;
  match_score: number;
}

export interface KnowledgeSearchResponseModel {
  items: KnowledgeSearchResultItemModel[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface KnowledgeGovernanceSummaryModel {
  total_items: number;
  published_count: number;
  in_review_count: number;
  draft_count: number;
  superseded_count: number;
  retired_count: number;
  overdue_reviews_count: number;
  expiring_soon_count: number;
  mandatory_attestation_items_count: number;
}

// =============================================================================
// STEP 43: ENTERPRISE INSTITUTIONAL ACCREDITATION, QUALITY ASSURANCE & CQI
// =============================================================================

export enum AccreditationFrameworkType {
  NAAC = "NAAC",
  NBA = "NBA",
  NIRF = "NIRF",
  ISO_21001 = "ISO_21001",
  ABET = "ABET",
  INTERNAL_IQAC = "INTERNAL_IQAC",
  CUSTOM = "CUSTOM",
}

export enum AccreditationFrameworkStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  SUPERSEDED = "SUPERSEDED",
  ARCHIVED = "ARCHIVED",
}

export enum AccreditationScoringModel {
  NUMERIC_SCALE = "NUMERIC_SCALE",
  MATURITY_LEVEL = "MATURITY_LEVEL",
  PASS_FAIL = "PASS_FAIL",
  HYBRID = "HYBRID",
}

export enum AccreditationCriterionType {
  QUALITATIVE = "QUALITATIVE",
  QUANTITATIVE = "QUANTITATIVE",
  COMPLIANCE = "COMPLIANCE",
}

export enum AccreditationAssessmentStatus {
  UNASSESSED = "UNASSESSED",
  IN_PROGRESS = "IN_PROGRESS",
  SUBMITTED = "SUBMITTED",
  UNDER_REVIEW = "UNDER_REVIEW",
  APPROVED = "APPROVED",
  CHANGES_REQUESTED = "CHANGES_REQUESTED",
  NON_COMPLIANT = "NON_COMPLIANT",
  NOT_APPLICABLE = "NOT_APPLICABLE",
}

export enum AccreditationMaturityLevel {
  LEVEL_1_INITIAL = "LEVEL_1_INITIAL",
  LEVEL_2_DEVELOPING = "LEVEL_2_DEVELOPING",
  LEVEL_3_DEFINED = "LEVEL_3_DEFINED",
  LEVEL_4_MANAGED = "LEVEL_4_MANAGED",
  LEVEL_5_OPTIMIZING = "LEVEL_5_OPTIMIZING",
}

export enum AccreditationEvidenceCategory {
  POLICY_SOP = "POLICY_SOP",
  EXAM_RECORD = "EXAM_RECORD",
  FACULTY_CREDENTIAL = "FACULTY_CREDENTIAL",
  STUDENT_DATA = "STUDENT_DATA",
  INFRASTRUCTURE_AUDIT = "INFRASTRUCTURE_AUDIT",
  GOVERNANCE_MINUTES = "GOVERNANCE_MINUTES",
  FINANCIAL_AUDIT = "FINANCIAL_AUDIT",
  SURVEY_FEEDBACK = "SURVEY_FEEDBACK",
  EXTERNAL_CERTIFICATE = "EXTERNAL_CERTIFICATE",
}

export enum AccreditationEvidenceVerificationStatus {
  UNVERIFIED = "UNVERIFIED",
  VERIFIED = "VERIFIED",
  REJECTED = "REJECTED",
  EXPIRED = "EXPIRED",
}

export enum QualityIndicatorCategory {
  ACADEMIC_EXCELLENCE = "ACADEMIC_EXCELLENCE",
  RESEARCH_INNOVATION = "RESEARCH_INNOVATION",
  STUDENT_SUCCESS = "STUDENT_SUCCESS",
  FACULTY_PROFILE = "FACULTY_PROFILE",
  INFRASTRUCTURE_RESOURCES = "INFRASTRUCTURE_RESOURCES",
  GOVERNANCE_FINANCE = "GOVERNANCE_FINANCE",
  INSTITUTIONAL_VALUES = "INSTITUTIONAL_VALUES",
}

export enum QualityDataQualityStatus {
  EXCELLENT = "EXCELLENT",
  ACCEPTABLE = "ACCEPTABLE",
  WARNING_STALE = "WARNING_STALE",
  WARNING_INCOMPLETE = "WARNING_INCOMPLETE",
  CALCULATION_FAILED = "CALCULATION_FAILED",
}

export enum QualityAuditType {
  ACADEMIC_AUDIT = "ACADEMIC_AUDIT",
  ADMINISTRATIVE_AUDIT = "ADMINISTRATIVE_AUDIT",
  GREEN_ENVIRONMENTAL = "GREEN_ENVIRONMENTAL",
  ENERGY_AUDIT = "ENERGY_AUDIT",
  ISO_SURVEILLANCE = "ISO_SURVEILLANCE",
  DEPARTMENT_REVIEW = "DEPARTMENT_REVIEW",
}

export enum QualityAuditStatus {
  PLANNED = "PLANNED",
  IN_PROGRESS = "IN_PROGRESS",
  REPORT_DRAFTED = "REPORT_DRAFTED",
  FINALIZED = "FINALIZED",
  CLOSED = "CLOSED",
}

export enum QualityFindingSeverity {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum QualityFindingStatus {
  OPEN = "OPEN",
  ASSIGNED = "ASSIGNED",
  IN_PROGRESS = "IN_PROGRESS",
  AWAITING_VERIFICATION = "AWAITING_VERIFICATION",
  CLOSED = "CLOSED",
  OVERDUE = "OVERDUE",
  REOPENED = "REOPENED",
}

export enum QualityCAPAType {
  CORRECTIVE = "CORRECTIVE",
  PREVENTIVE = "PREVENTIVE",
  IMPROVEMENT = "IMPROVEMENT",
}

export enum QualityCAPAStatus {
  PROPOSED = "PROPOSED",
  APPROVED = "APPROVED",
  IN_PROGRESS = "IN_PROGRESS",
  IMPLEMENTED = "IMPLEMENTED",
  VERIFIED_EFFECTIVE = "VERIFIED_EFFECTIVE",
  REJECTED = "REJECTED",
  REOPENED = "REOPENED",
}

export enum QualityImprovementStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  EVALUATING = "EVALUATING",
  ACHIEVED = "ACHIEVED",
  PARTIALLY_ACHIEVED = "PARTIALLY_ACHIEVED",
  CLOSED = "CLOSED",
}

export enum AccreditationReadinessCategory {
  HIGH_READINESS = "HIGH_READINESS",
  SUBSTANTIAL_PROGRESS = "SUBSTANTIAL_PROGRESS",
  SIGNIFICANT_GAPS = "SIGNIFICANT_GAPS",
  CRITICAL_REMEDIATION_NEEDED = "CRITICAL_REMEDIATION_NEEDED",
}

export interface AccreditationFrameworkModel {
  id: UUID;
  tenant_id: UUID;
  code: string;
  name: string;
  description?: string | null;
  issuing_body: string;
  framework_type: string;
  scope_type: string;
  campus_id?: UUID | null;
  department_id?: UUID | null;
  status: string;
  current_version_number: number;
  effective_from?: string | null;
  effective_until?: string | null;
  review_by_date?: string | null;
  owner_user_id: UUID;
  scoring_model: string;
  max_score?: number | null;
  weighting_supported: boolean;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AccreditationFrameworkVersionModel {
  id: UUID;
  tenant_id: UUID;
  framework_id: UUID;
  version_number: number;
  title: string;
  description?: string | null;
  rules_snapshot_json: Record<string, any>;
  criteria_snapshot_json: Record<string, any>[];
  change_summary?: string | null;
  published_by_user_id: UUID;
  published_at: string;
  created_at: string;
}

export interface AccreditationCriterionModel {
  id: UUID;
  tenant_id: UUID;
  framework_id: UUID;
  parent_criterion_id?: UUID | null;
  code: string;
  title: string;
  description?: string | null;
  criterion_type: string;
  weight: number;
  max_score: number;
  is_mandatory: boolean;
  assessment_guidelines?: string | null;
  evidence_requirements: string[];
  order_index: number;
  is_active: boolean;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AccreditationAssessmentCycleModel {
  id: UUID;
  tenant_id: UUID;
  framework_id: UUID;
  code: string;
  title: string;
  academic_year: string;
  start_date: string;
  end_date: string;
  target_submission_date?: string | null;
  status: string;
  overall_score?: number | null;
  readiness_percentage: number;
  lead_coordinator_id: UUID;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AccreditationCriterionAssessmentModel {
  id: UUID;
  tenant_id: UUID;
  cycle_id: UUID;
  criterion_id: UUID;
  department_id?: UUID | null;
  accountable_owner_id: UUID;
  status: string;
  score?: number | null;
  target_score?: number | null;
  maturity_level?: string | null;
  not_applicable_reason?: string | null;
  executive_summary?: string | null;
  findings?: string | null;
  strengths?: string | null;
  weaknesses?: string | null;
  recommendations?: string | null;
  assessor_id?: UUID | null;
  reviewer_id?: UUID | null;
  assessed_at?: string | null;
  reviewed_at?: string | null;
  lock_version: number;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AccreditationEvidenceModel {
  id: UUID;
  tenant_id: UUID;
  evidence_code: string;
  title: string;
  description?: string | null;
  evidence_category: string;
  source_type: string;
  document_id?: UUID | null;
  knowledge_item_id?: UUID | null;
  record_id?: UUID | null;
  external_uri?: string | null;
  campus_id?: UUID | null;
  department_id?: UUID | null;
  owner_user_id: UUID;
  valid_from: string;
  valid_until?: string | null;
  is_expired: boolean;
  confidentiality: string;
  verification_status: string;
  verified_by_user_id?: UUID | null;
  verified_at?: string | null;
  reviewer_notes?: string | null;
  integrity_hash_sha256?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AccreditationCriterionEvidenceMapModel {
  id: UUID;
  tenant_id: UUID;
  assessment_id: UUID;
  evidence_id: UUID;
  relevance_remarks?: string | null;
  mapped_by_user_id: UUID;
  created_at: string;
}

export interface QualityIndicatorModel {
  id: UUID;
  tenant_id: UUID;
  code: string;
  name: string;
  description?: string | null;
  category: string;
  source_module: string;
  calculation_method: string;
  reporting_frequency: string;
  unit_of_measurement: string;
  target_value: number;
  benchmark_threshold: number;
  current_value?: number | null;
  last_calculated_at?: string | null;
  data_quality_status: string;
  data_quality_notes?: string | null;
  owner_user_id: UUID;
  is_active: boolean;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface QualityIndicatorObservationModel {
  id: UUID;
  tenant_id: UUID;
  indicator_id: UUID;
  period_label: string;
  observation_date: string;
  observed_value: number;
  target_value: number;
  data_source_mode: string;
  is_verified: boolean;
  data_completeness_pct: number;
  outlier_flag: boolean;
  notes?: string | null;
  observed_by_user_id: UUID;
  created_at: string;
  updated_at: string;
}

export interface QualityAuditProgramModel {
  id: UUID;
  tenant_id: UUID;
  code: string;
  title: string;
  description?: string | null;
  audit_type: string;
  scope: string;
  campus_id?: UUID | null;
  department_id?: UUID | null;
  lead_auditor_id: UUID;
  co_auditors_json: string[];
  scheduled_start_date: string;
  scheduled_end_date: string;
  actual_completion_date?: string | null;
  status: string;
  conflict_of_interest_declared: boolean;
  summary_findings?: string | null;
  recommendations?: string | null;
  finalized_at?: string | null;
  finalized_by_user_id?: UUID | null;
  is_immutable: boolean;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface QualityAuditChecklistItemModel {
  id: UUID;
  tenant_id: UUID;
  audit_program_id: UUID;
  criterion_id?: UUID | null;
  item_code: string;
  requirement_description: string;
  compliance_status: string;
  auditor_notes?: string | null;
  evidence_reference?: string | null;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface QualityFindingModel {
  id: UUID;
  tenant_id: UUID;
  finding_code: string;
  source_type: string;
  audit_program_id?: UUID | null;
  criterion_id?: UUID | null;
  department_id?: UUID | null;
  title: string;
  description: string;
  root_cause_analysis?: string | null;
  severity: string;
  status: string;
  identified_by_user_id: UUID;
  assigned_owner_id: UUID;
  target_resolution_date: string;
  resolved_at?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface QualityCorrectiveActionModel {
  id: UUID;
  tenant_id: UUID;
  finding_id: UUID;
  action_code: string;
  action_type: string;
  proposed_action: string;
  preventive_measures?: string | null;
  responsible_owner_id: UUID;
  status: string;
  due_date: string;
  completed_at?: string | null;
  evidence_notes?: string | null;
  evidence_document_id?: UUID | null;
  verification_criteria: string;
  verified_by_user_id?: UUID | null;
  verified_at?: string | null;
  closure_decision?: string | null;
  closure_notes?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface QualityImprovementPlanModel {
  id: UUID;
  tenant_id: UUID;
  code: string;
  title: string;
  objective: string;
  baseline_measurement: string;
  target_outcome: string;
  linked_indicator_id?: UUID | null;
  responsible_owner_id: UUID;
  start_date: string;
  target_date: string;
  actual_completion_date?: string | null;
  status: string;
  evaluation_notes?: string | null;
  lessons_learned?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AccreditationReadinessSnapshotModel {
  id: UUID;
  tenant_id: UUID;
  cycle_id: UUID;
  framework_id: UUID;
  overall_readiness_score: number;
  criteria_assessed_count: number;
  criteria_total_count: number;
  evidence_verified_count: number;
  evidence_required_count: number;
  open_high_risk_findings_count: number;
  score_projected?: number | null;
  score_maximum?: number | null;
  readiness_category: string;
  gap_summary_json: Record<string, any>[];
  department_readiness_json: Record<string, any>;
  calculated_by_user_id: UUID;
  created_at: string;
}

export interface AccreditationDashboardSummaryModel {
  active_frameworks_count: number;
  active_cycles_count: number;
  total_criteria_count: number;
  assessed_criteria_count: number;
  verified_evidences_count: number;
  total_evidences_count: number;
  open_findings_count: number;
  critical_findings_count: number;
  active_audits_count: number;
  active_cqi_plans_count: number;
  overall_readiness_avg_pct: number;
}


// =============================================================================
// STEP 44: ENTERPRISE INSTITUTIONAL RESEARCH, INNOVATION, GRANTS & IP MANAGEMENT
// =============================================================================

export type ResearchProjectCategory =
  | "FACULTY_LED"
  | "COLLABORATIVE_INSTITUTIONAL"
  | "STUDENT_PROJECT"
  | "FUNDED_RESEARCH"
  | "INDUSTRY_SPONSORED"
  | "GOVERNMENT_FUNDED"
  | "INTERDISCIPLINARY"
  | "APPLIED_INNOVATION"
  | "CONSULTANCY"
  | "INSTITUTIONAL_INITIATIVE";

export type ResearchProjectStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "ACTIVE"
  | "ON_HOLD"
  | "AT_RISK"
  | "COMPLETED"
  | "CLOSED";

export type ResearchTeamRole =
  | "PRINCIPAL_INVESTIGATOR"
  | "CO_INVESTIGATOR"
  | "FACULTY_RESEARCHER"
  | "STUDENT_RESEARCHER"
  | "RESEARCH_ASSISTANT"
  | "POSTDOC_FELLOW"
  | "EXTERNAL_COLLABORATOR"
  | "PROJECT_ADMINISTRATOR"
  | "FINANCE_OFFICER"
  | "COMPLIANCE_REVIEWER";

export type ResearchOpportunityStatus =
  | "DRAFT"
  | "OPEN"
  | "CLOSING_SOON"
  | "CLOSED"
  | "ARCHIVED";

export type ResearchGrantInternalReviewStatus =
  | "DRAFT"
  | "SUBMITTED_FOR_REVIEW"
  | "DEPARTMENT_REVIEW"
  | "FINANCE_REVIEW"
  | "ETHICS_REVIEW"
  | "INSTITUTIONALLY_APPROVED"
  | "REJECTED_INTERNAL"
  | "REVISION_REQUESTED";

export type ResearchExternalSubmissionStatus =
  | "NOT_SUBMITTED"
  | "SUBMITTED_EXTERNAL"
  | "UNDER_EXTERNAL_REVIEW"
  | "AWARDED"
  | "REJECTED_EXTERNAL"
  | "WITHDRAWN";

export type ResearchMilestoneStatus =
  | "PLANNED"
  | "IN_PROGRESS"
  | "UNDER_REVIEW"
  | "ACCEPTED"
  | "REJECTED"
  | "BLOCKED"
  | "CANCELLED";

export type ResearchEthicsApprovalType =
  | "HUMAN_PARTICIPANTS"
  | "ANIMAL_RESEARCH"
  | "BIOSAFETY"
  | "LABORATORY_SAFETY"
  | "DATA_PROTECTION"
  | "INSTITUTIONAL_AUTHORIZATION"
  | "CONFLICT_OF_INTEREST"
  | "EXTERNAL_AGREEMENT";

export type ResearchEthicsApprovalStatus =
  | "NOT_SUBMITTED"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "CONDITIONAL_APPROVAL"
  | "REJECTED"
  | "EXPIRED"
  | "SUSPENDED";

export type ResearchOutputType =
  | "JOURNAL_ARTICLE"
  | "CONFERENCE_PAPER"
  | "BOOK"
  | "BOOK_CHAPTER"
  | "PATENT"
  | "RESEARCH_DATASET"
  | "SOFTWARE_TOOL"
  | "TECHNICAL_REPORT"
  | "WORKING_PAPER"
  | "INDUSTRY_DELIVERABLE";

export type ResearchOutputStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "ACCEPTED"
  | "PUBLISHED"
  | "VERIFIED"
  | "REJECTED";

export type ResearchIPConfidentiality =
  | "PUBLIC"
  | "INTERNAL_CONFIDENTIAL"
  | "STRICTLY_CONFIDENTIAL"
  | "TRADE_SECRET";

export type ResearchPatentStatus =
  | "NOT_FILED"
  | "PROVISIONAL_FILED"
  | "NON_PROVISIONAL_FILED"
  | "PCT_INTERNATIONAL"
  | "EXAMINATION"
  | "GRANTED"
  | "MAINTAINED"
  | "ABANDONED"
  | "EXPIRED";

export type ResearchProjectRiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type ResearchProjectRiskStatus =
  | "IDENTIFIED"
  | "ANALYZING"
  | "MITIGATING"
  | "RESOLVED"
  | "ACCEPTED";

export interface ResearchProjectModel {
  id: UUID;
  tenant_id: UUID;
  project_code: string;
  title: string;
  abstract?: string | null;
  description?: string | null;
  research_category: ResearchProjectCategory | string;
  research_domain: string;
  status: ResearchProjectStatus | string;
  principal_investigator_id: UUID;
  department_id?: UUID | null;
  campus_id?: UUID | null;
  start_date?: string | null;
  planned_end_date?: string | null;
  actual_end_date?: string | null;
  currency: string;
  proposed_budget: number;
  approved_budget: number;
  actual_expenditure: number;
  requires_ethics_approval: boolean;
  ethics_approval_type?: string | null;
  external_collaborators_json: Record<string, any>[];
  risks_json: Record<string, any>[];
  tags: string[];
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchProjectStatusHistoryModel {
  id: UUID;
  from_status: string;
  to_status: string;
  actor_user_id: UUID;
  reason: string;
  transitioned_at: string;
}

export interface ResearchTeamMemberModel {
  id: UUID;
  tenant_id: UUID;
  project_id: UUID;
  user_id?: UUID | null;
  role: ResearchTeamRole | string;
  contribution_description?: string | null;
  access_scope: string;
  is_external: boolean;
  external_name?: string | null;
  external_institution?: string | null;
  external_email?: string | null;
  is_active: boolean;
  start_date?: string | null;
  end_date?: string | null;
  created_at: string;
}

export interface ResearchFundingOpportunityModel {
  id: UUID;
  tenant_id: UUID;
  opportunity_code: string;
  title: string;
  description?: string | null;
  funding_organization: string;
  opportunity_url?: string | null;
  category: string;
  research_domains: string[];
  eligibility_criteria?: string | null;
  opening_date?: string | null;
  closing_date?: string | null;
  min_amount?: number | null;
  max_amount?: number | null;
  currency: string;
  required_documents: string[];
  internal_contact_user_id?: UUID | null;
  campus_id?: UUID | null;
  department_id?: UUID | null;
  status: ResearchOpportunityStatus | string;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchGrantApplicationModel {
  id: UUID;
  tenant_id: UUID;
  project_id?: UUID | null;
  opportunity_id?: UUID | null;
  application_code: string;
  title: string;
  proposal_abstract?: string | null;
  research_objectives?: string | null;
  methodology?: string | null;
  expected_outcomes?: string | null;
  proposed_budget: number;
  currency: string;
  principal_investigator_id: UUID;
  co_investigators_json: Record<string, any>[];
  work_packages_json: Record<string, any>[];
  required_attachments_json: Record<string, any>[];
  internal_review_status: ResearchGrantInternalReviewStatus | string;
  internal_reviewer_user_id?: UUID | null;
  internal_reviewed_at?: string | null;
  internal_review_comments?: string | null;
  external_submission_status: ResearchExternalSubmissionStatus | string;
  external_submission_reference?: string | null;
  submitted_external_at?: string | null;
  submission_confirmed_by_user_id?: UUID | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchGrantAwardModel {
  id: UUID;
  tenant_id: UUID;
  award_code: string;
  project_id: UUID;
  application_id?: UUID | null;
  funding_organization: string;
  award_amount: number;
  currency: string;
  received_amount: number;
  allocated_amount: number;
  spent_amount: number;
  remaining_balance: number;
  award_date: string;
  period_start_date: string;
  period_end_date: string;
  disbursement_schedule_json: Record<string, any>[];
  conditions_and_restrictions?: string | null;
  reporting_requirements?: string | null;
  financial_manager_id?: UUID | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchBudgetPlanModel {
  id: UUID;
  tenant_id: UUID;
  project_id: UUID;
  award_id?: UUID | null;
  version_number: number;
  category: string;
  item_description: string;
  proposed_amount: number;
  approved_amount: number;
  allocated_amount: number;
  actual_expenditure: number;
  committed_expenditure: number;
  remaining_balance: number;
  currency: string;
  justification?: string | null;
  effective_date?: string | null;
  revision_reason?: string | null;
  approved_by_user_id?: UUID | null;
  approved_at?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchMilestoneModel {
  id: UUID;
  tenant_id: UUID;
  project_id: UUID;
  title: string;
  description?: string | null;
  planned_date: string;
  actual_date?: string | null;
  responsible_user_id?: UUID | null;
  acceptance_criteria?: string | null;
  deliverable_reference?: string | null;
  completion_percentage: number;
  status: ResearchMilestoneStatus | string;
  is_mandatory_for_closure: boolean;
  dependencies_json: string[];
  blocker_notes?: string | null;
  verified_by_user_id?: UUID | null;
  verified_at?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchEthicsApprovalModel {
  id: UUID;
  tenant_id: UUID;
  project_id: UUID;
  approval_type: ResearchEthicsApprovalType | string;
  governing_policy: string;
  committee_name: string;
  application_reference: string;
  submission_date: string;
  review_due_date?: string | null;
  decision_date?: string | null;
  expiry_date?: string | null;
  status: ResearchEthicsApprovalStatus | string;
  conditions_and_restrictions?: string | null;
  reviewer_user_id?: UUID | null;
  decision_rationale?: string | null;
  document_id?: UUID | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchOutputModel {
  id: UUID;
  tenant_id: UUID;
  project_id?: UUID | null;
  output_type: ResearchOutputType | string;
  title: string;
  abstract?: string | null;
  authors_json: Record<string, any>[];
  publication_venue?: string | null;
  publication_date?: string | null;
  doi_or_urn?: string | null;
  citation_count: number;
  open_access_status: boolean;
  status: ResearchOutputStatus | string;
  is_verified: boolean;
  verified_by_user_id?: UUID | null;
  verified_at?: string | null;
  funding_acknowledgements?: string | null;
  document_id?: UUID | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchInventionDisclosureModel {
  id: UUID;
  tenant_id: UUID;
  project_id?: UUID | null;
  award_id?: UUID | null;
  disclosure_code: string;
  title: string;
  technical_description: string;
  inventors_json: Record<string, any>[];
  institutional_ownership_percentage: number;
  confidentiality_level: ResearchIPConfidentiality | string;
  patent_filing_status: ResearchPatentStatus | string;
  patent_application_number?: string | null;
  patent_jurisdiction?: string | null;
  patent_filing_date?: string | null;
  licensing_notes?: string | null;
  commercialization_revenue: number;
  document_id?: UUID | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchFacilityReferenceModel {
  id: UUID;
  tenant_id: UUID;
  project_id: UUID;
  facility_name: string;
  facility_type: string;
  asset_reference_id?: string | null;
  booking_reference?: string | null;
  usage_hours: number;
  notes?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface ResearchProjectRiskModel {
  id: UUID;
  tenant_id: UUID;
  project_id: UUID;
  risk_title: string;
  risk_category: string;
  likelihood: number;
  impact: number;
  calculated_risk_level: ResearchProjectRiskLevel | string;
  status: ResearchProjectRiskStatus | string;
  owner_user_id?: UUID | null;
  mitigation_plan?: string | null;
  target_resolution_date?: string | null;
  related_milestone_id?: UUID | null;
  resolution_notes?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ResearchAnalyticsSummaryModel {
  total_projects: number;
  active_projects: number;
  completed_projects: number;
  under_review_projects: number;
  total_proposed_budget: number;
  total_awarded_funding: number;
  total_actual_expenditure: number;
  budget_utilization_rate: number;
  total_funding_opportunities: number;
  total_grant_applications: number;
  approved_grant_applications: number;
  grant_success_rate: number;
  total_milestones: number;
  overdue_milestones: number;
  ethics_approvals_count: number;
  expiring_ethics_approvals: number;
  total_publications: number;
  verified_publications: number;
  total_citations: number;
  total_invention_disclosures: number;
  patents_filed_or_granted: number;
  commercialization_revenue: number;
}

export interface ResearchDeadlineSweepModel {
  processed_at: string;
  expiring_ethics_approvals_flagged: number;
  overdue_milestones_flagged: number;
  closing_opportunities_flagged: number;
}

// =============================================================================
// STEP 45: ENTERPRISE LIBRARY, LEARNING RESOURCES & KNOWLEDGE ACCESS
// =============================================================================

export enum LibraryBranchStatus {
  ACTIVE = "ACTIVE",
  INACTIVE = "INACTIVE",
  TEMPORARILY_CLOSED = "TEMPORARILY_CLOSED",
  RENOVATION = "RENOVATION",
}

export enum LibraryResourceType {
  BOOK = "BOOK",
  REFERENCE_BOOK = "REFERENCE_BOOK",
  JOURNAL = "JOURNAL",
  PERIODICAL = "PERIODICAL",
  RESEARCH_PAPER = "RESEARCH_PAPER",
  THESIS = "THESIS",
  DISSERTATION = "DISSERTATION",
  NEWSPAPER = "NEWSPAPER",
  MAGAZINE = "MAGAZINE",
  AUDIO_VIDEO = "AUDIO_VIDEO",
  E_BOOK = "E_BOOK",
  E_JOURNAL = "E_JOURNAL",
  INSTITUTIONAL_PUBLICATION = "INSTITUTIONAL_PUBLICATION",
  OTHER = "OTHER",
}

export enum LibraryCatalogStatus {
  DRAFT = "DRAFT",
  CATALOGUED = "CATALOGUED",
  UNDER_REVIEW = "UNDER_REVIEW",
  RESTRICTED = "RESTRICTED",
  WITHDRAWN = "WITHDRAWN",
}

export enum LibraryCopyCondition {
  NEW = "NEW",
  EXCELLENT = "EXCELLENT",
  GOOD = "GOOD",
  FAIR = "FAIR",
  POOR = "POOR",
  DAMAGED = "DAMAGED",
  UNDER_REPAIR = "UNDER_REPAIR",
  LOST = "LOST",
  MISSING = "MISSING",
  WITHDRAWN = "WITHDRAWN",
}

export enum LibraryCirculationStatus {
  AVAILABLE = "AVAILABLE",
  CHECKED_OUT = "CHECKED_OUT",
  RESERVED = "RESERVED",
  IN_TRANSIT = "IN_TRANSIT",
  ON_HOLD = "ON_HOLD",
  LOST = "LOST",
  DAMAGED = "DAMAGED",
  MISSING = "MISSING",
  UNDER_REPAIR = "UNDER_REPAIR",
  WITHDRAWN = "WITHDRAWN",
  RESTRICTED_REFERENCE_ONLY = "RESTRICTED_REFERENCE_ONLY",
}

export enum LibraryMemberCategory {
  UNDERGRADUATE_STUDENT = "UNDERGRADUATE_STUDENT",
  POSTGRADUATE_STUDENT = "POSTGRADUATE_STUDENT",
  DOCTORAL_RESEARCHER = "DOCTORAL_RESEARCHER",
  FACULTY = "FACULTY",
  STAFF = "STAFF",
  ALUMNI = "ALUMNI",
  VISITING_SCHOLAR = "VISITING_SCHOLAR",
  EXTERNAL = "EXTERNAL",
}

export enum LibraryMemberStatus {
  ACTIVE = "ACTIVE",
  EXPIRED = "EXPIRED",
  SUSPENDED_OVERDUE = "SUSPENDED_OVERDUE",
  SUSPENDED_FINES = "SUSPENDED_FINES",
  SUSPENDED_DISCIPLINARY = "SUSPENDED_DISCIPLINARY",
  INACTIVE = "INACTIVE",
}

export enum LibraryLoanStatus {
  ACTIVE = "ACTIVE",
  RETURNED = "RETURNED",
  OVERDUE = "OVERDUE",
  LOST = "LOST",
  DAMAGED = "DAMAGED",
  CLAIMED_RETURNED = "CLAIMED_RETURNED",
}

export enum LibraryReservationStatus {
  WAITING = "WAITING",
  ALLOCATED_PENDING_PICKUP = "ALLOCATED_PENDING_PICKUP",
  FULFILLED = "FULFILLED",
  CANCELLED = "CANCELLED",
  EXPIRED = "EXPIRED",
}

export enum LibraryFineCategory {
  OVERDUE = "OVERDUE",
  LOST_ITEM = "LOST_ITEM",
  DAMAGED_ITEM = "DAMAGED_ITEM",
  PROCESSING_FEE = "PROCESSING_FEE",
  MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT",
}

export enum LibraryFineStatus {
  ESTIMATED = "ESTIMATED",
  ASSESSED = "ASSESSED",
  POSTED_TO_FINANCE = "POSTED_TO_FINANCE",
  PAID = "PAID",
  PARTIALLY_PAID = "PARTIALLY_PAID",
  WAIVED = "WAIVED",
  DISPUTED = "DISPUTED",
}

export enum LibraryAcquisitionStatus {
  REQUESTED = "REQUESTED",
  UNDER_REVIEW = "UNDER_REVIEW",
  APPROVED = "APPROVED",
  ORDERED = "ORDERED",
  RECEIVED = "RECEIVED",
  CATALOGUED = "CATALOGUED",
  REJECTED = "REJECTED",
  CANCELLED = "CANCELLED",
}

export enum LibrarySubscriptionType {
  PRINT_JOURNAL = "PRINT_JOURNAL",
  ONLINE_DATABASE = "ONLINE_DATABASE",
  E_JOURNAL_PACKAGE = "E_JOURNAL_PACKAGE",
  MAGAZINE = "MAGAZINE",
  NEWSPAPER = "NEWSPAPER",
  INSTITUTIONAL_MEMBERSHIP = "INSTITUTIONAL_MEMBERSHIP",
}

export enum LibrarySubscriptionStatus {
  ACTIVE = "ACTIVE",
  EXPIRED = "EXPIRED",
  PENDING_RENEWAL = "PENDING_RENEWAL",
  CANCELLED = "CANCELLED",
}

export enum LibraryInventoryAuditStatus {
  DRAFT = "DRAFT",
  IN_PROGRESS = "IN_PROGRESS",
  RECONCILIATION = "RECONCILIATION",
  COMPLETED = "COMPLETED",
  CANCELLED = "CANCELLED",
}

export enum LibraryAuditScanResult {
  PRESENT_ON_SHELF = "PRESENT_ON_SHELF",
  CHECKED_OUT_VERIFIED = "CHECKED_OUT_VERIFIED",
  MISSING = "MISSING",
  MISPLACED = "MISPLACED",
  DAMAGED = "DAMAGED",
  UNRECORDED_ACCESSION = "UNRECORDED_ACCESSION",
}

export interface LibraryBranchModel {
  id: UUID;
  tenant_id: UUID;
  branch_code: string;
  name: string;
  description?: string | null;
  campus_id?: UUID | null;
  department_id?: UUID | null;
  location_building?: string | null;
  location_floor?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  operating_hours_json: Record<string, any>;
  closure_dates_json: any[];
  head_librarian_user_id?: UUID | null;
  status: LibraryBranchStatus | string;
  is_active: boolean;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryLendingPolicyModel {
  id: UUID;
  tenant_id: UUID;
  policy_code: string;
  name: string;
  library_id?: UUID | null;
  member_category: LibraryMemberCategory | string;
  resource_type: LibraryResourceType | string;
  max_items_allowed: number;
  loan_period_days: number;
  max_renewals_allowed: number;
  fine_grace_period_days: number;
  fine_daily_rate: number;
  max_fine_limit: number;
  allow_hold_reservations: boolean;
  priority_weight: number;
  is_active: boolean;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryCatalogItemModel {
  id: UUID;
  tenant_id: UUID;
  catalog_code: string;
  title: string;
  subtitle?: string | null;
  authors_json: string[];
  editors_json: string[];
  contributors_json: string[];
  publisher?: string | null;
  publication_year?: number | null;
  edition?: string | null;
  primary_language: string;
  isbn_or_issn?: string | null;
  doi?: string | null;
  classification_number?: string | null;
  subject_classification?: string | null;
  keywords_json: string[];
  resource_type: LibraryResourceType | string;
  description_abstract?: string | null;
  is_digital: boolean;
  digital_access_url?: string | null;
  document_file_id?: UUID | null;
  status: LibraryCatalogStatus | string;
  total_copies_count: number;
  available_copies_count: number;
  created_by_user_id?: UUID | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryPhysicalCopyModel {
  id: UUID;
  tenant_id: UUID;
  catalog_item_id: UUID;
  library_id: UUID;
  accession_number: string;
  barcode?: string | null;
  rfid_tag?: string | null;
  shelf_location?: string | null;
  call_number?: string | null;
  acquisition_date?: string | null;
  purchase_price?: number | null;
  currency: string;
  condition_grade: LibraryCopyCondition | string;
  circulation_status: LibraryCirculationStatus | string;
  is_reference_only: boolean;
  last_inventoried_at?: string | null;
  withdrawal_date?: string | null;
  withdrawal_reason?: string | null;
  condition_notes?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryMemberProfileModel {
  id: UUID;
  tenant_id: UUID;
  user_id: UUID;
  membership_number: string;
  member_category: LibraryMemberCategory | string;
  home_library_id?: UUID | null;
  student_profile_id?: UUID | null;
  staff_profile_id?: UUID | null;
  status: LibraryMemberStatus | string;
  valid_from: string;
  valid_until?: string | null;
  max_borrow_limit_override?: number | null;
  current_active_loans: number;
  current_outstanding_fines: number;
  is_borrowing_suspended: boolean;
  suspension_reason?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryCirculationLoanModel {
  id: UUID;
  tenant_id: UUID;
  loan_reference_code: string;
  copy_id: UUID;
  member_id: UUID;
  user_id: UUID;
  library_id: UUID;
  issued_at: string;
  issued_by_user_id: UUID;
  due_date: string;
  returned_at?: string | null;
  returned_to_library_id?: UUID | null;
  received_by_user_id?: UUID | null;
  renewal_count: number;
  max_renewals_allowed: number;
  status: LibraryLoanStatus | string;
  calculated_fine_amount: number;
  staff_override_used: boolean;
  override_justification?: string | null;
  notes?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryReservationModel {
  id: UUID;
  tenant_id: UUID;
  reservation_code: string;
  catalog_item_id: UUID;
  copy_id?: UUID | null;
  member_id: UUID;
  user_id: UUID;
  library_id: UUID;
  placed_at: string;
  allocated_at?: string | null;
  allocated_copy_id?: UUID | null;
  pickup_deadline?: string | null;
  fulfilled_at?: string | null;
  cancelled_at?: string | null;
  cancellation_reason?: string | null;
  expired_at?: string | null;
  queue_position: number;
  priority_rank: number;
  status: LibraryReservationStatus | string;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryFineRecordModel {
  id: UUID;
  tenant_id: UUID;
  fine_reference_code: string;
  loan_id?: UUID | null;
  member_id: UUID;
  user_id: UUID;
  fine_category: LibraryFineCategory | string;
  base_amount: number;
  waived_amount: number;
  final_payable_amount: number;
  currency: string;
  fine_status: LibraryFineStatus | string;
  days_overdue: number;
  calculation_basis?: string | null;
  finance_invoice_id?: UUID | null;
  finance_payment_reference?: string | null;
  waiver_reason?: string | null;
  waived_by_user_id?: UUID | null;
  assessed_at: string;
  resolved_at?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryAcquisitionRequestModel {
  id: UUID;
  tenant_id: UUID;
  request_code: string;
  title: string;
  author?: string | null;
  publisher?: string | null;
  isbn_or_issn?: string | null;
  requested_by_user_id: UUID;
  department_id?: UUID | null;
  library_id?: UUID | null;
  justification?: string | null;
  number_of_copies: number;
  estimated_unit_cost?: number | null;
  total_estimated_cost?: number | null;
  currency: string;
  approval_status: LibraryAcquisitionStatus | string;
  approved_by_user_id?: UUID | null;
  purchase_order_reference?: string | null;
  order_date?: string | null;
  receipt_date?: string | null;
  accession_numbers_created_json: string[];
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibrarySubscriptionModel {
  id: UUID;
  tenant_id: UUID;
  subscription_code: string;
  publication_title: string;
  publisher_or_vendor: string;
  subscription_type: LibrarySubscriptionType | string;
  start_date: string;
  end_date: string;
  renewal_deadline_date?: string | null;
  frequency: string;
  annual_subscription_cost: number;
  currency: string;
  library_id?: UUID | null;
  status: LibrarySubscriptionStatus | string;
  digital_access_portal_url?: string | null;
  expected_issues_count: number;
  received_issues_count: number;
  renewal_decision?: string | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryDigitalResourceAccessModel {
  id: UUID;
  tenant_id: UUID;
  catalog_item_id?: UUID | null;
  subscription_id?: UUID | null;
  user_id: UUID;
  member_id?: UUID | null;
  access_timestamp: string;
  ip_address?: string | null;
  access_type: string;
  download_token?: string | null;
  token_expires_at?: string | null;
  bytes_transferred: number;
  metadata_json: Record<string, any>;
  created_at: string;
}

export interface LibraryInventoryAuditModel {
  id: UUID;
  tenant_id: UUID;
  audit_code: string;
  title: string;
  library_id: UUID;
  location_section?: string | null;
  audit_scope: string;
  start_date: string;
  end_date?: string | null;
  status: LibraryInventoryAuditStatus | string;
  auditor_user_id?: UUID | null;
  total_expected_copies: number;
  verified_present_copies: number;
  missing_copies_count: number;
  damaged_copies_count: number;
  misplaced_copies_count: number;
  reconciliation_notes?: string | null;
  approved_by_user_id?: UUID | null;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LibraryInventoryAuditItemModel {
  id: UUID;
  tenant_id: UUID;
  audit_id: UUID;
  copy_id: UUID;
  accession_number: string;
  scanned_barcode?: string | null;
  expected_status: string;
  scanned_status: string;
  shelf_location_found?: string | null;
  discrepancy_resolved: boolean;
  resolution_action?: string | null;
  audited_at: string;
  audited_by_user_id?: UUID | null;
  metadata_json: Record<string, any>;
}

export interface LibraryAnalyticsSummaryModel {
  total_branches: number;
  total_catalog_titles: number;
  total_physical_copies: number;
  available_copies: number;
  total_active_members: number;
  total_active_loans: number;
  total_overdue_loans: number;
  total_active_reservations: number;
  total_outstanding_fines: number;
  total_subscriptions: number;
  active_subscriptions: number;
  pending_acquisitions: number;
  active_inventory_audits: number;
  circulation_rate_percentage: number;
}

export interface LibraryDeadlineSweepModel {
  processed_at: string;
  overdue_loans_flagged: number;
  fines_computed_amount: number;
  expired_reservations_released: number;
  expiring_subscriptions_flagged: number;
}





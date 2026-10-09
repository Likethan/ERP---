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
}

export enum RetentionTriggerEvent {
  CREATION = "CREATION",
  COMPLETION = "COMPLETION",
  GRADUATION = "GRADUATION",
  EXPIRATION = "EXPIRATION",
  DEACTIVATION = "DEACTIVATION",
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

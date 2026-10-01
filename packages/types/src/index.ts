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
 * Standard API Envelope for all successful REST responses
 */
export interface ApiResponse<T> {
  success: true;
  data: T;
  meta?: {
    timestamp: string;
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







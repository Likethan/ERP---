export type StatutoryApprovalCategory =
  | "DEPARTMENT_ACADEMIC_REQUEST"
  | "ACADEMIC_CALENDAR_CHANGE"
  | "TIMETABLE_CHANGE"
  | "FACULTY_LEAVE"
  | "ACADEMIC_EVENT"
  | "EXAMINATION_REQUEST"
  | "DEPARTMENT_ADMIN_REQUEST"
  | "SPECIAL_ACADEMIC_PERMISSION"
  | "ACADEMIC_PERFORMANCE_INTERVENTION";

export type StatutoryApprovalStatus =
  "PENDING" | "APPROVED" | "REJECTED" | "MODIFICATION_REQUESTED" | "FORWARDED";

export type ApprovalUrgency = "ROUTINE" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ApprovalAuditEntry {
  action: string;
  by: string;
  timestamp: string;
  notes: string;
}

export interface StatutoryApprovalItem {
  id: string;
  title: string;
  category: StatutoryApprovalCategory;
  department_id: string;
  department_name: string;
  submitted_by: string;
  submission_date: string;
  urgency: ApprovalUrgency;
  status: StatutoryApprovalStatus;
  details: Record<string, any>;
  remarks?: string | null;
  decided_by?: string | null;
  decision_date?: string | null;
  audit_trail: ApprovalAuditEntry[];
}

export interface DepartmentHealthMetric {
  id: string;
  name: string;
  code: string;
  hod: string;
  students: number;
  faculty: number;
  faculty_ratio: string;
  attendance_rate: number;
  syllabus_progress: number;
  accreditation_score: number;
  status: "EXEMPLARY" | "ON_TRACK" | "ATTENTION_NEEDED" | "CRITICAL";
  pending_approvals: number;
}

export interface CriticalAcademicAlert {
  id: string;
  severity: "ROUTINE" | "MEDIUM" | "HIGH" | "CRITICAL";
  department: string;
  title: string;
  detail: string;
}

export interface RecentInstitutionalActivity {
  id: string;
  timestamp: string;
  category: string;
  title: string;
  department: string;
}

export interface VicePrincipalDashboardData {
  academic_year: string;
  semester_filter?: number | null;
  kpis: {
    total_departments: number;
    total_students: number;
    total_faculty: number;
    overall_student_attendance: number;
    faculty_attendance: number;
    syllabus_completion_rate: number;
    examination_readiness: number;
    pending_approvals_count: number;
    critical_academic_alerts: number;
  };
  department_metrics: DepartmentHealthMetric[];
  critical_alerts: CriticalAcademicAlert[];
  recent_institutional_activities: RecentInstitutionalActivity[];
}

export interface DepartmentMonitoringItem {
  id: string;
  name: string;
  code: string;
  hod_name: string;
  hod_email: string;
  student_count: number;
  faculty_count: number;
  faculty_ratio: string;
  student_attendance: number;
  faculty_attendance: number;
  syllabus_progress: number;
  pending_approvals: number;
  status: "EXEMPLARY" | "ON_TRACK" | "ATTENTION_NEEDED" | "CRITICAL";
  accreditation_score: number;
  delay_alerts_count: number;
  labs_count: number;
  classrooms_count: number;
}

export interface CalendarMilestone {
  id: string;
  event: string;
  scheduled_date: string;
  actual_date?: string | null;
  status: "COMPLETED" | "UPCOMING" | "OVERDUE";
  variance_days: number;
}

export interface SyllabusDelayItem {
  subject_code: string;
  subject_name: string;
  department: string;
  semester: number;
  faculty_name: string;
  planned_topics: number;
  completed_topics: number;
  completion_percentage: number;
  expected_percentage: number;
  lag_days: number;
  remedial_status: string;
}

export interface AcademicMonitoringData {
  academic_year: string;
  semester_type: string;
  milestones: CalendarMilestone[];
  syllabus_delay_tracking: SyllabusDelayItem[];
  timetable_coverage: {
    total_scheduled_hours_weekly: number;
    classes_conducted_on_schedule_pct: number;
    faculty_substitution_rate_pct: number;
    unassigned_lecture_slots: number;
  };
}

export interface FacultySupervisionItem {
  id: string;
  name: string;
  employee_code: string;
  designation: string;
  department: string;
  email: string;
  weekly_teaching_hours: number;
  assigned_subjects: string[];
  status: "NORMAL" | "OVERLOADED" | "UNDERLOADED";
  attendance_rate: number;
  active_leaves: number;
}

export interface FacultySupervisionData {
  workload_summary: {
    total_faculty: number;
    compliant_workload_count: number;
    overloaded_count: number;
    underloaded_count: number;
    average_teaching_hours: number;
    statutory_min_hours: number;
    statutory_max_hours: number;
  };
  faculty: FacultySupervisionItem[];
}

export interface LowAttendanceStudentItem {
  roll_number: string;
  name: string;
  department: string;
  semester: number;
  section: string;
  attendance_percentage: number;
  attended_sessions: number;
  total_sessions: number;
  shortfall_sessions: number;
  mentor_name: string;
  risk_level: "ROUTINE" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: string;
}

export interface InstitutionalStrengthItem {
  department: string;
  year_1: number;
  year_2: number;
  year_3: number;
  year_4: number;
  total: number;
}

export interface StudentSupervisionData {
  threshold: number;
  total_students_monitored: number;
  total_shortage_students: number;
  institutional_strength: InstitutionalStrengthItem[];
  low_attendance_radar: LowAttendanceStudentItem[];
  academic_backlogs_overview: {
    zero_backlogs_pct: number;
    one_to_two_backlogs_pct: number;
    three_plus_backlogs_pct: number;
    critical_academic_probation_count: number;
  };
}

export interface ExaminationScheduleItem {
  id: string;
  name: string;
  date_range: string;
  type: string;
  status: string;
  question_papers_moderated?: number;
  question_papers_total?: number;
  seating_plan_published?: boolean;
  external_examiners_count?: number;
  batches_scheduled?: number;
  total_halls?: number;
  chief_superintendent?: string;
}

export interface CiaMarkSubmissionItem {
  department: string;
  total_courses: number;
  submitted: number;
  locked: number;
  pending: number;
  status: string;
}

export interface ExaminationsOversightData {
  schedules: ExaminationScheduleItem[];
  cia_mark_submissions: CiaMarkSubmissionItem[];
  results_analysis: {
    overall_institutional_pass_pct: number;
    first_class_with_distinction_pct: number;
    first_class_pct: number;
    arrear_rate_pct: number;
    department_pass_ranking: {
      rank: number;
      department: string;
      pass_pct: number;
    }[];
  };
}

export interface ReportItem {
  id: string;
  name: string;
  type: string;
  generated_on: string;
  format: string[];
  description: string;
}

export interface InstitutionalReportsData {
  academic_year: string;
  available_reports: ReportItem[];
  summary_metrics: Record<string, number>;
}

export interface InstitutionalAnnouncement {
  id: string;
  title: string;
  target_audience: string;
  priority: "ROUTINE" | "HIGH" | "CRITICAL";
  published_at: string;
  author: string;
  summary: string;
  pinned: boolean;
}

export interface InstitutionalAuditLog {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  entity: string;
  details: string;
  ip_address: string;
}

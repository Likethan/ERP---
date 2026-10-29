/**
 * CampusOS Workforce Management Domain Types (Step 51)
 * "One Campus. One System. One Source of Truth."
 */

export type EmploymentType =
  | "PERMANENT"
  | "CONTRACT"
  | "TEMPORARY"
  | "VISITING"
  | "ADJUNCT"
  | "PROBATION";

export type EmploymentStatus =
  | "DRAFT"
  | "ONBOARDING"
  | "ACTIVE"
  | "ON_LEAVE"
  | "SUSPENDED"
  | "NOTICE_PERIOD"
  | "SEPARATED"
  | "ARCHIVED";

export type EmploymentChangeType =
  | "JOINING"
  | "TRANSFER"
  | "PROMOTION"
  | "DESIGNATION_CHANGE"
  | "DEPARTMENT_CHANGE"
  | "MANAGER_CHANGE"
  | "STATUS_CHANGE"
  | "CONTRACT_RENEWAL"
  | "COMPENSATION_REVISION"
  | "SEPARATION";

export type LifecycleCaseType =
  | "ONBOARDING"
  | "OFFBOARDING"
  | "PROBATION_REVIEW"
  | "CONFIRMATION"
  | "TRANSFER";

export type LifecycleCaseStatus =
  | "DRAFT"
  | "IN_PROGRESS"
  | "PENDING_APPROVAL"
  | "COMPLETED"
  | "CANCELLED"
  | "BLOCKED";

export type LifecycleTaskStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "WAIVED"
  | "BLOCKED";

export type LeaveRequestStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "CANCELLED"
  | "WITHDRAWN";

export type HRCaseCategory =
  | "PROFILE_UPDATE"
  | "EMPLOYMENT_LETTER"
  | "SALARY_QUERY"
  | "CONTRACT_QUERY"
  | "LEAVE_CORRECTION"
  | "GRIEVANCE"
  | "GENERAL_INQUIRY";

export type HRCaseStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "RESOLVED"
  | "CLOSED"
  | "REJECTED";

export interface WorkforceEmployeeItem {
  id: string;
  tenant_id: string;
  user_id: string;
  employee_number: string;
  first_name: string;
  last_name: string;
  full_name: string;
  official_email: string;
  phone_number?: string;
  employment_type: EmploymentType;
  employment_status: EmploymentStatus;
  designation: string;
  job_title: string;
  department_id?: string;
  department_name?: string;
  campus_id?: string;
  campus_name?: string;
  reporting_manager_id?: string;
  reporting_manager_name?: string;
  work_location?: string;
  joining_date: string;
  probation_end_date?: string;
  confirmation_date?: string;
  contract_start_date?: string;
  contract_end_date?: string;
  separation_date?: string;
  separation_reason?: string;
  notice_period_days: number;
  qualifications: Array<Record<string, unknown>>;
  certifications: Array<Record<string, unknown>>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkforceEmploymentHistoryItem {
  id: string;
  employee_id: string;
  change_type: EmploymentChangeType;
  effective_date: string;
  previous_designation?: string;
  new_designation?: string;
  previous_job_title?: string;
  new_job_title?: string;
  previous_status?: string;
  new_status?: string;
  notes?: string;
  recorded_by_user_id?: string;
  created_at: string;
}

export interface WorkforceLifecycleTaskItem {
  id: string;
  case_id: string;
  title: string;
  description?: string;
  category: string;
  assigned_role: string;
  assigned_to_user_id?: string;
  assigned_to_name?: string;
  status: LifecycleTaskStatus;
  due_date?: string;
  completed_at?: string;
  completed_by_user_id?: string;
  completion_evidence?: string;
  is_mandatory: boolean;
}

export interface WorkforceLifecycleCaseItem {
  id: string;
  employee_id: string;
  employee_name: string;
  case_type: LifecycleCaseType;
  status: LifecycleCaseStatus;
  initiated_date: string;
  target_completion_date?: string;
  completed_date?: string;
  total_tasks: number;
  completed_tasks: number;
  mandatory_tasks_remaining: number;
  notes?: string;
  tasks: WorkforceLifecycleTaskItem[];
  created_at: string;
}

export interface WorkforceLeaveTypeItem {
  id: string;
  code: string;
  name: string;
  description?: string;
  is_paid: boolean;
  is_encashable: boolean;
  requires_supporting_doc: boolean;
  is_active: boolean;
}

export interface WorkforceLeavePolicyItem {
  id: string;
  leave_type_id: string;
  leave_type_name: string;
  policy_code: string;
  name: string;
  effective_from: string;
  effective_to?: string;
  annual_entitlement: number;
  accrual_frequency: string;
  accrual_rate: number;
  carry_forward_limit: number;
  max_consecutive_days: number;
  allow_half_day: boolean;
  is_active: boolean;
}

export interface WorkforceLeaveBalanceItem {
  id: string;
  employee_id: string;
  employee_name: string;
  leave_type_id: string;
  leave_type_code: string;
  leave_type_name: string;
  balance_year: number;
  opening_balance: number;
  accrued_days: number;
  used_days: number;
  pending_days: number;
  adjusted_days: number;
  carried_forward_days: number;
  available_days: number;
}

export interface WorkforceLeaveRequestItem {
  id: string;
  employee_id: string;
  employee_name: string;
  employee_number: string;
  department_name?: string;
  leave_type_id: string;
  leave_type_name: string;
  request_number: string;
  start_date: string;
  end_date: string;
  is_half_day: boolean;
  half_day_session?: string;
  total_days: number;
  reason: string;
  supporting_document_url?: string;
  status: LeaveRequestStatus;
  decision_notes?: string;
  has_timetable_conflicts: boolean;
  submitted_at: string;
  created_at: string;
}

export interface WorkforceAvailabilityResponse {
  employee_id: string;
  employee_name: string;
  start_date: string;
  end_date: string;
  is_available: boolean;
  status: string;
  approved_leave_days: string[];
  pending_leave_days: string[];
  timetable_session_conflicts: Array<{
    conflict_date: string;
    timetable_session_id: string;
    course_code: string;
    start_time: string;
    end_time: string;
    conflict_type: string;
  }>;
}

export interface WorkforceWorkloadSummary {
  employee_id: string;
  employee_name: string;
  employee_number: string;
  department_name?: string;
  expected_hours: number;
  scheduled_teaching_hours: number;
  adjusted_hours: number;
  total_actual_hours: number;
  variance_hours: number;
  load_status: "BALANCED" | "OVERLOAD" | "UNDER_ALLOCATED";
  sessions_count: number;
}

export interface WorkforceHRCaseItem {
  id: string;
  employee_id: string;
  employee_name: string;
  case_number: string;
  category: HRCaseCategory;
  priority: string;
  status: HRCaseStatus;
  subject: string;
  description: string;
  proposed_changes?: Record<string, unknown>;
  resolution?: string;
  assigned_to_user_id?: string;
  assigned_to_name?: string;
  is_confidential: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkforceReportOverview {
  headcount: {
    total_active_employees: number;
    total_onboarding: number;
    total_on_leave: number;
    total_notice_period: number;
    by_employment_type: Record<string, number>;
  };
  department_distribution: Record<string, number>;
  campus_distribution: Record<string, number>;
  upcoming_probation_milestones: Array<{
    employee_id: string;
    employee_name: string;
    employee_number: string;
    department_name?: string;
    probation_end_date: string;
    days_remaining: number;
  }>;
  upcoming_contract_expirations: Array<{
    employee_id: string;
    employee_name: string;
    employee_number: string;
    department_name?: string;
    contract_end_date: string;
    days_remaining: number;
  }>;
  leave_metrics: {
    total_leave_requests_submitted: number;
    total_leave_days_approved: number;
    currently_pending_requests: number;
  };
  hr_case_metrics: {
    total_open_cases: number;
    total_resolved_cases: number;
    sla_compliance_rate_pct: number;
  };
}

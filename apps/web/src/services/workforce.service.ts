/**
 * CampusOS Workforce Management & Staff Lifecycle Service (Step 51)
 * "One Campus. One System. One Source of Truth."
 *
 * Interacts with FastAPI `/api/v1/workforce/*` endpoints.
 */

import { apiFetch } from "@/lib/api-client";
import type {
  WorkforceEmployeeItem,
  WorkforceEmploymentHistoryItem,
  WorkforceLifecycleCaseItem,
  WorkforceLifecycleTaskItem,
  WorkforceLeaveTypeItem,
  WorkforceLeavePolicyItem,
  WorkforceLeaveBalanceItem,
  WorkforceLeaveRequestItem,
  WorkforceAvailabilityResponse,
  WorkforceWorkloadSummary,
  WorkforceHRCaseItem,
  WorkforceReportOverview,
  EmploymentType,
  EmploymentStatus,
  LifecycleTaskStatus,
  HRCaseCategory,
} from "@/types/workforce";

export interface WorkforceEmployeeFilterParams {
  search?: string;
  department_id?: string;
  campus_id?: string;
  employment_type?: EmploymentType;
  employment_status?: EmploymentStatus;
  page?: number;
  page_size?: number;
}

export interface WorkforceEmployeeCreatePayload {
  user_id: string;
  employee_number?: string;
  designation: string;
  job_title: string;
  department_id?: string;
  campus_id?: string;
  reporting_manager_id?: string;
  employment_type?: EmploymentType;
  employment_status?: EmploymentStatus;
  work_location?: string;
  joining_date: string;
  probation_end_date?: string;
  notice_period_days?: number;
  qualifications?: Array<Record<string, unknown>>;
  certifications?: Array<Record<string, unknown>>;
}

export interface WorkforceEmployeeUpdatePayload {
  designation?: string;
  job_title?: string;
  department_id?: string;
  campus_id?: string;
  reporting_manager_id?: string;
  employment_type?: EmploymentType;
  work_location?: string;
  probation_end_date?: string;
  contract_end_date?: string;
  notice_period_days?: number;
}

export interface WorkforceLeaveRequestSubmitPayload {
  employee_id: string;
  leave_type_id: string;
  start_date: string;
  end_date: string;
  is_half_day?: boolean;
  half_day_session?: "FIRST_HALF" | "SECOND_HALF";
  reason: string;
  supporting_document_url?: string;
}

export interface WorkforceHRCaseCreatePayload {
  employee_id?: string;
  category: HRCaseCategory;
  priority?: "LOW" | "NORMAL" | "HIGH" | "URGENT";
  subject: string;
  description: string;
  proposed_changes?: Record<string, unknown>;
  is_confidential?: boolean;
}

class EnterpriseWorkforceService {
  // =========================================================================
  // 1. Employee Master & Employment Lifecycle
  // =========================================================================

  async listEmployees(params?: WorkforceEmployeeFilterParams): Promise<{ items: WorkforceEmployeeItem[]; total: number }> {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.department_id) q.set("department_id", params.department_id);
    if (params?.campus_id) q.set("campus_id", params.campus_id);
    if (params?.employment_type) q.set("employment_type", params.employment_type);
    if (params?.employment_status) q.set("employment_status", params.employment_status);
    if (params?.page) q.set("page", params.page.toString());
    if (params?.page_size) q.set("page_size", params.page_size.toString());

    const qs = q.toString() ? `?${q.toString()}` : "";
    const res = await apiFetch<WorkforceEmployeeItem[]>(`/api/v1/workforce/employees${qs}`);
    const items = res.data || [];
    return {
      items,
      total: (res.meta?.total as number) ?? items.length,
    };
  }

  async getEmployee(employeeId: string): Promise<WorkforceEmployeeItem | null> {
    const res = await apiFetch<WorkforceEmployeeItem>(`/api/v1/workforce/employees/${employeeId}`);
    return res.data || null;
  }

  async createEmployee(payload: WorkforceEmployeeCreatePayload): Promise<WorkforceEmployeeItem> {
    const res = await apiFetch<WorkforceEmployeeItem>("/api/v1/workforce/employees", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  async updateEmployee(employeeId: string, payload: WorkforceEmployeeUpdatePayload): Promise<WorkforceEmployeeItem> {
    const res = await apiFetch<WorkforceEmployeeItem>(`/api/v1/workforce/employees/${employeeId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  async transitionStatus(
    employeeId: string,
    newStatus: EmploymentStatus,
    reason: string
  ): Promise<WorkforceEmployeeItem> {
    const res = await apiFetch<WorkforceEmployeeItem>(`/api/v1/workforce/employees/${employeeId}/transition-status`, {
      method: "POST",
      body: JSON.stringify({ new_status: newStatus, reason }),
    });
    return res.data;
  }

  async getEmploymentHistory(employeeId: string): Promise<WorkforceEmploymentHistoryItem[]> {
    const res = await apiFetch<WorkforceEmploymentHistoryItem[]>(
      `/api/v1/workforce/employees/${employeeId}/employment-history`
    );
    return res.data || [];
  }

  // =========================================================================
  // 2. Onboarding & Offboarding Lifecycle
  // =========================================================================

  async listLifecycleCases(params?: {
    employee_id?: string;
    case_type?: string;
    status?: string;
  }): Promise<WorkforceLifecycleCaseItem[]> {
    const q = new URLSearchParams();
    if (params?.employee_id) q.set("employee_id", params.employee_id);
    if (params?.case_type) q.set("case_type", params.case_type);
    if (params?.status) q.set("status", params.status);

    const qs = q.toString() ? `?${q.toString()}` : "";
    const res = await apiFetch<WorkforceLifecycleCaseItem[]>(`/api/v1/workforce/lifecycle/cases${qs}`);
    return res.data || [];
  }

  async updateLifecycleTask(
    taskId: string,
    payload: { status: LifecycleTaskStatus; completion_evidence?: string; blocker_reason?: string }
  ): Promise<WorkforceLifecycleTaskItem> {
    const res = await apiFetch<WorkforceLifecycleTaskItem>(`/api/v1/workforce/lifecycle/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  async initiateSeparation(payload: {
    employee_id: string;
    separation_date: string;
    separation_reason: string;
    notice_period_days?: number;
    notes?: string;
  }): Promise<WorkforceLifecycleCaseItem> {
    const res = await apiFetch<WorkforceLifecycleCaseItem>("/api/v1/workforce/offboarding/initiate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  // =========================================================================
  // 3. Leave Engine: Types, Policies, Balances, Requests, Approvals
  // =========================================================================

  async listLeaveTypes(): Promise<WorkforceLeaveTypeItem[]> {
    const res = await apiFetch<WorkforceLeaveTypeItem[]>("/api/v1/workforce/leave/types");
    return res.data || [];
  }

  async listLeavePolicies(): Promise<WorkforceLeavePolicyItem[]> {
    const res = await apiFetch<WorkforceLeavePolicyItem[]>("/api/v1/workforce/leave/policies");
    return res.data || [];
  }

  async listLeaveBalances(params?: { employee_id?: string; year?: number }): Promise<WorkforceLeaveBalanceItem[]> {
    const q = new URLSearchParams();
    if (params?.employee_id) q.set("employee_id", params.employee_id);
    if (params?.year) q.set("year", params.year.toString());

    const qs = q.toString() ? `?${q.toString()}` : "";
    const res = await apiFetch<WorkforceLeaveBalanceItem[]>(`/api/v1/workforce/leave/balances${qs}`);
    return res.data || [];
  }

  async listLeaveRequests(params?: {
    employee_id?: string;
    department_id?: string;
    status?: string;
  }): Promise<WorkforceLeaveRequestItem[]> {
    const q = new URLSearchParams();
    if (params?.employee_id) q.set("employee_id", params.employee_id);
    if (params?.department_id) q.set("department_id", params.department_id);
    if (params?.status) q.set("status", params.status);

    const qs = q.toString() ? `?${q.toString()}` : "";
    const res = await apiFetch<WorkforceLeaveRequestItem[]>(`/api/v1/workforce/leave/requests${qs}`);
    return res.data || [];
  }

  async submitLeaveRequest(payload: WorkforceLeaveRequestSubmitPayload): Promise<WorkforceLeaveRequestItem> {
    const res = await apiFetch<WorkforceLeaveRequestItem>("/api/v1/workforce/leave/requests", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  async approveLeaveRequest(requestId: string, notes?: string): Promise<WorkforceLeaveRequestItem> {
    const res = await apiFetch<WorkforceLeaveRequestItem>(`/api/v1/workforce/leave/requests/${requestId}/approve`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
    return res.data;
  }

  async rejectLeaveRequest(requestId: string, rejectionReason: string): Promise<WorkforceLeaveRequestItem> {
    const res = await apiFetch<WorkforceLeaveRequestItem>(`/api/v1/workforce/leave/requests/${requestId}/reject`, {
      method: "POST",
      body: JSON.stringify({ rejection_reason: rejectionReason }),
    });
    return res.data;
  }

  async cancelLeaveRequest(requestId: string): Promise<WorkforceLeaveRequestItem> {
    const res = await apiFetch<WorkforceLeaveRequestItem>(`/api/v1/workforce/leave/requests/${requestId}/cancel`, {
      method: "POST",
    });
    return res.data;
  }

  // =========================================================================
  // 4. Availability & Academic Timetable Integration
  // =========================================================================

  async checkAvailability(
    employeeId: string,
    startDate: string,
    endDate: string
  ): Promise<WorkforceAvailabilityResponse> {
    const res = await apiFetch<WorkforceAvailabilityResponse>(
      `/api/v1/workforce/availability/check?employee_id=${employeeId}&start_date=${startDate}&end_date=${endDate}`
    );
    return res.data;
  }

  // =========================================================================
  // 5. Workload Planning & Expectations
  // =========================================================================

  async getWorkloadSummary(params: {
    employee_id: string;
    academic_year_id?: string;
    semester_id?: string;
  }): Promise<WorkforceWorkloadSummary> {
    const q = new URLSearchParams();
    q.set("employee_id", params.employee_id);
    if (params.academic_year_id) q.set("academic_year_id", params.academic_year_id);
    if (params.semester_id) q.set("semester_id", params.semester_id);

    const res = await apiFetch<WorkforceWorkloadSummary>(`/api/v1/workforce/workload/summary?${q.toString()}`);
    return res.data;
  }

  // =========================================================================
  // 6. HR Cases & Employee Self-Service
  // =========================================================================

  async listHRCases(params?: {
    employee_id?: string;
    status?: string;
    category?: string;
  }): Promise<WorkforceHRCaseItem[]> {
    const q = new URLSearchParams();
    if (params?.employee_id) q.set("employee_id", params.employee_id);
    if (params?.status) q.set("status", params.status);
    if (params?.category) q.set("category", params.category);

    const qs = q.toString() ? `?${q.toString()}` : "";
    const res = await apiFetch<WorkforceHRCaseItem[]>(`/api/v1/workforce/hr-cases${qs}`);
    return res.data || [];
  }

  async createHRCase(payload: WorkforceHRCaseCreatePayload): Promise<WorkforceHRCaseItem> {
    const res = await apiFetch<WorkforceHRCaseItem>("/api/v1/workforce/hr-cases", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  }

  async resolveHRCase(caseId: string, resolution: string): Promise<WorkforceHRCaseItem> {
    const res = await apiFetch<WorkforceHRCaseItem>(`/api/v1/workforce/hr-cases/${caseId}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "RESOLVED", resolution }),
    });
    return res.data;
  }

  // =========================================================================
  // 7. Workforce Reporting & Analytics
  // =========================================================================

  async getReportOverview(): Promise<WorkforceReportOverview> {
    const res = await apiFetch<WorkforceReportOverview>("/api/v1/workforce/reports/overview");
    return res.data;
  }
}

export const workforceService = new EnterpriseWorkforceService();
export default workforceService;

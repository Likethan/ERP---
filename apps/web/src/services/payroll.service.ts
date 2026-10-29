/**
 * CampusOS Enterprise Payroll, Compensation, Benefits & Statutory Compliance Service (Step 52)
 * "One Campus. One System. One Source of Truth."
 *
 * Interacts with FastAPI `/api/v1/payroll/*` endpoints.
 */

import { apiFetch } from "@/lib/api-client";
import type {
  EmployeeBankDetail,
  EmployeeCompensation,
  PayrollCalendar,
  PayrollJournalEntry,
  PayrollPaymentBatch,
  PayrollPeriod,
  PayrollRun,
  Payslip,
  SalaryComponent,
  SalaryGrade,
  SalaryStructure,
  StatutoryComplianceRule,
} from "@/types/payroll";

export const payrollService = {
  // 1. Salary Grades
  async listSalaryGrades(isActive?: boolean): Promise<SalaryGrade[]> {
    const params = new URLSearchParams();
    if (isActive !== undefined) params.append("is_active", String(isActive));
    const res = await apiFetch<SalaryGrade[]>(`/api/v1/payroll/salary-grades?${params.toString()}`);
    return res.data || [];
  },

  async createSalaryGrade(payload: {
    code: string;
    name: string;
    description?: string;
    min_base_pay: number;
    max_base_pay: number;
  }): Promise<SalaryGrade> {
    const res = await apiFetch<SalaryGrade>("/api/v1/payroll/salary-grades", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  // 2. Salary Components
  async listSalaryComponents(componentType?: string): Promise<SalaryComponent[]> {
    const params = new URLSearchParams();
    if (componentType) params.append("component_type", componentType);
    const res = await apiFetch<SalaryComponent[]>(`/api/v1/payroll/salary-components?${params.toString()}`);
    return res.data || [];
  },

  async createSalaryComponent(payload: {
    code: string;
    name: string;
    description?: string;
    component_type: string;
    calculation_method: string;
    default_value?: number;
    is_statutory?: boolean;
    taxability?: string;
  }): Promise<SalaryComponent> {
    const res = await apiFetch<SalaryComponent>("/api/v1/payroll/salary-components", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  // 3. Salary Structures
  async listSalaryStructures(): Promise<SalaryStructure[]> {
    const res = await apiFetch<SalaryStructure[]>("/api/v1/payroll/salary-structures");
    return res.data || [];
  },

  async createSalaryStructure(payload: {
    code: string;
    name: string;
    description?: string;
    currency?: string;
    pay_frequency?: string;
    items: Array<{
      component_id: string;
      calculation_method: string;
      factor_value?: number;
      fixed_amount?: number;
      sequence?: number;
    }>;
  }): Promise<SalaryStructure> {
    const res = await apiFetch<SalaryStructure>("/api/v1/payroll/salary-structures", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  // 4. Employee Compensation & Bank Details
  async listEmployeeCompensations(employeeId?: string): Promise<EmployeeCompensation[]> {
    const params = new URLSearchParams();
    if (employeeId) params.append("employee_id", employeeId);
    const res = await apiFetch<EmployeeCompensation[]>(`/api/v1/payroll/employee-compensations?${params.toString()}`);
    return res.data || [];
  },

  async assignEmployeeCompensation(payload: {
    employee_id: string;
    structure_id: string;
    salary_grade_id?: string;
    annual_ctc: number;
    monthly_gross: number;
    base_pay: number;
    effective_from: string;
    effective_to?: string;
    notes?: string;
  }): Promise<EmployeeCompensation> {
    const res = await apiFetch<EmployeeCompensation>("/api/v1/payroll/employee-compensations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async getEmployeeBankDetails(employeeId: string): Promise<EmployeeBankDetail> {
    const res = await apiFetch<EmployeeBankDetail>(`/api/v1/payroll/employees/${employeeId}/bank-details`);
    return res.data;
  },

  async setEmployeeBankDetails(
    employeeId: string,
    payload: {
      account_holder_name: string;
      bank_name: string;
      account_number: string;
      ifsc_code: string;
      branch_name: string;
    }
  ): Promise<EmployeeBankDetail> {
    const res = await apiFetch<EmployeeBankDetail>(`/api/v1/payroll/employees/${employeeId}/bank-details`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async verifyEmployeeBankDetails(employeeId: string): Promise<EmployeeBankDetail> {
    const res = await apiFetch<EmployeeBankDetail>(`/api/v1/payroll/employees/${employeeId}/bank-details/verify`, {
      method: "POST",
      body: JSON.stringify({ is_verified: true }),
    });
    return res.data;
  },

  // 5. Statutory Compliance Rules
  async listStatutoryRules(jurisdiction?: string): Promise<StatutoryComplianceRule[]> {
    const params = new URLSearchParams();
    if (jurisdiction) params.append("jurisdiction", jurisdiction);
    const res = await apiFetch<StatutoryComplianceRule[]>(`/api/v1/payroll/statutory-rules?${params.toString()}`);
    return res.data || [];
  },

  async createStatutoryRule(payload: {
    jurisdiction: string;
    rule_code: string;
    title: string;
    description?: string;
    employee_rate: number;
    employer_rate: number;
    wage_ceiling: number;
    effective_from: string;
    slab_configuration?: Array<Record<string, any>>;
  }): Promise<StatutoryComplianceRule> {
    const res = await apiFetch<StatutoryComplianceRule>("/api/v1/payroll/statutory-rules", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  // 6. Calendars & Periods
  async listPayrollCalendars(): Promise<PayrollCalendar[]> {
    const res = await apiFetch<PayrollCalendar[]>("/api/v1/payroll/calendars");
    return res.data || [];
  },

  async createPayrollCalendar(payload: {
    name: string;
    pay_frequency?: string;
    cutoff_day_of_month?: number;
    pay_day_of_month?: number;
  }): Promise<PayrollCalendar> {
    const res = await apiFetch<PayrollCalendar>("/api/v1/payroll/calendars", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async listPayrollPeriods(calendarId?: string): Promise<PayrollPeriod[]> {
    const params = new URLSearchParams();
    if (calendarId) params.append("calendar_id", calendarId);
    const res = await apiFetch<PayrollPeriod[]>(`/api/v1/payroll/periods?${params.toString()}`);
    return res.data || [];
  },

  async createPayrollPeriod(payload: {
    calendar_id: string;
    period_code: string;
    start_date: string;
    end_date: string;
    cutoff_date: string;
  }): Promise<PayrollPeriod> {
    const res = await apiFetch<PayrollPeriod>("/api/v1/payroll/periods", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  // 7. Payroll Runs
  async listPayrollRuns(params?: { period_id?: string; calendar_id?: string; status?: string }): Promise<PayrollRun[]> {
    const q = new URLSearchParams();
    if (params?.period_id) q.set("period_id", params.period_id);
    if (params?.calendar_id) q.set("calendar_id", params.calendar_id);
    if (params?.status) q.set("status", params.status);
    const qs = q.toString() ? `?${q.toString()}` : "";
    const res = await apiFetch<PayrollRun[]>(`/api/v1/payroll/runs${qs}`);
    return res.data || [];
  },

  async createPayrollRun(payload: {
    period_id: string;
    calendar_id: string;
    run_number?: string;
    department_id?: string;
    campus_id?: string;
    notes?: string;
  }): Promise<PayrollRun> {
    const res = await apiFetch<PayrollRun>("/api/v1/payroll/runs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async getPayrollRun(runId: string): Promise<PayrollRun> {
    const res = await apiFetch<PayrollRun>(`/api/v1/payroll/runs/${runId}`);
    return res.data;
  },

  async calculatePayrollRun(runId: string, payload?: { force_recalculate?: boolean }): Promise<PayrollRun> {
    const res = await apiFetch<PayrollRun>(`/api/v1/payroll/runs/${runId}/calculate`, {
      method: "POST",
      body: JSON.stringify(payload || {}),
    });
    return res.data;
  },

  async approvePayrollRun(runId: string, notes?: string): Promise<PayrollRun> {
    const params = new URLSearchParams();
    if (notes) params.append("notes", notes);
    const res = await apiFetch<PayrollRun>(`/api/v1/payroll/runs/${runId}/approve?${params.toString()}`, {
      method: "POST",
    });
    return res.data;
  },

  async cancelPayrollRun(runId: string, reason: string): Promise<PayrollRun> {
    const res = await apiFetch<PayrollRun>(`/api/v1/payroll/runs/${runId}/cancel`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
    return res.data;
  },

  async postPayrollRun(runId: string): Promise<PayrollJournalEntry> {
    const res = await apiFetch<PayrollJournalEntry>(`/api/v1/payroll/runs/${runId}/post`, {
      method: "POST",
    });
    return res.data;
  },

  async postPayrollToAccounting(runId: string): Promise<PayrollJournalEntry> {
    return this.postPayrollRun(runId);
  },

  async getPayrollJournal(runId: string): Promise<PayrollJournalEntry> {
    const res = await apiFetch<PayrollJournalEntry>(`/api/v1/payroll/runs/${runId}/journal`);
    return res.data;
  },

  // 8. Payment Batches
  async listPaymentBatches(): Promise<PayrollPaymentBatch[]> {
    const res = await apiFetch<PayrollPaymentBatch[]>("/api/v1/payroll/payment-batches");
    return res.data || [];
  },

  async createPaymentBatch(payload: {
    payroll_run_id: string;
    payment_method?: string;
    export_format?: string;
  }): Promise<PayrollPaymentBatch> {
    const res = await apiFetch<PayrollPaymentBatch>("/api/v1/payroll/payment-batches", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  async getPaymentBatch(batchId: string): Promise<PayrollPaymentBatch> {
    const res = await apiFetch<PayrollPaymentBatch>(`/api/v1/payroll/payment-batches/${batchId}`);
    return res.data;
  },

  async reconcilePaymentBatch(
    batchId: string,
    payload: {
      reconciled_items: Array<{
        payment_item_id: string;
        status: string;
        transaction_reference?: string;
      }>;
    }
  ): Promise<PayrollPaymentBatch> {
    const res = await apiFetch<PayrollPaymentBatch>(`/api/v1/payroll/payment-batches/${batchId}/reconcile`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },

  // 9. Payslips & Employee Self-Service
  async getMyPayslips(): Promise<Payslip[]> {
    const res = await apiFetch<Payslip[]>("/api/v1/payroll/payslips/my-payslips");
    return res.data || [];
  },

  async getEmployeePayslips(employeeId: string): Promise<Payslip[]> {
    const res = await apiFetch<Payslip[]>(`/api/v1/payroll/employees/${employeeId}/payslips`);
    return res.data || [];
  },

  async getPayslipByToken(token: string): Promise<Payslip> {
    const res = await apiFetch<Payslip>(`/api/v1/payroll/payslips/token/${token}`);
    return res.data;
  },

  async submitPayslipDiscrepancy(payload: {
    subject: string;
    description: string;
  }): Promise<{ status: string; case_number: string; message: string }> {
    const res = await apiFetch<{ status: string; case_number: string; message: string }>("/api/v1/payroll/payslips/dispute", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return res.data;
  },
};

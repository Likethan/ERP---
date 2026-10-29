/**
 * TypeScript definitions for Enterprise Payroll, Compensation, Benefits & Statutory Compliance (Step 52).
 * CampusOS Tagline: "One Campus. One System. One Source of Truth."
 */

export interface SalaryGrade {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  min_base_pay: number;
  max_base_pay: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SalaryComponent {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  component_type: "EARNING" | "DEDUCTION" | "EMPLOYER_CONTRIBUTION";
  calculation_method: "FLAT_AMOUNT" | "PERCENTAGE_OF_BASIC" | "PERCENTAGE_OF_GROSS" | "FORMULA";
  default_value: number;
  is_statutory: boolean;
  taxability: "TAXABLE" | "EXEMPT" | "PARTIALLY_EXEMPT";
  is_recurring: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SalaryStructureItem {
  id: string;
  structure_id: string;
  component_id: string;
  component_name?: string;
  component_type?: string;
  calculation_method: string;
  factor_value: number;
  fixed_amount: number;
  sequence: number;
}

export interface SalaryStructure {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  currency: string;
  pay_frequency: string;
  version: number;
  is_active: boolean;
  items: SalaryStructureItem[];
  created_at: string;
  updated_at: string;
}

export interface EmployeeCompensation {
  id: string;
  tenant_id: string;
  employee_id: string;
  structure_id: string;
  salary_grade_id?: string;
  annual_ctc: number;
  monthly_gross: number;
  base_pay: number;
  effective_from: string;
  effective_to?: string;
  currency: string;
  custom_components: Record<string, any>;
  notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmployeeBankDetail {
  id: string;
  tenant_id: string;
  employee_id: string;
  account_holder_name: string;
  bank_name: string;
  account_number_masked: string;
  ifsc_code: string;
  branch_name: string;
  is_primary: boolean;
  is_verified: boolean;
  verified_by_user_id?: string;
  verified_at?: string;
  created_at: string;
  updated_at: string;
}

export interface StatutoryComplianceRule {
  id: string;
  tenant_id: string;
  jurisdiction: string;
  rule_code: string;
  title: string;
  description?: string;
  employee_rate: number;
  employer_rate: number;
  wage_ceiling: number;
  effective_from: string;
  effective_to?: string;
  slab_configuration: Record<string, any>[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PayrollCalendar {
  id: string;
  tenant_id: string;
  name: string;
  pay_frequency: string;
  cutoff_day_of_month: number;
  pay_day_of_month: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PayrollPeriod {
  id: string;
  tenant_id: string;
  calendar_id: string;
  period_code: string;
  start_date: string;
  end_date: string;
  cutoff_date: string;
  is_closed: boolean;
  created_at: string;
  updated_at: string;
}

export interface PayrollRunItemDetail {
  id: string;
  component_id: string;
  component_name: string;
  component_type: string;
  amount: number;
  calculation_notes?: string;
}

export interface PayrollRunItem {
  id: string;
  tenant_id: string;
  payroll_run_id: string;
  employee_id: string;
  compensation_id: string;
  days_in_period: number;
  worked_days: number;
  paid_leave_days: number;
  unpaid_leave_days: number;
  proration_factor: number;
  gross_earnings: number;
  total_deductions: number;
  employer_contributions: number;
  net_pay: number;
  calculation_breakdown: Record<string, any>;
  details: PayrollRunItemDetail[];
  created_at: string;
}

export interface PayrollRun {
  id: string;
  tenant_id: string;
  period_id: string;
  calendar_id: string;
  run_number: string;
  status: "DRAFT" | "CALCULATING" | "CALCULATED" | "VALIDATION_FAILED" | "PENDING_APPROVAL" | "APPROVED" | "POSTED" | "PAID" | "CANCELLED";
  is_locked: boolean;
  department_id?: string;
  campus_id?: string;
  total_gross_pay: number;
  total_deductions: number;
  total_employer_contributions: number;
  total_net_pay: number;
  employee_count: number;
  approved_by_user_id?: string;
  approved_at?: string;
  posted_by_user_id?: string;
  posted_at?: string;
  rejection_reason?: string;
  items?: PayrollRunItem[];
  created_at: string;
  updated_at: string;
}

export interface PayrollJournalLine {
  id: string;
  account_code: string;
  account_name: string;
  line_type: "DEBIT" | "CREDIT";
  amount: number;
  department_id?: string;
  description?: string;
}

export interface PayrollJournalEntry {
  id: string;
  tenant_id: string;
  payroll_run_id: string;
  entry_number: string;
  entry_date: string;
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
  posted_by_user_id: string;
  posted_at: string;
  lines: PayrollJournalLine[];
  created_at: string;
}

export interface PayrollPaymentItem {
  id: string;
  batch_id: string;
  employee_id: string;
  run_item_id: string;
  amount: number;
  bank_name: string;
  account_number_masked: string;
  ifsc_code: string;
  status: string;
  transaction_reference?: string;
  reconciled_at?: string;
}

export interface PayrollPaymentBatch {
  id: string;
  tenant_id: string;
  payroll_run_id: string;
  batch_number: string;
  payment_method: string;
  status: "PREPARED" | "APPROVED" | "EXPORTED" | "PARTIALLY_RECONCILED" | "RECONCILED" | "FAILED";
  total_amount: number;
  total_records: number;
  disbursed_at?: string;
  exported_at?: string;
  export_format: string;
  items: PayrollPaymentItem[];
  created_at: string;
  updated_at: string;
}

export interface Payslip {
  id: string;
  tenant_id: string;
  payroll_run_id: string;
  run_item_id: string;
  employee_id: string;
  payslip_number: string;
  period_code: string;
  gross_pay: number;
  total_deductions: number;
  net_pay: number;
  secure_token: string;
  storage_key?: string;
  is_published: boolean;
  created_at: string;
}

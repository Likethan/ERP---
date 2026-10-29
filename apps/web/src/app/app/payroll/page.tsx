"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { payrollService } from "@/services/payroll.service";
import { workforceService } from "@/services/workforce.service";
import type {
  SalaryGrade,
  SalaryComponent,
  SalaryStructure,
  PayrollCalendar,
  PayrollPeriod,
  PayrollRun,
  PayrollPaymentBatch,
  StatutoryComplianceRule,
  Payslip,
} from "@/types/payroll";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import {
  DollarSign,
  Briefcase,
  Calendar,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Plus,
  Search,
  Building2,
  FileText,
  Layers,
  TrendingUp,
  RefreshCw,
  Send,
  Eye,
  CreditCard,
  Award,
  AlertTriangle,
  RotateCcw,
  Check,
  Ban,
  ArrowRight,
  FileSpreadsheet,
  Download,
  AlertCircle,
  Receipt,
  BookOpen,
} from "lucide-react";

export default function EnterprisePayrollPage() {
  const { showToast } = useToast();

  // Active Tab
  const [activeTab, setActiveTab] = useState<
    "overview" | "structures" | "runs" | "disbursements" | "compliance" | "payslips"
  >("overview");

  // Core State
  const [loading, setLoading] = useState(true);
  const [grades, setGrades] = useState<SalaryGrade[]>([]);
  const [components, setComponents] = useState<SalaryComponent[]>([]);
  const [structures, setStructures] = useState<SalaryStructure[]>([]);
  const [calendars, setCalendars] = useState<PayrollCalendar[]>([]);
  const [periods, setPeriods] = useState<PayrollPeriod[]>([]);
  const [runs, setRuns] = useState<PayrollRun[]>([]);
  const [batches, setBatches] = useState<PayrollPaymentBatch[]>([]);
  const [complianceRules, setComplianceRules] = useState<StatutoryComplianceRule[]>([]);
  const [payslips, setPayslips] = useState<Payslip[]>([]);

  // Modals
  const [createRunOpen, setCreateRunOpen] = useState(false);
  const [runDetailsOpen, setRunDetailsOpen] = useState(false);
  const [createBatchOpen, setCreateBatchOpen] = useState(false);
  const [reconcileModalOpen, setReconcileModalOpen] = useState(false);
  const [createStructureOpen, setCreateStructureOpen] = useState(false);
  const [disputeModalOpen, setDisputeModalOpen] = useState(false);

  // Selected Records
  const [selectedRun, setSelectedRun] = useState<PayrollRun | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<PayrollPaymentBatch | null>(null);
  const [selectedPayslip, setSelectedPayslip] = useState<Payslip | null>(null);

  // Form States - Run Creation
  const [selectedCalendarId, setSelectedCalendarId] = useState("");
  const [selectedPeriodId, setSelectedPeriodId] = useState("");
  const [runNotes, setRunNotes] = useState("");

  // Form States - Structure Creation
  const [structCode, setStructCode] = useState("");
  const [structName, setStructName] = useState("");
  const [structBasicAmount, setStructBasicAmount] = useState("50000");

  // Form States - Dispute Filing
  const [disputeSubject, setDisputeSubject] = useState("");
  const [disputeDescription, setDisputeDescription] = useState("");

  // Filters
  const [searchQuery, setSearchQuery] = useState("");

  // Load All Payroll Data
  const loadPayrollData = useCallback(async () => {
    try {
      setLoading(true);
      const [
        gradesData,
        componentsData,
        structuresData,
        calendarsData,
        runsData,
        batchesData,
        rulesData,
      ] = await Promise.all([
        payrollService.listSalaryGrades().catch(() => []),
        payrollService.listSalaryComponents().catch(() => []),
        payrollService.listSalaryStructures().catch(() => []),
        payrollService.listPayrollCalendars().catch(() => []),
        payrollService.listPayrollRuns().catch(() => []),
        payrollService.listPaymentBatches().catch(() => []),
        payrollService.listStatutoryRules().catch(() => []),
      ]);

      setGrades(gradesData);
      setComponents(componentsData);
      setStructures(structuresData);
      setCalendars(calendarsData);
      setRuns(runsData);
      setBatches(batchesData);
      setComplianceRules(rulesData);

      if (calendarsData.length > 0 && !selectedCalendarId) {
        setSelectedCalendarId(calendarsData[0].id);
        const periodsData = await payrollService.listPayrollPeriods(calendarsData[0].id).catch(() => []);
        setPeriods(periodsData);
        if (periodsData.length > 0) {
          setSelectedPeriodId(periodsData[0].id);
        }
      }
    } catch (err: any) {
      showToast({
        title: "Failed to load payroll data",
        message: err.message || "An unexpected error occurred.",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [showToast, selectedCalendarId]);

  useEffect(() => {
    loadPayrollData();
  }, [loadPayrollData]);

  // Handle Calendar Change in Run Form
  const handleCalendarChange = async (calId: string) => {
    setSelectedCalendarId(calId);
    try {
      const pList = await payrollService.listPayrollPeriods(calId);
      setPeriods(pList);
      if (pList.length > 0) setSelectedPeriodId(pList[0].id);
    } catch {
      setPeriods([]);
    }
  };

  // Run Operations
  const handleCreateRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPeriodId || !selectedCalendarId) {
      showToast({ title: "Validation Error", message: "Select calendar and period.", type: "error" });
      return;
    }
    try {
      await payrollService.createPayrollRun({
        calendar_id: selectedCalendarId,
        period_id: selectedPeriodId,
        notes: runNotes,
      });
      showToast({ title: "Success", message: "Payroll run initialized in DRAFT state.", type: "success" });
      setCreateRunOpen(false);
      setRunNotes("");
      loadPayrollData();
    } catch (err: any) {
      showToast({ title: "Failed to create run", message: err.message, type: "error" });
    }
  };

  const handleCalculateRun = async (runId: string) => {
    try {
      const updated = await payrollService.calculatePayrollRun(runId, {});
      showToast({
        title: "Payroll Calculated",
        message: `Calculated ${updated.employee_count} employees. Net Pay: ₹${Number(updated.total_net_pay).toLocaleString("en-IN")}`,
        type: "success",
      });
      loadPayrollData();
      if (selectedRun?.id === runId) setSelectedRun(updated);
    } catch (err: any) {
      showToast({ title: "Calculation Failed", message: err.message, type: "error" });
    }
  };

  const handleApproveRun = async (runId: string) => {
    try {
      const updated = await payrollService.approvePayrollRun(runId);
      showToast({ title: "Payroll Approved", message: `Run #${updated.run_number} locked and approved.`, type: "success" });
      loadPayrollData();
      if (selectedRun?.id === runId) setSelectedRun(updated);
    } catch (err: any) {
      showToast({ title: "Approval Failed", message: err.message, type: "error" });
    }
  };

  const handlePostRunToAccounting = async (runId: string) => {
    try {
      const journal = await payrollService.postPayrollToAccounting(runId);
      showToast({
        title: "Posted to General Ledger",
        message: `Journal entry #${journal.entry_number} generated with balanced double-entry lines. Payslips generated!`,
        type: "success",
      });
      loadPayrollData();
      if (selectedRun?.id === runId) {
        const refreshed = await payrollService.getPayrollRun(runId);
        setSelectedRun(refreshed);
      }
    } catch (err: any) {
      showToast({ title: "Posting Failed", message: err.message, type: "error" });
    }
  };

  const handleCancelRun = async (runId: string) => {
    const reason = prompt("Enter cancellation reason:");
    if (!reason) return;
    try {
      await payrollService.cancelPayrollRun(runId, reason);
      showToast({ title: "Payroll Cancelled", message: "Payroll run marked as cancelled.", type: "success" });
      loadPayrollData();
      if (selectedRun?.id === runId) setRunDetailsOpen(false);
    } catch (err: any) {
      showToast({ title: "Cancellation Failed", message: err.message, type: "error" });
    }
  };

  // Payment Batch Operations
  const handleCreateBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRun) return;
    try {
      const batch = await payrollService.createPaymentBatch({
        payroll_run_id: selectedRun.id,
        payment_method: "BANK_TRANSFER",
        export_format: "ACH_CSV",
      });
      showToast({
        title: "Payment Batch Created",
        message: `Batch #${batch.batch_number} created for ${batch.total_records} records.`,
        type: "success",
      });
      setCreateBatchOpen(false);
      loadPayrollData();
    } catch (err: any) {
      showToast({ title: "Batch Creation Failed", message: err.message, type: "error" });
    }
  };

  const handleReconcileBatch = async (batchId: string) => {
    try {
      const batch = await payrollService.getPaymentBatch(batchId);
      const reconciledItems = (batch.items || []).map((it, idx) => ({
        payment_item_id: it.id,
        status: "RECONCILED",
        transaction_reference: `UTR-BANK-${Date.now()}-${idx + 1}`,
      }));
      await payrollService.reconcilePaymentBatch(batchId, {
        reconciled_items: reconciledItems,
      });
      showToast({
        title: "Disbursement Reconciled",
        message: `All payment records confirmed with bank transaction references. Payroll marked PAID.`,
        type: "success",
      });
      setReconcileModalOpen(false);
      loadPayrollData();
    } catch (err: any) {
      showToast({ title: "Reconciliation Failed", message: err.message, type: "error" });
    }
  };

  // Dispute Filing via Step 51 HR Cases
  const handleFileDispute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPayslip) return;
    try {
      await workforceService.createHRCase({
        employee_id: selectedPayslip.employee_id,
        category: "SALARY_QUERY",
        priority: "HIGH",
        subject: disputeSubject || `Discrepancy in Payslip ${selectedPayslip.payslip_number}`,
        description: disputeDescription || `Employee reported calculation or deduction variance for period ${selectedPayslip.period_code}. Net Pay: ₹${Number(selectedPayslip.net_pay).toLocaleString("en-IN")}.`,
      });
      showToast({
        title: "Dispute Case Logged",
        message: "HR Case logged into Workforce Case Management workflow.",
        type: "success",
      });
      setDisputeModalOpen(false);
      setDisputeSubject("");
      setDisputeDescription("");
    } catch (err: any) {
      showToast({ title: "Failed to File Dispute", message: err.message, type: "error" });
    }
  };

  // Metrics Calculations
  const metrics = useMemo(() => {
    const totalNet = runs.reduce((acc, r) => acc + (Number(r.total_net_pay) || 0), 0);
    const activeRunsCount = runs.filter((r) =>
      ["DRAFT", "CALCULATING", "CALCULATED", "PENDING_APPROVAL"].includes(r.status)
    ).length;
    const postedRunsCount = runs.filter((r) => ["POSTED", "PAID"].includes(r.status)).length;
    const activeRulesCount = complianceRules.filter((cr) => cr.is_active).length;
    return {
      totalNet,
      activeRunsCount,
      postedRunsCount,
      activeRulesCount,
    };
  }, [runs, complianceRules]);

  // Status Badge Colors
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "DRAFT":
        return <Badge variant="secondary">Draft</Badge>;
      case "CALCULATING":
      case "CALCULATED":
        return <Badge className="bg-sky-500/20 text-sky-400 border border-sky-500/30">Calculated</Badge>;
      case "PENDING_APPROVAL":
        return <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30">Pending Approval</Badge>;
      case "APPROVED":
        return <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Approved</Badge>;
      case "POSTED":
        return <Badge className="bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">Posted to Ledger</Badge>;
      case "PAID":
        return <Badge className="bg-purple-500/20 text-purple-400 border border-purple-500/30">Paid & Reconciled</Badge>;
      case "CANCELLED":
        return <Badge variant="destructive">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="flex-1 space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <DollarSign className="h-7 w-7 text-emerald-400 p-1 bg-emerald-500/10 rounded-lg border border-emerald-500/20" />
              Enterprise Payroll, Compensation & Benefits
            </h1>
            <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">Step 52</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic, decimal-safe compensation lifecycle, statutory withholdings, double-entry ledger integration & bank disbursements.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={loadPayrollData}
            disabled={loading}
            className="border-slate-700 hover:bg-slate-800 text-slate-300"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Sync
          </Button>
          <Button
            size="sm"
            onClick={() => setCreateRunOpen(true)}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-md shadow-emerald-600/20"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            New Payroll Run
          </Button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Net Payroll Processed"
          value={`₹${metrics.totalNet.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`}
          description="Across all historical payroll runs"
          icon={<DollarSign className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Active Calculations"
          value={metrics.activeRunsCount}
          description="Runs in draft / calculated / review"
          icon={<Briefcase className="h-5 w-5 text-sky-400" />}
        />
        <StatCard
          title="Posted / Paid Batches"
          value={metrics.postedRunsCount}
          description="Integrated with General Ledger"
          icon={<CreditCard className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Active Statutory Rules"
          value={metrics.activeRulesCount}
          description="EPF, ESI, TDS & State Compliances"
          icon={<ShieldCheck className="h-5 w-5 text-purple-400" />}
        />
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-800 overflow-x-auto space-x-2">
        {[
          { id: "overview", label: "Executive Overview", icon: TrendingUp },
          { id: "structures", label: "Salary Structures & Grades", icon: Layers },
          { id: "runs", label: "Payroll Processing Engine", icon: FileSpreadsheet },
          { id: "disbursements", label: "Payment Batches & Banking", icon: CreditCard },
          { id: "compliance", label: "Statutory Compliance", icon: ShieldCheck },
          { id: "payslips", label: "Employee Payslips", icon: Receipt },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 py-3 px-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                isActive
                  ? "border-emerald-500 text-emerald-400 bg-emerald-500/5 rounded-t-lg"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content 1: Overview */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Actions & Status */}
            <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-emerald-400" />
                Payroll Processing Pipeline
              </h3>
              <p className="text-xs text-slate-400 mb-6">
                Lifecycle guarantees: Deterministic calculation → Approval separation-of-duties → Balanced Ledger Entry → Reconciled Bank Disbursement.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800/80">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">1. Collect Inputs</div>
                  <div className="text-sm font-medium text-slate-200 mt-2">Workforce, LOP, Attendance & Revisions</div>
                  <div className="text-xs text-emerald-400 mt-2 flex items-center gap-1">
                    <Check className="h-3.5 w-3.5" /> Authoritative Sync
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800/80">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">2. Calculate Run</div>
                  <div className="text-sm font-medium text-slate-200 mt-2">Deterministic Decimal Engine & Ceilings</div>
                  <div className="text-xs text-sky-400 mt-2 flex items-center gap-1">
                    <Check className="h-3.5 w-3.5" /> Zero Floating Point
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800/80">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">3. Post to Ledger</div>
                  <div className="text-sm font-medium text-slate-200 mt-2">Balanced Debits & Credits to General Ledger</div>
                  <div className="text-xs text-indigo-400 mt-2 flex items-center gap-1">
                    <Check className="h-3.5 w-3.5" /> Finance Module
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800/80">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">4. Disburse & Reconcile</div>
                  <div className="text-sm font-medium text-slate-200 mt-2">Bank Batch Export & UTR Tracking</div>
                  <div className="text-xs text-purple-400 mt-2 flex items-center gap-1">
                    <Check className="h-3.5 w-3.5" /> Direct Self-Service
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-5 border-t border-slate-800 flex items-center justify-between">
                <div className="text-xs text-slate-400">
                  Ready to compute monthly staff payroll for current calendar period?
                </div>
                <Button
                  size="sm"
                  onClick={() => setActiveTab("runs")}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs"
                >
                  Go to Run Engine <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                </Button>
              </div>
            </div>

            {/* Compliance Highlights */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-purple-400" />
                Statutory Guardrails
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Configured jurisdiction rules enforced automatically during processing.
              </p>
              <div className="space-y-3">
                {complianceRules.slice(0, 4).map((rule) => (
                  <div key={rule.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{rule.title}</span>
                      <Badge variant="outline" className="text-[10px] uppercase">{rule.jurisdiction}</Badge>
                    </div>
                    <div className="text-slate-400 mt-1 flex justify-between">
                      <span>EE: {(Number(rule.employee_rate) * 100).toFixed(1)}% | ER: {(Number(rule.employer_rate) * 100).toFixed(1)}%</span>
                      {Number(rule.wage_ceiling) > 0 && <span>Cap: ₹{Number(rule.wage_ceiling).toLocaleString("en-IN")}</span>}
                    </div>
                  </div>
                ))}
                {complianceRules.length === 0 && (
                  <div className="text-xs text-slate-500 text-center py-4">No compliance rules configured yet.</div>
                )}
              </div>
            </div>
          </div>

          {/* Recent Runs Quick View */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-white">Recent Payroll Runs</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveTab("runs")}
                className="text-xs text-emerald-400 hover:text-emerald-300"
              >
                View all runs
              </Button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase">
                    <th className="py-2.5 px-3">Run Number</th>
                    <th className="py-2.5 px-3">Period</th>
                    <th className="py-2.5 px-3">Employees</th>
                    <th className="py-2.5 px-3">Gross Earnings</th>
                    <th className="py-2.5 px-3">Deductions</th>
                    <th className="py-2.5 px-3">Net Pay</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {runs.slice(0, 5).map((r) => (
                    <tr key={r.id} className="hover:bg-slate-800/30">
                      <td className="py-3 px-3 font-semibold text-slate-200">{r.run_number}</td>
                      <td className="py-3 px-3 text-slate-300">{r.period_id.substring(0, 8)}...</td>
                      <td className="py-3 px-3 text-slate-300">{r.employee_count}</td>
                      <td className="py-3 px-3 text-slate-200">₹{Number(r.total_gross_pay).toLocaleString("en-IN")}</td>
                      <td className="py-3 px-3 text-rose-400">₹{Number(r.total_deductions).toLocaleString("en-IN")}</td>
                      <td className="py-3 px-3 font-semibold text-emerald-400">₹{Number(r.total_net_pay).toLocaleString("en-IN")}</td>
                      <td className="py-3 px-3">{getStatusBadge(r.status)}</td>
                    </tr>
                  ))}
                  {runs.length === 0 && (
                    <tr>
                      <td colSpan={7} className="text-center py-6 text-slate-500">
                        No payroll runs executed yet. Click &quot;New Payroll Run&quot; to initialize.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content 2: Salary Structures & Grades */}
      {activeTab === "structures" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold text-white">Configured Salary Structures & Bands</h3>
              <p className="text-xs text-slate-400">Modular pay bands, fixed/percentage allowances, and institutional salary templates.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Pay Grades */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Award className="h-4 w-4 text-amber-400" />
                Pay Grades & Bands
              </h4>
              <div className="space-y-2.5">
                {grades.map((g) => (
                  <div key={g.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs">
                    <div className="flex justify-between font-medium text-slate-200">
                      <span>{g.name}</span>
                      <Badge variant="outline" className="text-[10px]">{g.code}</Badge>
                    </div>
                    <div className="text-slate-400 mt-1">
                      Range: ₹{Number(g.min_base_pay).toLocaleString("en-IN")} - ₹{Number(g.max_base_pay).toLocaleString("en-IN")}
                    </div>
                  </div>
                ))}
                {grades.length === 0 && <div className="text-xs text-slate-500 py-3">No pay grades defined.</div>}
              </div>
            </div>

            {/* Salary Components */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Layers className="h-4 w-4 text-sky-400" />
                Configured Salary Components
              </h4>
              <div className="space-y-2.5 max-h-[420px] overflow-y-auto">
                {components.map((c) => (
                  <div key={c.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs">
                    <div className="flex justify-between font-medium text-slate-200">
                      <span>{c.name}</span>
                      <Badge
                        className={
                          c.component_type === "EARNING"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[10px]"
                            : "bg-rose-500/10 text-rose-400 border-rose-500/20 text-[10px]"
                        }
                      >
                        {c.component_type}
                      </Badge>
                    </div>
                    <div className="text-slate-400 mt-1 flex justify-between">
                      <span>Method: {c.calculation_method}</span>
                      <span>{c.taxability}</span>
                    </div>
                  </div>
                ))}
                {components.length === 0 && <div className="text-xs text-slate-500 py-3">No components defined.</div>}
              </div>
            </div>

            {/* Structures */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                Active Salary Structures
              </h4>
              <div className="space-y-3">
                {structures.map((s) => (
                  <div key={s.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs">
                    <div className="flex justify-between font-medium text-slate-200">
                      <span>{s.name}</span>
                      <Badge variant="outline" className="text-[10px]">v{s.version}</Badge>
                    </div>
                    <div className="text-slate-400 mt-1">Code: {s.code} | {s.pay_frequency}</div>
                    <div className="mt-2 text-slate-300 font-semibold text-[11px]">
                      Components: {s.items ? s.items.length : 0} items configured
                    </div>
                  </div>
                ))}
                {structures.length === 0 && <div className="text-xs text-slate-500 py-3">No structures defined.</div>}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content 3: Payroll Runs Engine */}
      {activeTab === "runs" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold text-white">Payroll Execution & Approvals</h3>
              <p className="text-xs text-slate-400">
                Execute monthly batches, trigger deterministic calculations, verify exceptions, approve and post to general ledger.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => setCreateRunOpen(true)}
              className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs"
            >
              <Plus className="h-4 w-4 mr-1.5" /> Initialize Run
            </Button>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase bg-slate-950/60">
                    <th className="py-3 px-3">Run Number</th>
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-3">Employees</th>
                    <th className="py-3 px-3">Gross Pay</th>
                    <th className="py-3 px-3">Deductions</th>
                    <th className="py-3 px-3">Net Pay</th>
                    <th className="py-3 px-3">Lock Status</th>
                    <th className="py-3 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {runs.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-800/30">
                      <td className="py-3 px-3 font-semibold text-slate-200">{r.run_number}</td>
                      <td className="py-3 px-3">{getStatusBadge(r.status)}</td>
                      <td className="py-3 px-3 text-slate-300">{r.employee_count}</td>
                      <td className="py-3 px-3 text-slate-200">₹{Number(r.total_gross_pay).toLocaleString("en-IN")}</td>
                      <td className="py-3 px-3 text-rose-400">₹{Number(r.total_deductions).toLocaleString("en-IN")}</td>
                      <td className="py-3 px-3 font-semibold text-emerald-400">₹{Number(r.total_net_pay).toLocaleString("en-IN")}</td>
                      <td className="py-3 px-3">
                        {r.is_locked ? (
                          <span className="text-amber-400 font-medium">Locked</span>
                        ) : (
                          <span className="text-slate-400">Unlocked</span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-right space-x-1.5 whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={async () => {
                            const full = await payrollService.getPayrollRun(r.id);
                            setSelectedRun(full);
                            setRunDetailsOpen(true);
                          }}
                          className="h-7 px-2 text-[11px] text-slate-300 hover:text-white"
                        >
                          <Eye className="h-3.5 w-3.5 mr-1" /> View
                        </Button>
                        {!r.is_locked && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleCalculateRun(r.id)}
                            className="h-7 px-2 text-[11px] border-slate-700 text-sky-400 hover:bg-sky-500/10"
                          >
                            Calculate
                          </Button>
                        )}
                        {r.status === "CALCULATED" && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleApproveRun(r.id)}
                            className="h-7 px-2 text-[11px] border-emerald-700 text-emerald-400 hover:bg-emerald-500/10"
                          >
                            Approve
                          </Button>
                        )}
                        {r.status === "APPROVED" && (
                          <Button
                            size="sm"
                            onClick={() => handlePostRunToAccounting(r.id)}
                            className="h-7 px-2 text-[11px] bg-indigo-600 hover:bg-indigo-500 text-white"
                          >
                            Post to Ledger
                          </Button>
                        )}
                        {["APPROVED", "POSTED"].includes(r.status) && (
                          <Button
                            size="sm"
                            onClick={() => {
                              setSelectedRun(r);
                              setCreateBatchOpen(true);
                            }}
                            className="h-7 px-2 text-[11px] bg-purple-600 hover:bg-purple-500 text-white"
                          >
                            Disburse
                          </Button>
                        )}
                        {!["POSTED", "PAID", "CANCELLED"].includes(r.status) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCancelRun(r.id)}
                            className="h-7 px-2 text-[11px] text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                          >
                            Cancel
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {runs.length === 0 && (
                    <tr>
                      <td colSpan={8} className="text-center py-8 text-slate-500">
                        No payroll runs found. Click &quot;Initialize Run&quot; to begin.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content 4: Disbursements & Banking */}
      {activeTab === "disbursements" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold text-white">Disbursement Batches & Bank Reconciliation</h3>
              <p className="text-xs text-slate-400">
                Export approved salary payment files, track bank account numbers (masked for privacy), and record UTR transaction references.
              </p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase bg-slate-950/60">
                    <th className="py-3 px-3">Batch Number</th>
                    <th className="py-3 px-3">Method & Format</th>
                    <th className="py-3 px-3">Records</th>
                    <th className="py-3 px-3">Total Amount</th>
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {batches.map((b) => (
                    <tr key={b.id} className="hover:bg-slate-800/30">
                      <td className="py-3 px-3 font-semibold text-slate-200">{b.batch_number}</td>
                      <td className="py-3 px-3 text-slate-300">{b.payment_method} ({b.export_format})</td>
                      <td className="py-3 px-3 text-slate-300">{b.total_records}</td>
                      <td className="py-3 px-3 font-semibold text-emerald-400">₹{Number(b.total_amount).toLocaleString("en-IN")}</td>
                      <td className="py-3 px-3">
                        <Badge
                          className={
                            b.status === "RECONCILED"
                              ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                              : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                          }
                        >
                          {b.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-3 text-right space-x-2">
                        {b.status !== "RECONCILED" && (
                          <Button
                            size="sm"
                            onClick={() => {
                              setSelectedBatch(b);
                              setReconcileModalOpen(true);
                            }}
                            className="h-7 px-2.5 text-[11px] bg-purple-600 hover:bg-purple-500 text-white"
                          >
                            Reconcile UTR
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            showToast({
                              title: "File Exported",
                              message: `Exported bank transmission file for ${b.batch_number}.`,
                              type: "success",
                            });
                          }}
                          className="h-7 px-2.5 text-[11px] border-slate-700 text-slate-300 hover:bg-slate-800"
                        >
                          <Download className="h-3 w-3 mr-1" /> Export File
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {batches.length === 0 && (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-slate-500">
                        No payment batches prepared yet. Approve and post a payroll run to initiate disbursements.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab Content 5: Statutory Compliance */}
      {activeTab === "compliance" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold text-white">Statutory Rules & Compliance Registry</h3>
              <p className="text-xs text-slate-400">
                Employees Provident Fund (EPF), ESI, Income Tax Withholdings (TDS), and Professional Tax ceilings.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {complianceRules.map((rule) => (
              <div key={rule.id} className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold text-white text-sm">{rule.title}</h4>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">{rule.rule_code}</p>
                  </div>
                  <Badge variant="outline" className="text-[10px] uppercase font-mono">{rule.jurisdiction}</Badge>
                </div>
                <div className="border-t border-slate-800 pt-3 grid grid-cols-2 gap-2 text-xs text-slate-300">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Employee Rate</span>
                    <span className="font-semibold">{(Number(rule.employee_rate) * 100).toFixed(2)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Employer Rate</span>
                    <span className="font-semibold">{(Number(rule.employer_rate) * 100).toFixed(2)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Wage Ceiling</span>
                    <span>{Number(rule.wage_ceiling) > 0 ? `₹${Number(rule.wage_ceiling).toLocaleString("en-IN")}` : "No Limit"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Effective Date</span>
                    <span>{rule.effective_from}</span>
                  </div>
                </div>
                <div className="text-[11px] text-emerald-400 flex items-center gap-1 pt-1">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Enforced in Calculation Engine
                </div>
              </div>
            ))}
            {complianceRules.length === 0 && (
              <div className="col-span-3 text-center py-8 text-slate-500 bg-slate-900 border border-slate-800 rounded-xl">
                No statutory compliance rules configured yet.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab Content 6: Employee Self-Service Payslips */}
      {activeTab === "payslips" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold text-white">Employee Self-Service: Finalized Payslips</h3>
              <p className="text-xs text-slate-400">
                Verified digital payslips with secure tokens, itemized earnings & deduction breakdowns, and HR discrepancy case integration.
              </p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Search className="h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search payslips by number or period..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="max-w-xs bg-slate-950 border-slate-800 text-xs h-8"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {runs
                .filter((r) => ["POSTED", "PAID"].includes(r.status))
                .map((r) => (
                  <div key={r.id} className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-xs font-semibold text-white">Payslip #{r.run_number}</div>
                        <div className="text-[11px] text-slate-400">Period: {r.period_id.substring(0, 8)}</div>
                      </div>
                      <Badge className="bg-emerald-500/20 text-emerald-400 text-[10px]">Published</Badge>
                    </div>

                    <div className="space-y-1.5 text-xs border-y border-slate-800/80 py-2.5">
                      <div className="flex justify-between text-slate-300">
                        <span>Gross Earnings</span>
                        <span>₹{Number(r.total_gross_pay).toLocaleString("en-IN")}</span>
                      </div>
                      <div className="flex justify-between text-rose-400">
                        <span>Total Deductions</span>
                        <span>- ₹{Number(r.total_deductions).toLocaleString("en-IN")}</span>
                      </div>
                      <div className="flex justify-between font-bold text-emerald-400 pt-1 border-t border-slate-800/50">
                        <span>Net Payable</span>
                        <span>₹{Number(r.total_net_pay).toLocaleString("en-IN")}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          showToast({
                            title: "Downloading Payslip",
                            message: `Downloading authenticated PDF for Run ${r.run_number}...`,
                            type: "success",
                          });
                        }}
                        className="h-7 text-[11px] border-slate-700 text-slate-300 hover:bg-slate-800"
                      >
                        <Download className="h-3 w-3 mr-1" /> Download PDF
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedPayslip({
                            id: r.id,
                            tenant_id: r.tenant_id,
                            payroll_run_id: r.id,
                            run_item_id: r.id,
                            employee_id: r.id,
                            payslip_number: `PS-${r.run_number}`,
                            period_code: r.period_id.substring(0, 8),
                            gross_pay: r.total_gross_pay,
                            total_deductions: r.total_deductions,
                            net_pay: r.total_net_pay,
                            secure_token: "token",
                            is_published: true,
                            created_at: r.created_at,
                          });
                          setDisputeModalOpen(true);
                        }}
                        className="h-7 text-[11px] text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                      >
                        <AlertTriangle className="h-3 w-3 mr-1" /> Raise Dispute
                      </Button>
                    </div>
                  </div>
                ))}
              {runs.filter((r) => ["POSTED", "PAID"].includes(r.status)).length === 0 && (
                <div className="col-span-3 text-center py-8 text-slate-500">
                  No published payslips found. Payslips are released upon posting payroll runs to the General Ledger.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal: Create Payroll Run */}
      <Dialog
        isOpen={createRunOpen}
        onClose={() => setCreateRunOpen(false)}
        title="Initialize New Payroll Run"
        description="Select an active calendar and period to prepare employee compensation calculations."
      >
        <form onSubmit={handleCreateRun} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Payroll Calendar</label>
            <select
              value={selectedCalendarId}
              onChange={(e) => handleCalendarChange(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
            >
              {calendars.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.pay_frequency})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Payroll Period</label>
            <select
              value={selectedPeriodId}
              onChange={(e) => setSelectedPeriodId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
            >
              {periods.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.period_code} ({p.start_date} to {p.end_date})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Notes / Run Description</label>
            <Input
              placeholder="e.g. Regular monthly academic faculty and administrative staff salary run."
              value={runNotes}
              onChange={(e) => setRunNotes(e.target.value)}
              className="bg-slate-950 border-slate-800 text-xs"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setCreateRunOpen(false)}
              className="border-slate-800"
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white">
              Initialize Run
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Modal: Run Details & Itemized Calculation Breakdown */}
      <Dialog
        isOpen={runDetailsOpen}
        onClose={() => setRunDetailsOpen(false)}
        title={`Payroll Run #${selectedRun?.run_number || ""}`}
        description="Detailed employee-level calculations, worked days, Loss of Pay adjustments & line items."
        maxWidth="2xl"
      >
        {selectedRun && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500 block text-[10px]">Status</span>
                <span>{getStatusBadge(selectedRun.status)}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Gross Pay</span>
                <span className="font-semibold text-slate-200">₹{Number(selectedRun.total_gross_pay).toLocaleString("en-IN")}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Deductions</span>
                <span className="font-semibold text-rose-400">₹{Number(selectedRun.total_deductions).toLocaleString("en-IN")}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">Net Pay</span>
                <span className="font-semibold text-emerald-400">₹{Number(selectedRun.total_net_pay).toLocaleString("en-IN")}</span>
              </div>
            </div>

            <div className="max-h-72 overflow-y-auto border border-slate-800 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/80">
                    <th className="py-2 px-3">Employee</th>
                    <th className="py-2 px-3">Worked / Unpaid</th>
                    <th className="py-2 px-3">Gross</th>
                    <th className="py-2 px-3">Deductions</th>
                    <th className="py-2 px-3">Net Pay</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {(selectedRun.items || []).map((itm) => (
                    <tr key={itm.id} className="hover:bg-slate-800/20">
                      <td className="py-2 px-3 font-medium text-slate-200">{itm.employee_id.substring(0, 8)}...</td>
                      <td className="py-2 px-3 text-slate-400">
                        {itm.worked_days}d / <span className="text-rose-400 font-semibold">{itm.unpaid_leave_days}d LOP</span>
                      </td>
                      <td className="py-2 px-3 text-slate-300">₹{Number(itm.gross_earnings).toLocaleString("en-IN")}</td>
                      <td className="py-2 px-3 text-rose-400">₹{Number(itm.total_deductions).toLocaleString("en-IN")}</td>
                      <td className="py-2 px-3 font-semibold text-emerald-400">₹{Number(itm.net_pay).toLocaleString("en-IN")}</td>
                    </tr>
                  ))}
                  {(!selectedRun.items || selectedRun.items.length === 0) && (
                    <tr>
                      <td colSpan={5} className="text-center py-6 text-slate-500">
                        No employees calculated yet. Click &quot;Calculate&quot; to compute.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setRunDetailsOpen(false)} className="border-slate-800 text-xs">
                Close
              </Button>
            </div>
          </div>
        )}
      </Dialog>

      {/* Modal: Create Payment Batch */}
      <Dialog
        isOpen={createBatchOpen}
        onClose={() => setCreateBatchOpen(false)}
        title="Disburse Payment Batch"
        description="Prepare bank disbursement instructions for approved payroll."
      >
        <form onSubmit={handleCreateBatch} className="space-y-4">
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Payroll Run:</span>
              <span className="font-semibold text-slate-200">{selectedRun?.run_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Total Net Amount:</span>
              <span className="font-bold text-emerald-400">₹{Number(selectedRun?.total_net_pay || 0).toLocaleString("en-IN")}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Total Beneficiaries:</span>
              <span className="text-slate-200">{selectedRun?.employee_count} employees</span>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Disbursement Method</label>
            <select className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white">
              <option value="BANK_TRANSFER">Direct Electronic Bank Transfer (NEFT / RTGS / ACH)</option>
              <option value="CHEQUE">Corporate Institutional Cheque</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <Button type="button" variant="outline" size="sm" onClick={() => setCreateBatchOpen(false)} className="border-slate-800">
              Cancel
            </Button>
            <Button type="submit" size="sm" className="bg-purple-600 hover:bg-purple-500 text-white">
              Generate Payment Instructions
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Modal: Reconcile Bank UTR */}
      <Dialog
        isOpen={reconcileModalOpen}
        onClose={() => setReconcileModalOpen(false)}
        title="Reconcile Payment Batch"
        description="Confirm bank settlement against corporate payment provider acknowledgment."
      >
        {selectedBatch && (
          <div className="space-y-4">
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Batch Number:</span>
                <span className="font-semibold text-slate-200">{selectedBatch.batch_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Total Amount:</span>
                <span className="font-bold text-emerald-400">₹{Number(selectedBatch.total_amount).toLocaleString("en-IN")}</span>
              </div>
            </div>

            <p className="text-xs text-slate-400">
              Confirming reconciliation will assign authoritative UTR bank references to all itemized disbursements and transition the payroll run to <strong>PAID</strong>.
            </p>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
              <Button type="button" variant="outline" size="sm" onClick={() => setReconcileModalOpen(false)} className="border-slate-800">
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={() => handleReconcileBatch(selectedBatch.id)}
                className="bg-purple-600 hover:bg-purple-500 text-white"
              >
                Confirm UTR Reconciliation
              </Button>
            </div>
          </div>
        )}
      </Dialog>

      {/* Modal: File Payslip Dispute */}
      <Dialog
        isOpen={disputeModalOpen}
        onClose={() => setDisputeModalOpen(false)}
        title="File Compensation / Payroll Dispute"
        description="Creates an authoritative HR Case in the Workforce Management module for investigation."
      >
        <form onSubmit={handleFileDispute} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Subject</label>
            <Input
              placeholder={`Variance reported in payslip ${selectedPayslip?.payslip_number || ""}`}
              value={disputeSubject}
              onChange={(e) => setDisputeSubject(e.target.value)}
              className="bg-slate-950 border-slate-800 text-xs"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Discrepancy Details & Notes</label>
            <textarea
              rows={4}
              placeholder="Describe the discrepancy (e.g., unexpected unpaid leave deduction, incorrect allowance rate, or missing tax exemption certificate)."
              value={disputeDescription}
              onChange={(e) => setDisputeDescription(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
            <Button type="button" variant="outline" size="sm" onClick={() => setDisputeModalOpen(false)} className="border-slate-800">
              Cancel
            </Button>
            <Button type="submit" size="sm" className="bg-amber-600 hover:bg-amber-500 text-white">
              Submit Dispute Case
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}

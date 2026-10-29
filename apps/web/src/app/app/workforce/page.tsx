"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { workforceService } from "@/services/workforce.service";
import type {
  WorkforceEmployeeItem,
  WorkforceEmploymentHistoryItem,
  WorkforceLifecycleCaseItem,
  WorkforceLeaveBalanceItem,
  WorkforceLeaveRequestItem,
  WorkforceHRCaseItem,
  WorkforceReportOverview,
  WorkforceAvailabilityResponse,
  WorkforceWorkloadSummary,
  EmploymentType,
  EmploymentStatus,
} from "@/types/workforce";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import {
  Users,
  Briefcase,
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Plus,
  Search,
  Building2,
  FileText,
  Layers,
  ShieldCheck,
  TrendingUp,
  RefreshCw,
  Send,
  Eye,
  UserCheck,
  Award,
  CalendarClock,
  Check,
  Ban,
  ArrowRight,
} from "lucide-react";

export default function WorkforceManagementPage() {
  const { showToast } = useToast();

  // Active Tab
  const [activeTab, setActiveTab] = useState<
    "overview" | "directory" | "lifecycle" | "leaves" | "availability" | "workload" | "cases" | "reports"
  >("overview");

  // Core State
  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState<WorkforceEmployeeItem[]>([]);
  const [lifecycleCases, setLifecycleCases] = useState<WorkforceLifecycleCaseItem[]>([]);
  const [leaveBalances, setLeaveBalances] = useState<WorkforceLeaveBalanceItem[]>([]);
  const [leaveRequests, setLeaveRequests] = useState<WorkforceLeaveRequestItem[]>([]);
  const [hrCases, setHRCases] = useState<WorkforceHRCaseItem[]>([]);
  const [reportOverview, setReportOverview] = useState<WorkforceReportOverview | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [filterDept, setFilterDept] = useState("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  // Modals
  const [createEmployeeOpen, setCreateEmployeeOpen] = useState(false);
  const [transitionStatusOpen, setTransitionStatusOpen] = useState(false);
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const [leaveRequestOpen, setLeaveRequestOpen] = useState(false);
  const [hrCaseOpen, setHrCaseOpen] = useState(false);
  const [availabilityCheckOpen, setAvailabilityCheckOpen] = useState(false);

  // Selected Records for Modals
  const [selectedEmployee, setSelectedEmployee] = useState<WorkforceEmployeeItem | null>(null);
  const [selectedHistory, setSelectedHistory] = useState<WorkforceEmploymentHistoryItem[]>([]);

  // Form States
  const [newDesignation, setNewDesignation] = useState("");
  const [newJobTitle, setNewJobTitle] = useState("");
  const [newEmpType, setNewEmpType] = useState<EmploymentType>("PERMANENT");
  const [newEmpStatus, setNewEmpStatus] = useState<EmploymentStatus>("ACTIVE");
  const [newJoiningDate, setNewJoiningDate] = useState(new Date().toISOString().split("T")[0]);

  // Transition Form State
  const [targetStatus, setTargetStatus] = useState<EmploymentStatus>("ON_LEAVE");
  const [transitionReason, setTransitionReason] = useState("");

  // Leave Form State
  const [leaveEmpId, setLeaveEmpId] = useState("");
  const [leaveTypeId, setLeaveTypeId] = useState("");
  const [leaveStartDate, setLeaveStartDate] = useState(new Date().toISOString().split("T")[0]);
  const [leaveEndDate, setLeaveEndDate] = useState(new Date().toISOString().split("T")[0]);
  const [leaveReason, setLeaveReason] = useState("");
  const [leaveIsHalfDay, setLeaveIsHalfDay] = useState(false);

  // HR Case Form State
  const [hrCaseCategory, setHrCaseCategory] = useState<"PROFILE_UPDATE" | "EMPLOYMENT_LETTER" | "GENERAL_INQUIRY">("PROFILE_UPDATE");
  const [hrCaseSubject, setHrCaseSubject] = useState("");
  const [hrCaseDescription, setHrCaseDescription] = useState("");

  // Availability State
  const [availEmpId, setAvailEmpId] = useState("");
  const [availStartDate, setAvailStartDate] = useState(new Date().toISOString().split("T")[0]);
  const [availEndDate, setAvailEndDate] = useState(new Date().toISOString().split("T")[0]);
  const [availResult, setAvailResult] = useState<WorkforceAvailabilityResponse | null>(null);
  const [checkingAvail, setCheckingAvail] = useState(false);

  // Workload Summary
  const [workloadEmpId, setWorkloadEmpId] = useState("");
  const [workloadSummary, setWorkloadSummary] = useState<WorkforceWorkloadSummary | null>(null);
  const [loadingWorkload, setLoadingWorkload] = useState(false);

  // ---------------------------------------------------------------------------
  // Load All Data
  // ---------------------------------------------------------------------------
  const loadWorkforceData = useCallback(async () => {
    setLoading(true);
    try {
      const [empRes, casesRes, balancesRes, requestsRes, hrRes, reportRes] = await Promise.allSettled([
        workforceService.listEmployees(),
        workforceService.listLifecycleCases(),
        workforceService.listLeaveBalances(),
        workforceService.listLeaveRequests(),
        workforceService.listHRCases(),
        workforceService.getReportOverview(),
      ]);

      if (empRes.status === "fulfilled") setEmployees(empRes.value.items || []);
      if (casesRes.status === "fulfilled") setLifecycleCases(casesRes.value || []);
      if (balancesRes.status === "fulfilled") setLeaveBalances(balancesRes.value || []);
      if (requestsRes.status === "fulfilled") setLeaveRequests(requestsRes.value || []);
      if (hrRes.status === "fulfilled") setHRCases(hrRes.value || []);
      if (reportRes.status === "fulfilled") setReportOverview(reportRes.value);
    } catch {
      showToast({
        type: "error",
        title: "Load Error",
        message: "Failed to load workforce administration records.",
      });
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadWorkforceData();
  }, [loadWorkforceData]);

  // Set default employee selection when list loads
  useEffect(() => {
    if (employees.length > 0) {
      if (!leaveEmpId) setLeaveEmpId(employees[0].id);
      if (!availEmpId) setAvailEmpId(employees[0].id);
      if (!workloadEmpId) setWorkloadEmpId(employees[0].id);
    }
  }, [employees, leaveEmpId, availEmpId, workloadEmpId]);

  // Load Workload summary when selected workload employee changes
  useEffect(() => {
    if (workloadEmpId) {
      setLoadingWorkload(true);
      workforceService
        .getWorkloadSummary({ employee_id: workloadEmpId })
        .then((res) => setWorkloadSummary(res))
        .catch(() => setWorkloadSummary(null))
        .finally(() => setLoadingWorkload(false));
    }
  }, [workloadEmpId]);

  // ---------------------------------------------------------------------------
  // Filtered Employees
  // ---------------------------------------------------------------------------
  const filteredEmployees = useMemo(() => {
    return employees.filter((emp) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        emp.employee_number.toLowerCase().includes(q) ||
        emp.first_name.toLowerCase().includes(q) ||
        emp.last_name.toLowerCase().includes(q) ||
        emp.official_email.toLowerCase().includes(q) ||
        emp.designation.toLowerCase().includes(q);

      const matchesDept = filterDept === "ALL" || emp.department_name === filterDept;
      const matchesStatus = filterStatus === "ALL" || emp.employment_status === filterStatus;

      return matchesSearch && matchesDept && matchesStatus;
    });
  }, [employees, searchQuery, filterDept, filterStatus]);

  // Departments list for filter dropdown
  const departmentOptions = useMemo(() => {
    const set = new Set<string>();
    employees.forEach((e) => {
      if (e.department_name) set.add(e.department_name);
    });
    return Array.from(set);
  }, [employees]);

  // ---------------------------------------------------------------------------
  // Actions: Employee History & Status Transition
  // ---------------------------------------------------------------------------
  const handleViewHistory = async (emp: WorkforceEmployeeItem) => {
    setSelectedEmployee(emp);
    try {
      const history = await workforceService.getEmploymentHistory(emp.id);
      setSelectedHistory(history);
      setHistoryModalOpen(true);
    } catch {
      showToast({ type: "error", title: "Error", message: "Failed to retrieve employment history." });
    }
  };

  const handleOpenTransition = (emp: WorkforceEmployeeItem) => {
    setSelectedEmployee(emp);
    setTargetStatus("ON_LEAVE");
    setTransitionReason("");
    setTransitionStatusOpen(true);
  };

  const handleExecuteTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmployee) return;

    try {
      await workforceService.transitionStatus(selectedEmployee.id, targetStatus, transitionReason);
      showToast({
        type: "success",
        title: "Status Transitioned",
        message: `${selectedEmployee.first_name} ${selectedEmployee.last_name} transitioned to ${targetStatus}.`,
      });
      setTransitionStatusOpen(false);
      loadWorkforceData();
    } catch (err: unknown) {
      showToast({
        type: "error",
        title: "Transition Failed",
        message: (err as Error).message || "Invalid lifecycle state transition.",
      });
    }
  };

  // ---------------------------------------------------------------------------
  // Actions: Lifecycle Task Completion
  // ---------------------------------------------------------------------------
  const handleCompleteTask = async (taskId: string) => {
    try {
      await workforceService.updateLifecycleTask(taskId, {
        status: "COMPLETED",
        completion_evidence: "Verified by workforce administrator",
      });
      showToast({ type: "success", title: "Task Completed", message: "Lifecycle checklist item updated." });
      loadWorkforceData();
    } catch {
      showToast({ type: "error", title: "Error", message: "Failed to update lifecycle task." });
    }
  };

  // ---------------------------------------------------------------------------
  // Actions: Leave Approvals & Rejections
  // ---------------------------------------------------------------------------
  const handleApproveLeave = async (requestId: string) => {
    try {
      await workforceService.approveLeaveRequest(requestId, "Approved by workforce authority");
      showToast({ type: "success", title: "Leave Approved", message: "Authoritative balance deducted." });
      loadWorkforceData();
    } catch (err: unknown) {
      showToast({
        type: "error",
        title: "Approval Failed",
        message: (err as Error).message || "Separation of duties or policy restriction prevented approval.",
      });
    }
  };

  const handleRejectLeave = async (requestId: string) => {
    const reason = prompt("Enter mandatory rejection justification:");
    if (!reason) return;

    try {
      await workforceService.rejectLeaveRequest(requestId, reason);
      showToast({ type: "success", title: "Leave Rejected", message: "Reserved balance restored." });
      loadWorkforceData();
    } catch (err: unknown) {
      showToast({ type: "error", title: "Rejection Failed", message: (err as Error).message || "Failed to reject leave." });
    }
  };

  const handleCancelLeave = async (requestId: string) => {
    try {
      await workforceService.cancelLeaveRequest(requestId);
      showToast({ type: "success", title: "Leave Cancelled", message: "Request cancelled and balance returned." });
      loadWorkforceData();
    } catch (err: unknown) {
      showToast({ type: "error", title: "Cancellation Failed", message: (err as Error).message || "Failed to cancel leave." });
    }
  };

  // ---------------------------------------------------------------------------
  // Actions: Submit Leave Request
  // ---------------------------------------------------------------------------
  const handleSubmitLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leaveEmpId || !leaveTypeId) {
      showToast({ type: "error", title: "Validation Error", message: "Please select employee and leave type." });
      return;
    }

    try {
      const res = await workforceService.submitLeaveRequest({
        employee_id: leaveEmpId,
        leave_type_id: leaveTypeId,
        start_date: leaveStartDate,
        end_date: leaveEndDate,
        is_half_day: leaveIsHalfDay,
        reason: leaveReason,
      });

      showToast({
        type: "success",
        title: "Leave Submitted",
        message: res.has_timetable_conflicts
          ? "Request submitted with academic timetable collisions flagged!"
          : "Leave request submitted successfully.",
      });
      setLeaveRequestOpen(false);
      setLeaveReason("");
      loadWorkforceData();
    } catch (err: unknown) {
      showToast({
        type: "error",
        title: "Submission Error",
        message: (err as Error).message || "Failed to submit leave request.",
      });
    }
  };

  // ---------------------------------------------------------------------------
  // Actions: Availability Collision Check
  // ---------------------------------------------------------------------------
  const handleCheckAvailability = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!availEmpId) return;

    setCheckingAvail(true);
    try {
      const result = await workforceService.checkAvailability(availEmpId, availStartDate, availEndDate);
      setAvailResult(result);
    } catch (err: unknown) {
      showToast({
        type: "error",
        title: "Availability Error",
        message: (err as Error).message || "Failed to compute availability collision status.",
      });
    } finally {
      setCheckingAvail(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Actions: HR Service Desk Case
  // ---------------------------------------------------------------------------
  const handleCreateHRCase = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await workforceService.createHRCase({
        employee_id: leaveEmpId || undefined,
        category: hrCaseCategory,
        subject: hrCaseSubject,
        description: hrCaseDescription,
      });
      showToast({ type: "success", title: "HR Case Created", message: "Ticket assigned to HR service desk." });
      setHrCaseOpen(false);
      setHrCaseSubject("");
      setHrCaseDescription("");
      loadWorkforceData();
    } catch (err: unknown) {
      showToast({ type: "error", title: "Case Error", message: (err as Error).message || "Failed to create HR case." });
    }
  };

  const handleResolveHRCase = async (caseId: string) => {
    const resolution = prompt("Enter resolution notes:");
    if (!resolution) return;

    try {
      await workforceService.resolveHRCase(caseId, resolution);
      showToast({ type: "success", title: "Case Resolved", message: "HR case marked as resolved." });
      loadWorkforceData();
    } catch {
      showToast({ type: "error", title: "Error", message: "Failed to resolve HR case." });
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* -------------------------------------------------------------------- */}
      {/* Page Header */}
      {/* -------------------------------------------------------------------- */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Workforce & HR Administration</h1>
            <Badge variant="outline" className="border-primary/30 text-primary bg-primary/5 text-xs font-medium">
              Step 51
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Enterprise staff lifecycle, leave ledger, onboarding/offboarding gatekeeping & academic availability.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadWorkforceData} disabled={loading} className="gap-1.5">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setLeaveRequestOpen(true)} className="gap-1.5 bg-primary">
            <Calendar className="h-3.5 w-3.5" />
            Request Leave
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setHrCaseOpen(true)} className="gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            New HR Case
          </Button>
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* KPI Cards */}
      {/* -------------------------------------------------------------------- */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <StatCard
          title="Active Headcount"
          value={reportOverview?.headcount.total_active_employees ?? employees.filter((e) => e.employment_status === "ACTIVE").length}
          icon={<Users className="h-4 w-4 text-emerald-500" />}
          description="Authoritative staff profiles"
        />
        <StatCard
          title="Onboarding Cases"
          value={reportOverview?.headcount.total_onboarding ?? lifecycleCases.filter((c) => c.case_type === "ONBOARDING" && c.status !== "COMPLETED").length}
          icon={<UserCheck className="h-4 w-4 text-amber-500" />}
          description="Pending clearance gates"
        />
        <StatCard
          title="Staff on Leave"
          value={reportOverview?.headcount.total_on_leave ?? employees.filter((e) => e.employment_status === "ON_LEAVE").length}
          icon={<Clock className="h-4 w-4 text-blue-500" />}
          description="Active approved absences"
        />
        <StatCard
          title="Pending Approvals"
          value={reportOverview?.leave_metrics.currently_pending_requests ?? leaveRequests.filter((r) => r.status === "SUBMITTED").length}
          icon={<CalendarClock className="h-4 w-4 text-violet-500" />}
          description="Awaiting manager sign-off"
        />
        <StatCard
          title="Open HR Cases"
          value={reportOverview?.hr_case_metrics.total_open_cases ?? hrCases.filter((c) => c.status === "OPEN" || c.status === "IN_PROGRESS").length}
          icon={<ShieldCheck className="h-4 w-4 text-rose-500" />}
          description="Service inquiries & updates"
        />
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* Tab Navigation */}
      {/* -------------------------------------------------------------------- */}
      <div className="flex border-b border-border/60 overflow-x-auto gap-1">
        {[
          { id: "overview", label: "Overview", icon: LayoutDashboardIcon },
          { id: "directory", label: "Employee Roster", icon: Users },
          { id: "lifecycle", label: "Onboarding & Offboarding", icon: UserCheck },
          { id: "leaves", label: "Leave Engine & Approvals", icon: Calendar },
          { id: "availability", label: "Availability & Conflicts", icon: AlertTriangle },
          { id: "workload", label: "Workload Planning", icon: Layers },
          { id: "cases", label: "HR Service Desk", icon: FileText },
          { id: "reports", label: "Workforce Analytics", icon: TrendingUp },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 py-2.5 px-4 text-xs font-semibold whitespace-nowrap transition-colors border-b-2 -mb-[1px] ${
                isActive
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* TAB 1: OVERVIEW */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Actions & Policy Notice */}
            <div className="p-5 rounded-xl border border-border bg-card/40 backdrop-blur-sm space-y-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-primary" />
                <h3 className="font-semibold text-sm">One Campus. One Source of Truth</h3>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Workforce Management records are strictly tenant-isolated and linked directly to authoritative People records.
                Self-approvals are prohibited by separation-of-duties controls, and academic timetable collisions are proactively flagged.
              </p>
              <div className="pt-2 border-t border-border/40 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Tenant Model</span>
                  <span className="font-medium text-emerald-500">Multi-Tenant Isolated</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Ledger Design</span>
                  <span className="font-medium text-primary">Immutable Transactions</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Timetable Collision Detection</span>
                  <span className="font-medium text-violet-500">Active Published Versions</span>
                </div>
              </div>
            </div>

            {/* Upcoming Milestones */}
            <div className="p-5 rounded-xl border border-border bg-card/40 backdrop-blur-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <Award className="h-4 w-4 text-amber-500" />
                  Upcoming Probation Milestones
                </h3>
                <span className="text-xs text-muted-foreground">
                  {reportOverview?.upcoming_probation_milestones.length ?? 0} Pending
                </span>
              </div>
              <div className="space-y-2">
                {reportOverview?.upcoming_probation_milestones.slice(0, 3).map((m, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40 text-xs">
                    <div>
                      <p className="font-medium">{m.employee_name}</p>
                      <p className="text-[11px] text-muted-foreground">{m.department_name || "General"} · {m.employee_number}</p>
                    </div>
                    <Badge variant="outline" className="text-amber-500 border-amber-500/20 text-[10px]">
                      {m.days_remaining}d left
                    </Badge>
                  </div>
                ))}
                {(!reportOverview || reportOverview.upcoming_probation_milestones.length === 0) && (
                  <p className="text-xs text-muted-foreground italic py-4 text-center">No upcoming probation reviews.</p>
                )}
              </div>
            </div>

            {/* Contract Expirations */}
            <div className="p-5 rounded-xl border border-border bg-card/40 backdrop-blur-sm space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-blue-500" />
                  Contract Renewals & Expirations
                </h3>
                <span className="text-xs text-muted-foreground">
                  {reportOverview?.upcoming_contract_expirations.length ?? 0} Approaching
                </span>
              </div>
              <div className="space-y-2">
                {reportOverview?.upcoming_contract_expirations.slice(0, 3).map((c, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40 text-xs">
                    <div>
                      <p className="font-medium">{c.employee_name}</p>
                      <p className="text-[11px] text-muted-foreground">{c.department_name || "Faculty"} · {c.contract_end_date}</p>
                    </div>
                    <Badge variant="outline" className="text-blue-500 border-blue-500/20 text-[10px]">
                      {c.days_remaining}d remaining
                    </Badge>
                  </div>
                ))}
                {(!reportOverview || reportOverview.upcoming_contract_expirations.length === 0) && (
                  <p className="text-xs text-muted-foreground italic py-4 text-center">No contracts due for expiration.</p>
                )}
              </div>
            </div>
          </div>

          {/* Pending Leave Requests Quick Approval */}
          <div className="rounded-xl border border-border bg-card/40 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-sm">Action Required: Leave Approval Inbox</h3>
                <p className="text-xs text-muted-foreground">Requests awaiting authorized supervisor or HR verification.</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setActiveTab("leaves")} className="text-xs gap-1">
                View All <ArrowRight className="h-3 w-3" />
              </Button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="text-[11px] uppercase bg-muted/40 text-muted-foreground border-b border-border">
                  <tr>
                    <th className="py-2.5 px-3">Employee</th>
                    <th className="py-2.5 px-3">Leave Type</th>
                    <th className="py-2.5 px-3">Dates</th>
                    <th className="py-2.5 px-3">Duration</th>
                    <th className="py-2.5 px-3">Timetable Warning</th>
                    <th className="py-2.5 px-3 text-right">Decision</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {leaveRequests.filter((r) => r.status === "SUBMITTED").slice(0, 5).map((req) => (
                    <tr key={req.id} className="hover:bg-muted/20">
                      <td className="py-2.5 px-3 font-medium">
                        {req.employee_name}
                        <span className="block text-[11px] text-muted-foreground">{req.employee_number}</span>
                      </td>
                      <td className="py-2.5 px-3">{req.leave_type_name}</td>
                      <td className="py-2.5 px-3">
                        {req.start_date} {req.start_date !== req.end_date ? `to ${req.end_date}` : ""}
                      </td>
                      <td className="py-2.5 px-3">{req.total_days} day(s)</td>
                      <td className="py-2.5 px-3">
                        {req.has_timetable_conflicts ? (
                          <Badge variant="outline" className="border-amber-500/30 text-amber-500 bg-amber-500/10 text-[10px] gap-1">
                            <AlertTriangle className="h-2.5 w-2.5" /> Collision Detected
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">None</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right space-x-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleApproveLeave(req.id)}
                          className="h-7 text-[11px] border-emerald-500/40 text-emerald-500 hover:bg-emerald-500/10"
                        >
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleRejectLeave(req.id)}
                          className="h-7 text-[11px] border-rose-500/40 text-rose-500 hover:bg-rose-500/10"
                        >
                          Reject
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {leaveRequests.filter((r) => r.status === "SUBMITTED").length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-muted-foreground">
                        No pending leave requests requiring approval.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* TAB 2: DIRECTORY */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === "directory" && (
        <div className="space-y-4">
          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between bg-card/40 p-3 rounded-xl border border-border">
            <div className="flex flex-1 items-center gap-2">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                <Input
                  placeholder="Search by name, employee #, title..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 h-8 text-xs"
                />
              </div>
              <select
                value={filterDept}
                onChange={(e) => setFilterDept(e.target.value)}
                className="h-8 text-xs bg-background border border-border rounded-md px-2 text-foreground"
              >
                <option value="ALL">All Departments</option>
                {departmentOptions.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="h-8 text-xs bg-background border border-border rounded-md px-2 text-foreground"
              >
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="ONBOARDING">ONBOARDING</option>
                <option value="ON_LEAVE">ON_LEAVE</option>
                <option value="NOTICE_PERIOD">NOTICE_PERIOD</option>
                <option value="SUSPENDED">SUSPENDED</option>
                <option value="SEPARATED">SEPARATED</option>
              </select>
            </div>
          </div>

          {/* Roster Table */}
          <div className="rounded-xl border border-border overflow-hidden bg-card/40">
            <table className="w-full text-xs text-left">
              <thead className="text-[11px] uppercase bg-muted/40 text-muted-foreground border-b border-border">
                <tr>
                  <th className="py-2.5 px-3">Employee</th>
                  <th className="py-2.5 px-3">Designation & Role</th>
                  <th className="py-2.5 px-3">Department & Campus</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Joined</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {filteredEmployees.map((emp) => (
                  <tr key={emp.id} className="hover:bg-muted/20">
                    <td className="py-2.5 px-3 font-medium">
                      {emp.first_name} {emp.last_name}
                      <span className="block text-[11px] text-muted-foreground">{emp.employee_number}</span>
                    </td>
                    <td className="py-2.5 px-3">
                      {emp.designation}
                      <span className="block text-[11px] text-muted-foreground">{emp.job_title}</span>
                    </td>
                    <td className="py-2.5 px-3">
                      {emp.department_name || "—"}
                      <span className="block text-[11px] text-muted-foreground">{emp.campus_name || "Main Campus"}</span>
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge variant="outline" className="text-[10px]">
                        {emp.employment_type}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          emp.employment_status === "ACTIVE"
                            ? "bg-emerald-500/10 text-emerald-500"
                            : emp.employment_status === "ONBOARDING"
                            ? "bg-amber-500/10 text-amber-500"
                            : emp.employment_status === "ON_LEAVE"
                            ? "bg-blue-500/10 text-blue-500"
                            : "bg-rose-500/10 text-rose-500"
                        }`}
                      >
                        {emp.employment_status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-muted-foreground">{emp.joining_date}</td>
                    <td className="py-2.5 px-3 text-right space-x-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleViewHistory(emp)}
                        className="h-7 text-[11px] gap-1"
                      >
                        <Clock className="h-3 w-3" /> History
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleOpenTransition(emp)}
                        className="h-7 text-[11px] gap-1"
                      >
                        Transition
                      </Button>
                    </td>
                  </tr>
                ))}
                {filteredEmployees.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-muted-foreground">
                      No matching employee records found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* TAB 3: LIFECYCLE (ONBOARDING & OFFBOARDING) */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === "lifecycle" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-sm">Staff Lifecycle Cases & Gatekeeping</h3>
              <p className="text-xs text-muted-foreground">
                Mandatory checklist clearance for appointments and auditable asset/access revocations for exits.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {lifecycleCases.map((c) => (
              <div key={c.id} className="p-4 rounded-xl border border-border bg-card/40 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={
                          c.case_type === "ONBOARDING"
                            ? "border-emerald-500/30 text-emerald-500 bg-emerald-500/10"
                            : "border-rose-500/30 text-rose-500 bg-rose-500/10"
                        }
                      >
                        {c.case_type}
                      </Badge>
                      <span className="font-medium text-xs text-foreground">{c.employee_name}</span>
                    </div>
                    <p className="text-[11px] text-muted-foreground mt-1">
                      Initiated: {c.initiated_date} · Tasks: {c.completed_tasks}/{c.total_tasks}
                    </p>
                  </div>
                  <Badge variant="secondary" className="text-[10px]">
                    {c.status}
                  </Badge>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-muted/60 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-primary h-1.5 rounded-full transition-all"
                    style={{ width: `${(c.completed_tasks / Math.max(1, c.total_tasks)) * 100}%` }}
                  />
                </div>

                {/* Task Checklist */}
                <div className="space-y-2 pt-2 border-t border-border/40">
                  <p className="text-[11px] font-semibold text-muted-foreground uppercase">Clearance Checklist</p>
                  {c.tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between p-2 rounded-lg bg-muted/20 text-xs border border-border/30"
                    >
                      <div className="flex items-center gap-2">
                        {task.status === "COMPLETED" ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                        ) : (
                          <Clock className="h-3.5 w-3.5 text-amber-500 shrink-0" />
                        )}
                        <div>
                          <p className={`font-medium ${task.status === "COMPLETED" ? "line-through text-muted-foreground" : ""}`}>
                            {task.title}
                          </p>
                          <span className="text-[10px] text-muted-foreground">
                            {task.category} · Role: {task.assigned_role} {task.is_mandatory && "· Mandatory"}
                          </span>
                        </div>
                      </div>
                      {task.status !== "COMPLETED" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCompleteTask(task.id)}
                          className="h-6 text-[10px] px-2"
                        >
                          Mark Done
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {lifecycleCases.length === 0 && (
              <div className="col-span-2 py-12 text-center text-muted-foreground">
                No active onboarding or offboarding lifecycle cases recorded.
              </div>
            )}
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* TAB 4: LEAVE MANAGEMENT & APPROVALS */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === "leaves" && (
        <div className="space-y-6">
          {/* Leave Balances Ledger Summary */}
          <div>
            <h3 className="font-semibold text-sm mb-3">Leave Balance Ledgers</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {leaveBalances.slice(0, 4).map((b) => (
                <div key={b.id} className="p-3.5 rounded-xl border border-border bg-card/40 space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{b.leave_type_name}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {b.balance_year}
                    </Badge>
                  </div>
                  <p className="text-xl font-bold text-foreground">{b.available_days} d</p>
                  <p className="text-[11px] text-muted-foreground">
                    Accrued: {b.accrued_days} · Used: {b.used_days} · Pending: {b.pending_days}
                  </p>
                </div>
              ))}
              {leaveBalances.length === 0 && (
                <div className="col-span-4 p-4 text-center text-xs text-muted-foreground">
                  No active leave ledgers initialized for current period.
                </div>
              )}
            </div>
          </div>

          {/* All Leave Requests */}
          <div className="rounded-xl border border-border overflow-hidden bg-card/40">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-sm">Authoritative Leave Transactions</h3>
                <p className="text-xs text-muted-foreground">Immutable audit records for all submitted leave requests.</p>
              </div>
              <Button size="sm" onClick={() => setLeaveRequestOpen(true)} className="gap-1 text-xs">
                <Plus className="h-3 w-3" /> Submit Leave
              </Button>
            </div>

            <table className="w-full text-xs text-left">
              <thead className="text-[11px] uppercase bg-muted/40 text-muted-foreground border-b border-border">
                <tr>
                  <th className="py-2.5 px-3">Req #</th>
                  <th className="py-2.5 px-3">Employee</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Dates</th>
                  <th className="py-2.5 px-3">Days</th>
                  <th className="py-2.5 px-3">Reason</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {leaveRequests.map((req) => (
                  <tr key={req.id} className="hover:bg-muted/20">
                    <td className="py-2.5 px-3 font-mono font-medium">{req.request_number}</td>
                    <td className="py-2.5 px-3">
                      {req.employee_name}
                      <span className="block text-[11px] text-muted-foreground">{req.department_name || "General"}</span>
                    </td>
                    <td className="py-2.5 px-3">{req.leave_type_name}</td>
                    <td className="py-2.5 px-3">
                      {req.start_date} {req.start_date !== req.end_date ? `to ${req.end_date}` : ""}
                    </td>
                    <td className="py-2.5 px-3">{req.total_days}</td>
                    <td className="py-2.5 px-3 max-w-xs truncate text-muted-foreground">{req.reason}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          req.status === "APPROVED"
                            ? "bg-emerald-500/10 text-emerald-500"
                            : req.status === "SUBMITTED"
                            ? "bg-amber-500/10 text-amber-500"
                            : req.status === "REJECTED"
                            ? "bg-rose-500/10 text-rose-500"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {req.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right space-x-1">
                      {req.status === "SUBMITTED" && (
                        <>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleApproveLeave(req.id)}
                            className="h-6 text-[11px] text-emerald-500 hover:text-emerald-600"
                          >
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleRejectLeave(req.id)}
                            className="h-6 text-[11px] text-rose-500 hover:text-rose-600"
                          >
                            Reject
                          </Button>
                        </>
                      )}
                      {req.status === "APPROVED" && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleCancelLeave(req.id)}
                          className="h-6 text-[11px] text-amber-500 hover:text-amber-600"
                        >
                          Cancel
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {leaveRequests.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-muted-foreground">
                      No leave requests recorded.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* TAB 5: AVAILABILITY & TIMETABLE CONFLICTS */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === "availability" && (
        <div className="space-y-6">
          <div className="p-5 rounded-xl border border-border bg-card/40 space-y-4">
            <div>
              <h3 className="font-semibold text-sm">Workforce Availability & Academic Collision Engine</h3>
              <p className="text-xs text-muted-foreground">
                Evaluates leave requests against published academic timetable sessions to prevent unstaffed classrooms.
              </p>
            </div>

            <form onSubmit={handleCheckAvailability} className="flex flex-wrap items-end gap-3 pt-2">
              <div className="space-y-1">
                <label className="text-[11px] font-medium text-muted-foreground">Select Faculty / Staff</label>
                <select
                  value={availEmpId}
                  onChange={(e) => setAvailEmpId(e.target.value)}
                  className="h-8 text-xs bg-background border border-border rounded-md px-2 text-foreground"
                >
                  {employees.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.first_name} {e.last_name} ({e.designation})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-medium text-muted-foreground">Start Date</label>
                <Input
                  type="date"
                  value={availStartDate}
                  onChange={(e) => setAvailStartDate(e.target.value)}
                  className="h-8 text-xs"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-medium text-muted-foreground">End Date</label>
                <Input
                  type="date"
                  value={availEndDate}
                  onChange={(e) => setAvailEndDate(e.target.value)}
                  className="h-8 text-xs"
                />
              </div>

              <Button type="submit" size="sm" disabled={checkingAvail} className="h-8 gap-1.5 text-xs">
                <Search className="h-3.5 w-3.5" />
                {checkingAvail ? "Evaluating..." : "Check Conflicts"}
              </Button>
            </form>

            {availResult && (
              <div className="mt-4 pt-4 border-t border-border space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold">Evaluation Status:</span>
                  <Badge
                    variant="outline"
                    className={
                      availResult.is_available
                        ? "border-emerald-500/30 text-emerald-500 bg-emerald-500/10"
                        : "border-rose-500/30 text-rose-500 bg-rose-500/10"
                    }
                  >
                    {availResult.status}
                  </Badge>
                </div>

                {availResult.timetable_session_conflicts.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-rose-500 flex items-center gap-1.5">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Detected {availResult.timetable_session_conflicts.length} Academic Schedule Conflict(s):
                    </p>
                    <div className="space-y-1.5">
                      {availResult.timetable_session_conflicts.map((c, idx) => (
                        <div key={idx} className="p-2.5 rounded-lg bg-rose-500/5 border border-rose-500/20 text-xs flex justify-between">
                          <div>
                            <span className="font-semibold text-rose-400">Date: {c.conflict_date}</span> · Course: {c.course_code}
                          </div>
                          <span className="text-muted-foreground">
                            {c.start_time} - {c.end_time}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-emerald-500 flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5" /> No scheduling collisions found with published timetable sessions.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* TAB 6: WORKLOAD PLANNING */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === "workload" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h3 className="font-semibold text-sm">Faculty & Staff Workload Allocation</h3>
              <p className="text-xs text-muted-foreground">Aggregates scheduled teaching hours, expectations & adjustment credits.</p>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-muted-foreground">Select Faculty:</label>
              <select
                value={workloadEmpId}
                onChange={(e) => setWorkloadEmpId(e.target.value)}
                className="h-8 text-xs bg-background border border-border rounded-md px-2 text-foreground"
              >
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.first_name} {e.last_name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {loadingWorkload && <p className="text-xs text-muted-foreground py-6 text-center">Calculating workload hours...</p>}

          {workloadSummary && !loadingWorkload && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl border border-border bg-card/40 space-y-1">
                <p className="text-xs text-muted-foreground">Expected Target</p>
                <p className="text-xl font-bold">{workloadSummary.expected_hours} hrs/wk</p>
                <p className="text-[11px] text-muted-foreground">Department standard</p>
              </div>

              <div className="p-4 rounded-xl border border-border bg-card/40 space-y-1">
                <p className="text-xs text-muted-foreground">Scheduled Teaching</p>
                <p className="text-xl font-bold text-primary">{workloadSummary.scheduled_teaching_hours} hrs/wk</p>
                <p className="text-[11px] text-muted-foreground">{workloadSummary.sessions_count} Timetable sessions</p>
              </div>

              <div className="p-4 rounded-xl border border-border bg-card/40 space-y-1">
                <p className="text-xs text-muted-foreground">Duty Adjustments</p>
                <p className="text-xl font-bold text-violet-500">{workloadSummary.adjusted_hours} hrs/wk</p>
                <p className="text-[11px] text-muted-foreground">Research/Admin credits</p>
              </div>

              <div className="p-4 rounded-xl border border-border bg-card/40 space-y-1">
                <p className="text-xs text-muted-foreground">Allocation Balance</p>
                <div className="flex items-center gap-2">
                  <p className="text-xl font-bold">{workloadSummary.total_actual_hours} hrs</p>
                  <Badge
                    variant="outline"
                    className={
                      workloadSummary.load_status === "BALANCED"
                        ? "border-emerald-500/30 text-emerald-500 bg-emerald-500/10 text-[10px]"
                        : workloadSummary.load_status === "OVERLOAD"
                        ? "border-rose-500/30 text-rose-500 bg-rose-500/10 text-[10px]"
                        : "border-amber-500/30 text-amber-500 bg-amber-500/10 text-[10px]"
                    }
                  >
                    {workloadSummary.load_status}
                  </Badge>
                </div>
                <p className="text-[11px] text-muted-foreground">Variance: {workloadSummary.variance_hours} hrs</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* TAB 7: HR SERVICE DESK */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === "cases" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-sm">Employee Self-Service & HR Cases</h3>
              <p className="text-xs text-muted-foreground">Profile update proposals, employment letters & service tickets.</p>
            </div>
            <Button size="sm" onClick={() => setHrCaseOpen(true)} className="gap-1.5 text-xs">
              <Plus className="h-3 w-3" /> New Request
            </Button>
          </div>

          <div className="rounded-xl border border-border overflow-hidden bg-card/40">
            <table className="w-full text-xs text-left">
              <thead className="text-[11px] uppercase bg-muted/40 text-muted-foreground border-b border-border">
                <tr>
                  <th className="py-2.5 px-3">Case #</th>
                  <th className="py-2.5 px-3">Employee</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Subject</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Resolution</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {hrCases.map((c) => (
                  <tr key={c.id} className="hover:bg-muted/20">
                    <td className="py-2.5 px-3 font-mono font-medium">{c.case_number}</td>
                    <td className="py-2.5 px-3 font-medium">{c.employee_name}</td>
                    <td className="py-2.5 px-3">
                      <Badge variant="outline" className="text-[10px]">
                        {c.category}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 font-medium max-w-xs truncate">{c.subject}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          c.status === "RESOLVED"
                            ? "bg-emerald-500/10 text-emerald-500"
                            : c.status === "OPEN"
                            ? "bg-amber-500/10 text-amber-500"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-muted-foreground max-w-xs truncate">
                      {c.resolution || "Pending resolution"}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {c.status !== "RESOLVED" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleResolveHRCase(c.id)}
                          className="h-6 text-[10px]"
                        >
                          Resolve
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {hrCases.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-muted-foreground">
                      No HR service tickets recorded.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* TAB 8: WORKFORCE REPORTS */}
      {/* -------------------------------------------------------------------- */}
      {activeTab === "reports" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Department Distribution */}
            <div className="p-5 rounded-xl border border-border bg-card/40 space-y-3">
              <h3 className="font-semibold text-sm">Headcount by Department</h3>
              <div className="space-y-2">
                {reportOverview &&
                  Object.entries(reportOverview.department_distribution).map(([dept, count]) => (
                    <div key={dept} className="flex items-center justify-between text-xs p-2 rounded bg-muted/20">
                      <span>{dept}</span>
                      <span className="font-bold">{count} staff</span>
                    </div>
                  ))}
              </div>
            </div>

            {/* Employment Composition */}
            <div className="p-5 rounded-xl border border-border bg-card/40 space-y-3">
              <h3 className="font-semibold text-sm">Employment Type Composition</h3>
              <div className="space-y-2">
                {reportOverview &&
                  Object.entries(reportOverview.headcount.by_employment_type).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between text-xs p-2 rounded bg-muted/20">
                      <span>{type}</span>
                      <span className="font-bold">{count}</span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* MODAL 1: STATUS TRANSITION */}
      {/* -------------------------------------------------------------------- */}
      <Dialog open={transitionStatusOpen} onOpenChange={setTransitionStatusOpen}>
        <div className="space-y-4 p-1">
          <h3 className="font-semibold text-base">Transition Employment Status</h3>
          {selectedEmployee && (
            <p className="text-xs text-muted-foreground">
              Transitioning <span className="font-medium text-foreground">{selectedEmployee.first_name} {selectedEmployee.last_name}</span> ({selectedEmployee.employee_number}) from{" "}
              <Badge variant="outline" className="text-[10px]">{selectedEmployee.employment_status}</Badge>.
            </p>
          )}

          <form onSubmit={handleExecuteTransition} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">New Employment Status</label>
              <select
                value={targetStatus}
                onChange={(e) => setTargetStatus(e.target.value as EmploymentStatus)}
                className="w-full h-9 text-xs bg-background border border-border rounded-md px-3 text-foreground"
              >
                <option value="ACTIVE">ACTIVE</option>
                <option value="ON_LEAVE">ON_LEAVE</option>
                <option value="SUSPENDED">SUSPENDED</option>
                <option value="NOTICE_PERIOD">NOTICE_PERIOD</option>
                <option value="SEPARATED">SEPARATED</option>
                <option value="ARCHIVED">ARCHIVED</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium">Justification / Reason (Mandatory)</label>
              <Input
                placeholder="Reason for state transition..."
                value={transitionReason}
                onChange={(e) => setTransitionReason(e.target.value)}
                required
                className="text-xs"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3">
              <Button type="button" variant="outline" size="sm" onClick={() => setTransitionStatusOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm">
                Confirm Transition
              </Button>
            </div>
          </form>
        </div>
      </Dialog>

      {/* -------------------------------------------------------------------- */}
      {/* MODAL 2: EMPLOYMENT HISTORY */}
      {/* -------------------------------------------------------------------- */}
      <Dialog open={historyModalOpen} onOpenChange={setHistoryModalOpen}>
        <div className="space-y-4 p-1 max-w-lg">
          <h3 className="font-semibold text-base">Employment Audit Trail</h3>
          {selectedEmployee && (
            <p className="text-xs text-muted-foreground">
              Traceable record of designation, department, and lifecycle transitions for {selectedEmployee.first_name} {selectedEmployee.last_name}.
            </p>
          )}

          <div className="space-y-2 max-h-80 overflow-y-auto">
            {selectedHistory.map((h) => (
              <div key={h.id} className="p-3 rounded-lg border border-border/50 bg-muted/20 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-[10px]">
                    {h.change_type}
                  </Badge>
                  <span className="text-[11px] text-muted-foreground">{h.effective_date}</span>
                </div>
                <p className="font-medium text-foreground">
                  {h.previous_designation && h.new_designation
                    ? `${h.previous_designation} → ${h.new_designation}`
                    : h.previous_status && h.new_status
                    ? `${h.previous_status} → ${h.new_status}`
                    : "Record modified"}
                </p>
                {h.notes && <p className="text-muted-foreground text-[11px]">{h.notes}</p>}
              </div>
            ))}
            {selectedHistory.length === 0 && (
              <p className="text-xs text-muted-foreground italic py-4 text-center">No history events recorded.</p>
            )}
          </div>

          <div className="flex justify-end">
            <Button size="sm" variant="outline" onClick={() => setHistoryModalOpen(false)}>
              Close
            </Button>
          </div>
        </div>
      </Dialog>

      {/* -------------------------------------------------------------------- */}
      {/* MODAL 3: REQUEST LEAVE */}
      {/* -------------------------------------------------------------------- */}
      <Dialog open={leaveRequestOpen} onOpenChange={setLeaveRequestOpen}>
        <div className="space-y-4 p-1">
          <h3 className="font-semibold text-base">Submit Leave Request</h3>
          <p className="text-xs text-muted-foreground">
            Subject to available balance verification and academic timetable collision checking.
          </p>

          <form onSubmit={handleSubmitLeave} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Employee</label>
              <select
                value={leaveEmpId}
                onChange={(e) => setLeaveEmpId(e.target.value)}
                className="w-full h-9 text-xs bg-background border border-border rounded-md px-3 text-foreground"
              >
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.first_name} {e.last_name} ({e.designation})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium">Leave Policy / Type</label>
              <select
                value={leaveTypeId}
                onChange={(e) => setLeaveTypeId(e.target.value)}
                className="w-full h-9 text-xs bg-background border border-border rounded-md px-3 text-foreground"
                required
              >
                <option value="">Select Leave Type</option>
                {leaveBalances.map((b) => (
                  <option key={b.leave_type_id} value={b.leave_type_id}>
                    {b.leave_type_name} (Available: {b.available_days}d)
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium">Start Date</label>
                <Input
                  type="date"
                  value={leaveStartDate}
                  onChange={(e) => setLeaveStartDate(e.target.value)}
                  className="text-xs"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">End Date</label>
                <Input
                  type="date"
                  value={leaveEndDate}
                  onChange={(e) => setLeaveEndDate(e.target.value)}
                  className="text-xs"
                  required
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="halfDayToggle"
                checked={leaveIsHalfDay}
                onChange={(e) => setLeaveIsHalfDay(e.target.checked)}
                className="rounded border-border text-primary"
              />
              <label htmlFor="halfDayToggle" className="text-xs text-foreground cursor-pointer">
                Half-Day Request (0.5 day)
              </label>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium">Reason for Absence</label>
              <Input
                placeholder="Medical appointment, family event..."
                value={leaveReason}
                onChange={(e) => setLeaveReason(e.target.value)}
                required
                className="text-xs"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3">
              <Button type="button" variant="outline" size="sm" onClick={() => setLeaveRequestOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm">
                Submit Request
              </Button>
            </div>
          </form>
        </div>
      </Dialog>

      {/* -------------------------------------------------------------------- */}
      {/* MODAL 4: CREATE HR CASE */}
      {/* -------------------------------------------------------------------- */}
      <Dialog open={hrCaseOpen} onOpenChange={setHrCaseOpen}>
        <div className="space-y-4 p-1">
          <h3 className="font-semibold text-base">New HR Service Desk Case</h3>
          <p className="text-xs text-muted-foreground">Submit a profile update proposal, letter request, or general inquiry.</p>

          <form onSubmit={handleCreateHRCase} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Category</label>
              <select
                value={hrCaseCategory}
                onChange={(e) => setHrCaseCategory(e.target.value as any)}
                className="w-full h-9 text-xs bg-background border border-border rounded-md px-3 text-foreground"
              >
                <option value="PROFILE_UPDATE">Profile Update Proposal</option>
                <option value="EMPLOYMENT_LETTER">Employment Verification Letter</option>
                <option value="GENERAL_INQUIRY">General HR Inquiry</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium">Subject</label>
              <Input
                placeholder="e.g. Update emergency contact number..."
                value={hrCaseSubject}
                onChange={(e) => setHrCaseSubject(e.target.value)}
                required
                className="text-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium">Description</label>
              <textarea
                rows={3}
                placeholder="Details of your request..."
                value={hrCaseDescription}
                onChange={(e) => setHrCaseDescription(e.target.value)}
                required
                className="w-full text-xs bg-background border border-border rounded-md p-2 text-foreground"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3">
              <Button type="button" variant="outline" size="sm" onClick={() => setHrCaseOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm">
                Create Ticket
              </Button>
            </div>
          </form>
        </div>
      </Dialog>
    </div>
  );
}

function LayoutDashboardIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="7" height="9" x="3" y="3" rx="1" />
      <rect width="7" height="5" x="14" y="3" rx="1" />
      <rect width="7" height="9" x="14" y="12" rx="1" />
      <rect width="7" height="5" x="3" y="16" rx="1" />
    </svg>
  );
}

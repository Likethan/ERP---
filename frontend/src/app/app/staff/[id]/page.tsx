"use client";

import React, { use, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { staffService } from "@/services/staff.service";
import { StaffDetailView } from "@/types/domain";
import { StaffShiftItem, StaffLeaveType } from "@/types/people";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs } from "@/components/ui/tabs";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { ArrowLeft, Mail, Phone, Clock, Plus, RefreshCw } from "lucide-react";

export default function Staff360ProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const staffId = resolvedParams.id;
  const { showToast } = useToast();
  const { activePersona } = useAuth();

  // Role permissions
  const canManageRoster =
    activePersona.role === "ADMIN" || activePersona.role === "HOD";
  const canApproveLeave =
    activePersona.role === "ADMIN" || activePersona.role === "HOD";

  const [staff, setStaff] = useState<StaffDetailView | null>(null);
  const [shifts, setShifts] = useState<StaffShiftItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // Change Shift Modal
  const [shiftModalOpen, setShiftModalOpen] = useState(false);
  const [selectedShiftId, setSelectedShiftId] = useState("");

  // Request Leave Modal
  const [leaveModalOpen, setLeaveModalOpen] = useState(false);
  const [leaveType, setLeaveType] = useState<StaffLeaveType>("CASUAL");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [leaveDays, setLeaveDays] = useState("1");
  const [leaveReason, setLeaveReason] = useState("");
  const [isSubmittingLeave, setIsSubmittingLeave] = useState(false);

  const loadStaff = useCallback(async () => {
    setLoading(true);
    try {
      const [staffRes, shiftsRes] = await Promise.all([
        staffService.getById(staffId),
        staffService.getShifts(),
      ]);

      if (staffRes.data) {
        setStaff(staffRes.data);
        if (staffRes.data.shift) {
          setSelectedShiftId(staffRes.data.shift.id);
        }
      }
      if (shiftsRes.data) {
        setShifts(shiftsRes.data);
      }
    } catch {
      showToast({
        type: "error",
        title: "Load Failed",
        message: `Failed to load staff record for ${staffId}.`,
      });
    } finally {
      setLoading(false);
    }
  }, [staffId, showToast]);

  useEffect(() => {
    loadStaff();
  }, [loadStaff]);

  // Handle Shift Update
  const handleAssignShift = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!staff) return;
    try {
      await staffService.assignShift(staff.id, selectedShiftId);
      showToast({
        type: "success",
        title: "Shift Reassigned",
        message: "Updated operational duty hours.",
      });
      setShiftModalOpen(false);
      loadStaff();
    } catch {
      showToast({
        type: "error",
        title: "Update Failed",
        message: "Could not reassign shift.",
      });
    }
  };

  // Handle Leave Request
  const handleRequestLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!staff) return;
    setIsSubmittingLeave(true);
    try {
      await staffService.createLeaveRequest({
        staffId: staff.id,
        staffName: `${staff.firstName} ${staff.lastName}`,
        department: staff.department,
        leaveType,
        startDate: startDate || new Date().toISOString().split("T")[0],
        endDate: endDate || new Date().toISOString().split("T")[0],
        totalDays: Number(leaveDays),
        reason: leaveReason || "Personal absence.",
      });

      showToast({
        type: "success",
        title: "Leave Application Submitted",
        message: "Request queued for departmental supervisory review.",
      });

      setLeaveModalOpen(false);
      setLeaveReason("");
      loadStaff();
    } catch {
      showToast({
        type: "error",
        title: "Submission Failed",
        message: "Failed to queue leave request.",
      });
    } finally {
      setIsSubmittingLeave(false);
    }
  };

  // Handle Approve Leave
  const handleApproveLeave = async (leaveId: string) => {
    await staffService.approveLeave(
      leaveId,
      "Administrative Officer",
      "Approved as per entitlement.",
    );
    showToast({
      type: "success",
      title: "Leave Approved",
      message: "Leave deduction debited from staff leave balance.",
    });
    loadStaff();
  };

  // Handle Reject Leave
  const handleRejectLeave = async (leaveId: string) => {
    await staffService.rejectLeave(
      leaveId,
      "Administrative Officer",
      "Duty constraints on selected dates.",
    );
    showToast({
      type: "warning",
      title: "Leave Rejected",
      message: "Notification dispatched to staff personnel.",
    });
    loadStaff();
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center text-slate-400 font-mono text-xs">
        Loading Staff Master Record...
      </div>
    );
  }

  if (!staff) {
    return (
      <div className="space-y-4">
        <Link href="/app/staff">
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            Back to Directory
          </Button>
        </Link>
        <EmptyState
          title="Staff Member Not Found"
          description={`No administrative staff profile exists with identifier "${staffId}".`}
          actionLabel="Return to Staff Directory"
          onAction={() => (window.location.href = "/app/staff")}
        />
      </div>
    );
  }

  const leaves = staff.leaves || [];

  const TABS = [
    { id: "overview", label: "Overview & Position" },
    {
      id: "shift",
      label: `Operational Shift (${staff.shift?.shiftType || "GENERAL"})`,
    },
    { id: "leave", label: `Leave Roster (${leaves.length})` },
    { id: "timeline", label: "Service Timeline" },
  ];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link href="/app/staff">
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            Back to Staff Directory
          </Button>
        </Link>
      </div>

      {/* Main Staff 360 Header Banner */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 shadow-xs backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-500/10 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-500/20 text-2xl font-bold font-mono shrink-0">
              {staff.firstName[0]}
              {staff.lastName[0]}
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                  {staff.firstName} {staff.lastName}
                </h1>
                <Badge
                  variant={staff.status === "ACTIVE" ? "success" : "secondary"}
                  dot
                >
                  {staff.status}
                </Badge>
                <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                  {staff.employeeCode}
                </span>
                <span className="rounded bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/60">
                  {staff.shift?.shiftType || "GENERAL"} SHIFT
                </span>
              </div>

              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {staff.role} &bull; {staff.department}
              </p>

              <div className="mt-2.5 flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  {staff.email}
                </span>
                <span className="flex items-center gap-1.5">
                  <Phone className="h-3.5 w-3.5 text-slate-400" />
                  {staff.phone}
                </span>
                <span className="flex items-center gap-1.5 font-mono">
                  <Clock className="h-3.5 w-3.5 text-slate-400" />
                  {staff.shift?.startTime} - {staff.shift?.endTime}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-center">
            <Button
              onClick={() => setShiftModalOpen(true)}
              variant="outline"
              size="sm"
              leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
            >
              Reassign Shift
            </Button>
            <Button
              onClick={() => setLeaveModalOpen(true)}
              variant="primary"
              size="sm"
              leftIcon={<Plus className="h-3.5 w-3.5" />}
            >
              Apply Leave
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {/* ======================================================== */}
      {/* TAB 1: OVERVIEW */}
      {/* ======================================================== */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Personnel Identity & Terms</CardTitle>
              <CardDescription>
                Employment classification and official university role.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Official Role</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {staff.role}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Department</span>
                <span className="text-slate-800 dark:text-slate-200">
                  {staff.department}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-400">Employment Terms</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 font-medium">
                  {staff.employmentType || "PERMANENT"}
                </span>
              </div>
              <div className="grid grid-cols-2 py-1.5">
                <span className="text-slate-400">Appointment Joining Date</span>
                <span className="font-mono text-slate-800 dark:text-slate-200">
                  {staff.joiningDate}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Leave Balances Card */}
          <Card>
            <CardHeader>
              <CardTitle>Statutory Leave Entitlements</CardTitle>
              <CardDescription>
                Current available balance for academic calendar year.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <div className="text-xs text-slate-500">Casual Leave</div>
                  <div className="text-xl font-bold font-mono text-indigo-600 dark:text-indigo-400 mt-1">
                    {staff.leaveBalance?.casual ?? 8}
                  </div>
                  <span className="text-[10px] text-slate-400">
                    Days Available
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <div className="text-xs text-slate-500">Medical / Sick</div>
                  <div className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                    {staff.leaveBalance?.sick ?? 10}
                  </div>
                  <span className="text-[10px] text-slate-400">
                    Days Available
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <div className="text-xs text-slate-500">Earned Leave</div>
                  <div className="text-xl font-bold font-mono text-purple-600 dark:text-purple-400 mt-1">
                    {staff.leaveBalance?.earned ?? 22}
                  </div>
                  <span className="text-[10px] text-slate-400">
                    Days Available
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 2: SHIFT MANAGEMENT */}
      {/* ======================================================== */}
      {activeTab === "shift" && (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Current Operational Shift Schedule
                </h3>
                <p className="text-xs text-slate-500">
                  Campus facility coverage, daily sign-in and sign-out
                  parameters.
                </p>
              </div>
              {canManageRoster && (
                <Button
                  size="sm"
                  variant="outline"
                  leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
                  onClick={() => setShiftModalOpen(true)}
                >
                  Change Shift Schedule
                </Button>
              )}
            </div>

            {staff.shift ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <span className="text-xs text-slate-400 font-semibold uppercase">
                    Shift Name
                  </span>
                  <div className="text-base font-bold text-slate-900 dark:text-white mt-1">
                    {staff.shift.shiftName}
                  </div>
                  <Badge variant="secondary" className="mt-2">
                    {staff.shift.shiftType}
                  </Badge>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <span className="text-xs text-slate-400 font-semibold uppercase">
                    Daily Timings
                  </span>
                  <div className="text-base font-bold font-mono text-indigo-600 dark:text-indigo-400 mt-1">
                    {staff.shift.startTime} &mdash; {staff.shift.endTime}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    8 Hours Daily Duty
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                  <span className="text-xs text-slate-400 font-semibold uppercase">
                    Scope & Coverage
                  </span>
                  <div className="text-xs text-slate-700 dark:text-slate-300 mt-1">
                    {staff.shift.description || "General operational support."}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 py-4">
                No shift schedule mapped.
              </p>
            )}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 3: LEAVE WORKFLOW */}
      {/* ======================================================== */}
      {activeTab === "leave" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Leave Applications & Absence History
              </h3>
              <p className="text-xs text-slate-500">
                Logged leave requests, approvals, and supervisory remarks.
              </p>
            </div>
            <Button
              size="sm"
              variant="primary"
              leftIcon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => setLeaveModalOpen(true)}
            >
              Apply Leave
            </Button>
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-xs">
            {leaves.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No leave requests filed during the active academic semester.
              </div>
            ) : (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Leave Type</th>
                    <th className="px-4 py-3">Duration</th>
                    <th className="px-4 py-3">Days</th>
                    <th className="px-4 py-3">Reason</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Supervisory Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {leaves.map((lv) => (
                    <tr
                      key={lv.id}
                      className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition"
                    >
                      <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">
                        {lv.leaveType}
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-600 dark:text-slate-300">
                        {lv.startDate} &rarr; {lv.endDate}
                      </td>
                      <td className="px-4 py-3 font-mono font-bold">
                        {lv.totalDays} {lv.totalDays === 1 ? "day" : "days"}
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300 max-w-xs truncate">
                        {lv.reason}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={
                            lv.status === "APPROVED"
                              ? "success"
                              : lv.status === "PENDING"
                                ? "warning"
                                : "destructive"
                          }
                          dot
                        >
                          {lv.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {lv.status === "PENDING" ? (
                          canApproveLeave ? (
                            <div className="flex items-center justify-end gap-1.5">
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleApproveLeave(lv.id)}
                              >
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleRejectLeave(lv.id)}
                                className="text-rose-500 hover:text-rose-600"
                              >
                                Reject
                              </Button>
                            </div>
                          ) : (
                            <span className="text-[11px] text-amber-500 font-mono">
                              Pending Review
                            </span>
                          )
                        ) : (
                          <span className="text-[11px] text-slate-400 font-mono">
                            {lv.reviewedBy || "Reviewed"}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* TAB 4: TIMELINE */}
      {/* ======================================================== */}
      {activeTab === "timeline" && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs">
          <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
            Staff Service History
          </h3>
          <p className="text-xs text-slate-500 mb-6">
            Institutional career records and shift duty assignments.
          </p>

          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
            <div className="relative">
              <div className="absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-indigo-600 bg-white dark:bg-slate-900" />
              <div className="text-xs">
                <span className="font-mono text-slate-400">2026-08-01</span>
                <h4 className="font-bold text-slate-900 dark:text-white mt-0.5">
                  Shift Schedule Reconfirmed for Academic Term
                </h4>
                <p className="text-slate-500">
                  Allocated to {staff.shift?.shiftName || "General Shift"}.
                </p>
              </div>
            </div>

            <div className="relative">
              <div className="absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-indigo-600 bg-white dark:bg-slate-900" />
              <div className="text-xs">
                <span className="font-mono text-slate-400">
                  {staff.joiningDate}
                </span>
                <h4 className="font-bold text-slate-900 dark:text-white mt-0.5">
                  Appointment Induction to Campus Support Operations
                </h4>
                <p className="text-slate-500">
                  Designated as {staff.role} in {staff.department}.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODALS */}
      {/* ======================================================== */}

      {/* Change Shift Modal */}
      <Dialog
        open={shiftModalOpen}
        onClose={() => setShiftModalOpen(false)}
        title="Reassign Operational Shift Schedule"
      >
        <form onSubmit={handleAssignShift} className="space-y-4 pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Select Shift
            </label>
            <select
              value={selectedShiftId}
              onChange={(e) => setSelectedShiftId(e.target.value)}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
            >
              {shifts.map((sh) => (
                <option key={sh.id} value={sh.id}>
                  {sh.shiftName} ({sh.startTime} - {sh.endTime})
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShiftModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Confirm Reassignment
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Request Leave Modal */}
      <Dialog
        open={leaveModalOpen}
        onClose={() => setLeaveModalOpen(false)}
        title="Apply for Absence / Leave of Duty"
      >
        <form onSubmit={handleRequestLeave} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Leave Category
              </label>
              <select
                value={leaveType}
                onChange={(e) => setLeaveType(e.target.value as StaffLeaveType)}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200"
              >
                <option value="CASUAL">Casual Leave (Personal)</option>
                <option value="SICK">Medical / Sick Leave</option>
                <option value="EARNED">Earned Privilege Leave</option>
                <option value="DUTY">Official Duty Deputation</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Number of Days
              </label>
              <Input
                type="number"
                min="1"
                max="30"
                value={leaveDays}
                onChange={(e) => setLeaveDays(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Start Date
              </label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                End Date
              </label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Reason for Absence *
            </label>
            <textarea
              required
              rows={3}
              value={leaveReason}
              onChange={(e) => setLeaveReason(e.target.value)}
              placeholder="State reason and hand-over arrangements..."
              className="w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setLeaveModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isSubmittingLeave}
            >
              Submit Application
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}

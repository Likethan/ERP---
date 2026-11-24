"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { teachingService } from "@/services/teaching.service";
import {
  FacultyLeaveApplication,
  FacultyLeaveBalance,
  FacultyLeaveType,
} from "@/types/teaching";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  CalendarDays,
  Plus,
  Clock,
  CheckCircle2,
  XCircle,
  FileText,
  UserCheck,
  ShieldCheck,
  ArrowRight,
  Briefcase,
  AlertCircle,
} from "lucide-react";

export default function FacultyLeaveManagementPage() {
  const { user, activePersona } = useAuth();
  const { showToast } = useToast();

  const userRole = activePersona?.role || user?.roles?.[0]?.name || "FACULTY";
  const isHOD =
    userRole === "HOD" ||
    userRole === "PRINCIPAL" ||
    userRole === "ADMIN" ||
    userRole === "SUPER_ADMIN";

  const [loading, setLoading] = useState(true);
  const [balances, setBalances] = useState<FacultyLeaveBalance[]>([]);
  const [leaves, setLeaves] = useState<FacultyLeaveApplication[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  // Apply Modal
  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    leaveType: "CASUAL" as FacultyLeaveType,
    startDate: new Date().toISOString().split("T")[0],
    endDate: new Date().toISOString().split("T")[0],
    totalDays: 1,
    reason: "",
    substituteFacultyId: "fac-cse-02",
    substituteFacultyName: "Dr. Ramesh Sundaram",
    substituteClassesArranged: true,
  });

  // HOD Review Modal
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedLeave, setSelectedLeave] =
    useState<FacultyLeaveApplication | null>(null);
  const [reviewAction, setReviewAction] = useState<"APPROVE" | "REJECT">(
    "APPROVE",
  );
  const [hodRemarks, setHodRemarks] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [balRes, leavesRes] = await Promise.all([
        teachingService.getFacultyLeaveBalances(),
        teachingService.getFacultyLeaves(),
      ]);
      if (balRes.success) setBalances(balRes.data);
      if (leavesRes.success) setLeaves(leavesRes.data);
    } catch (err) {
      console.error(err);
      showToast({
        type: "error",
        title: "Error",
        message: "Failed to load leave records.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredLeaves = useMemo(() => {
    if (selectedStatus === "ALL") return leaves;
    return leaves.filter((l) => l.status === selectedStatus);
  }, [leaves, selectedStatus]);

  const handleApplyLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.reason.trim()) {
      showToast({
        type: "error",
        title: "Validation Error",
        message: "Reason is required.",
      });
      return;
    }
    try {
      setSubmitting(true);
      const res = await teachingService.applyFacultyLeave({
        facultyId: activePersona?.id || "fac-cse-01",
        facultyName: activePersona?.name || "Dr. Rajesh Sharma",
        employeeCode: "EMP-CSE-01",
        department:
          activePersona?.department || "Computer Science & Engineering",
        leaveType: formData.leaveType,
        startDate: formData.startDate,
        endDate: formData.endDate,
        totalDays: Number(formData.totalDays),
        reason: formData.reason,
        substituteFacultyId: formData.substituteFacultyId,
        substituteFacultyName: formData.substituteFacultyName,
        substituteClassesArranged: formData.substituteClassesArranged,
      });

      if (res.success) {
        showToast({
          type: "success",
          title: "Leave Application Submitted",
          message:
            "Application routed to Head of Department (Dr. K. S. Anand) for endorsement.",
        });
        setApplyModalOpen(false);
        setFormData({ ...formData, reason: "" });
        await loadData();
      }
    } catch (err: any) {
      showToast({
        type: "error",
        title: "Application Failed",
        message: err.message,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleProcessHOD = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLeave) return;
    try {
      setReviewing(true);
      const res = await teachingService.processFacultyLeaveHOD(
        selectedLeave.id,
        reviewAction,
        hodRemarks ||
          (reviewAction === "APPROVE"
            ? "Approved by HOD. Substitute noted."
            : "Rejected by HOD."),
      );

      if (res.success) {
        showToast({
          type: "success",
          title:
            reviewAction === "APPROVE" ? "Leave Approved" : "Leave Rejected",
          message: `Application updated. Faculty balance adjusted accordingly.`,
        });
        setReviewModalOpen(false);
        await loadData();
      }
    } catch (err: any) {
      showToast({
        type: "error",
        title: "Action Failed",
        message: err.message,
      });
    } finally {
      setReviewing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs border-l-4 border-l-yellow-400">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-semibold text-yellow-950 border border-yellow-300 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-600" />
            Workforce Administration & Absence Governance
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Apply for Faculty Leave
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Dedicated institutional faculty leave portal featuring balance
            accrual tracking, substitute class arrangements, and HOD endorsement
            workflows.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/attendance/leaves">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<UserCheck className="h-3.5 w-3.5" />}
            >
              Student Leave Approvals
            </Button>
          </Link>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-3.5 w-3.5" />}
            onClick={() => setApplyModalOpen(true)}
          >
            Apply for Leave
          </Button>
        </div>
      </div>

      {/* Leave Balances Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {balances.map((b) => (
          <Card
            key={b.leaveType}
            className="hover:border-yellow-300 transition-all"
          >
            <CardContent className="p-4 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-800">{b.label}</span>
                <span className="text-slate-500 font-mono">
                  {b.consumedDays} / {b.allocatedDays} Used
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-slate-900">
                  {b.availableDays}
                </span>
                <span className="text-xs text-slate-500 font-medium">
                  Days Available
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full bg-yellow-500 rounded-full"
                  style={{
                    width: `${Math.min(
                      100,
                      Math.round(
                        (b.availableDays / (b.allocatedDays || 1)) * 100,
                      ),
                    )}%`,
                  }}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Leave Applications History */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle>My Faculty Leave Applications</CardTitle>
            <CardDescription>
              Audit ledger of leave requests, substitute teacher assignments,
              and HOD approvals.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING_HOD">Pending HOD Review</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-600">
                  <th className="py-3 px-4">Leave Type</th>
                  <th className="py-3 px-4">Duration & Dates</th>
                  <th className="py-3 px-4">Reason</th>
                  <th className="py-3 px-4">Substitute Faculty</th>
                  <th className="py-3 px-4">Status & HOD Decision</th>
                  {isHOD && <th className="py-3 px-4 text-right">Action</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      Loading leave applications...
                    </td>
                  </tr>
                ) : filteredLeaves.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No leave applications found matching filter.
                    </td>
                  </tr>
                ) : (
                  filteredLeaves.map((l) => (
                    <tr
                      key={l.id}
                      className="hover:bg-yellow-50/20 transition-colors"
                    >
                      <td className="py-3.5 px-4 font-semibold text-slate-900">
                        {l.leaveType.replace(/_/g, " ")}
                        <div className="text-[11px] text-slate-500 font-normal">
                          Applied: {new Date(l.appliedAt).toLocaleDateString()}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 font-mono">
                        <div className="font-bold text-slate-900">
                          {l.totalDays} Day{l.totalDays > 1 ? "s" : ""}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {l.startDate} to {l.endDate}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 max-w-xs text-slate-700">
                        {l.reason}
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-medium text-slate-900">
                          {l.substituteFacultyName}
                        </div>
                        <div className="text-[11px] text-emerald-700 flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" /> Class Swaps
                          Arranged
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <Badge
                          variant={
                            l.status === "APPROVED"
                              ? "success"
                              : l.status === "PENDING_HOD"
                                ? "warning"
                                : "danger"
                          }
                          dot
                        >
                          {l.status.replace(/_/g, " ")}
                        </Badge>
                        {l.hodRemarks && (
                          <div className="text-[11px] text-slate-500 mt-1 italic">
                            "{l.hodRemarks}"
                          </div>
                        )}
                      </td>

                      {isHOD && (
                        <td className="py-3.5 px-4 text-right">
                          {l.status === "PENDING_HOD" && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-xs h-7 px-2.5"
                              onClick={() => {
                                setSelectedLeave(l);
                                setHodRemarks("");
                                setReviewModalOpen(true);
                              }}
                            >
                              Review
                            </Button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Apply Leave Dialog */}
      <Dialog
        isOpen={applyModalOpen}
        onClose={() => setApplyModalOpen(false)}
        title="Apply for Faculty Leave"
      >
        <form onSubmit={handleApplyLeave} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Leave Category
              </label>
              <select
                value={formData.leaveType}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    leaveType: e.target.value as FacultyLeaveType,
                  })
                }
                className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              >
                <option value="CASUAL">Casual Leave (CL)</option>
                <option value="MEDICAL">Medical / Sick Leave (ML)</option>
                <option value="ON_DUTY">On Duty (OD) / Deputation</option>
                <option value="EARNED">Earned Leave (EL)</option>
                <option value="SPECIAL_CASUAL">Special Casual Leave</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700">
                Total Days Requested
              </label>
              <Input
                type="number"
                min="0.5"
                step="0.5"
                max="30"
                value={formData.totalDays}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    totalDays: Number(e.target.value),
                  })
                }
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">
                From Date
              </label>
              <Input
                type="date"
                value={formData.startDate}
                onChange={(e) =>
                  setFormData({ ...formData, startDate: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700">
                To Date
              </label>
              <Input
                type="date"
                value={formData.endDate}
                onChange={(e) =>
                  setFormData({ ...formData, endDate: e.target.value })
                }
                required
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Justification / Reason for Leave
            </label>
            <textarea
              rows={3}
              placeholder="State official reason for leave request..."
              className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              value={formData.reason}
              onChange={(e) =>
                setFormData({ ...formData, reason: e.target.value })
              }
              required
            />
          </div>

          <div className="rounded-lg bg-slate-50 p-3.5 border border-slate-200 space-y-3">
            <div className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              <UserCheck className="h-4 w-4 text-yellow-600" />
              Substitute Teacher Lecture Coverage
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-700">
                Nominated Colleague for Lecture Swap
              </label>
              <select
                value={formData.substituteFacultyName}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    substituteFacultyName: e.target.value,
                    substituteFacultyId: e.target.value.includes("Ramesh")
                      ? "fac-cse-02"
                      : "fac-cse-03",
                  })
                }
                className="w-full rounded-lg border border-slate-200 bg-white p-2 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              >
                <option value="Dr. Ramesh Sundaram">
                  Dr. Ramesh Sundaram (Associate Professor, CSE)
                </option>
                <option value="Dr. Priya Natarajan">
                  Dr. Priya Natarajan (Assistant Professor, CSE)
                </option>
                <option value="Prof. Anand V.">
                  Prof. Anand V. (Assistant Professor, CSE)
                </option>
              </select>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="subArranged"
                checked={formData.substituteClassesArranged}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    substituteClassesArranged: e.target.checked,
                  })
                }
                className="h-4 w-4 rounded border-slate-300 text-yellow-500 focus:ring-yellow-400"
              />
              <label htmlFor="subArranged" className="text-xs text-slate-700">
                I have coordinated with the colleague above to cover all
                scheduled lecture hours.
              </label>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button
              variant="ghost"
              size="sm"
              type="button"
              onClick={() => setApplyModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Submitting..." : "Submit Application to HOD"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* HOD Review Dialog */}
      <Dialog
        isOpen={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        title="Departmental Endorsement: Faculty Leave"
      >
        <form onSubmit={handleProcessHOD} className="space-y-4">
          <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div>
              Faculty:{" "}
              <strong className="text-slate-900">
                {selectedLeave?.facultyName}
              </strong>{" "}
              ({selectedLeave?.employeeCode})
            </div>
            <div>
              Duration: <strong>{selectedLeave?.totalDays} Days</strong> (
              {selectedLeave?.startDate} to {selectedLeave?.endDate})
            </div>
            <div>
              Substitute:{" "}
              <strong>{selectedLeave?.substituteFacultyName}</strong>
            </div>
            <div className="mt-1">Reason: "{selectedLeave?.reason}"</div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              HOD Decision
            </label>
            <div className="grid grid-cols-2 gap-3 mt-1">
              <Button
                type="button"
                variant={reviewAction === "APPROVE" ? "primary" : "outline"}
                size="sm"
                className="w-full text-xs"
                onClick={() => setReviewAction("APPROVE")}
              >
                Approve Leave
              </Button>
              <Button
                type="button"
                variant={reviewAction === "REJECT" ? "destructive" : "outline"}
                size="sm"
                className="w-full text-xs"
                onClick={() => setReviewAction("REJECT")}
              >
                Reject Request
              </Button>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Departmental Remarks / Endorsement Notes
            </label>
            <Input
              placeholder="e.g. Approved. Lecture swaps confirmed with Dr. Ramesh Sundaram."
              value={hodRemarks}
              onChange={(e) => setHodRemarks(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button
              variant="ghost"
              size="sm"
              type="button"
              onClick={() => setReviewModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={reviewing}
            >
              {reviewing ? "Processing..." : "Submit Endorsement"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}

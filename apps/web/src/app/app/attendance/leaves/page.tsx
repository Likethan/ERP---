"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceLeave, AttendanceLeaveStatus, LeaveType } from "@/types/attendance";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import {
  FileCheck2,
  Plus,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
  FileText,
  User,
  ArrowRight,
} from "lucide-react";

export default function LeaveManagementPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [leaves, setLeaves] = useState<AttendanceLeave[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Create Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    department: "Computer Science & Engineering",
    section: "A",
    leaveType: "MEDICAL" as LeaveType,
    startDate: new Date().toISOString().split("T")[0],
    endDate: new Date().toISOString().split("T")[0],
    totalDays: 1,
    reason: "",
    supportingDocName: "",
  });

  // Review Modal
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedLeave, setSelectedLeave] = useState<AttendanceLeave | null>(null);
  const [reviewAction, setReviewAction] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const loadLeaves = async () => {
    try {
      setLoading(true);
      const res = await attendanceService.getLeaves({
        status: statusFilter !== "ALL" ? statusFilter : undefined,
      });
      if (res.success) {
        setLeaves(res.data);
      }
    } catch (err) {
      console.error("Failed to load leaves", err);
      showToast({ type: "error", title: "Load Error", message: "Failed to load leave requests." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeaves();
  }, [statusFilter]);

  const handleCreateLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const res = await attendanceService.submitLeave(formData);
      if (res.success) {
        showToast({
          type: "success",
          title: "Leave Submitted",
          message: "Application queued for academic review.",
        });
        setCreateModalOpen(false);
        setFormData({ ...formData, reason: "", supportingDocName: "" });
        await loadLeaves();
      }
    } catch (err) {
      console.error("Failed to submit leave", err);
      showToast({ type: "error", title: "Submission Failed", message: "Could not submit leave request." });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReviewLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLeave) return;
    try {
      setReviewing(true);
      const res = await attendanceService.updateLeaveStatus(
        selectedLeave.id,
        reviewAction,
        reviewNotes,
        "Dr. K. S. Anand (HOD - CSE)"
      );
      if (res.success) {
        showToast({
          type: "success",
          title: `Leave ${reviewAction}`,
          message: `Application for ${res.data.studentName} has been ${reviewAction.toLowerCase()}.`,
        });
        setReviewModalOpen(false);
        setSelectedLeave(null);
        setReviewNotes("");
        await loadLeaves();
      }
    } catch (err) {
      console.error("Failed to update leave", err);
      showToast({ type: "error", title: "Update Failed", message: "Could not update leave status." });
    } finally {
      setReviewing(false);
    }
  };

  const getStatusBadge = (status: AttendanceLeaveStatus) => {
    switch (status) {
      case "APPROVED":
        return <Badge variant="success">Approved</Badge>;
      case "REJECTED":
        return <Badge variant="destructive">Rejected</Badge>;
      case "PENDING":
        return <Badge variant="warning">Pending Review</Badge>;
      case "CANCELLED":
        return <Badge variant="secondary">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const columns: ColumnDef<AttendanceLeave>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Student Name & Roll No.",
        cell: (row) => (
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              {row.studentName}
            </div>
            <div className="text-xs text-slate-500">{row.rollNumber} • Sec {row.section}</div>
          </div>
        ),
        sortable: true,
      },
      {
        id: "leaveType",
        header: "Leave Category",
        cell: (row) => (
          <div>
            <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
              {row.leaveType}
            </span>
            <div className="text-xs text-slate-500 mt-1 truncate max-w-[200px]">
              {row.reason}
            </div>
          </div>
        ),
        sortable: true,
      },
      {
        id: "duration",
        header: "Duration & Days",
        cell: (row) => (
          <div>
            <div className="font-medium text-slate-800 dark:text-slate-200 text-xs">
              {row.startDate} to {row.endDate}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5 font-semibold text-indigo-600 dark:text-indigo-400">
              {row.totalDays} {row.totalDays === 1 ? "Day" : "Days"}
            </div>
          </div>
        ),
      },
      {
        id: "status",
        header: "Status",
        cell: (row) => getStatusBadge(row.status),
        sortable: true,
      },
      {
        id: "reviewedBy",
        header: "Review Details",
        cell: (row) => (
          <div className="text-xs text-slate-600 dark:text-slate-400">
            {row.reviewedBy ? (
              <div>
                <div className="font-medium text-slate-800 dark:text-slate-200">{row.reviewedBy}</div>
                <div className="text-[10px] text-slate-400">{new Date(row.reviewedAt || "").toLocaleDateString()}</div>
              </div>
            ) : (
              <span className="text-slate-400 italic">Awaiting HOD sign-off</span>
            )}
          </div>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <div className="flex items-center gap-2">
            {row.status === "PENDING" && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setSelectedLeave(row);
                  setReviewAction("APPROVED");
                  setReviewModalOpen(true);
                }}
                className="h-7 text-xs"
              >
                Review Request
              </Button>
            )}
            {row.status !== "PENDING" && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setSelectedLeave(row);
                  setReviewModalOpen(true);
                }}
                className="h-7 text-xs text-slate-500"
              >
                View Details
              </Button>
            )}
          </div>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
              Absence Exemption
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Excused Absence Workflow</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Student Leave Management
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Submit and review medical, sports, and official on-duty leave requests for percentage exemption.
          </p>
        </div>

        <Button variant="primary" className="gap-2" onClick={() => setCreateModalOpen(true)}>
          <Plus className="h-4 w-4" />
          Apply for Leave
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filter Status:
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Requests ({leaves.length})</option>
          <option value="PENDING">Pending Review</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<AttendanceLeave>
        data={leaves}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search leaves by student name, roll number, or reason..."
        emptyTitle="No leave requests found"
        emptyDescription="Submit a new application to request an excused attendance exemption."
      />

      {/* Apply Leave Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Submit Excused Leave Application"
      >
        <form onSubmit={handleCreateLeave} className="space-y-4 text-xs">
          <p className="text-slate-500">
            Approved leaves are counted as valid exemptions in course attendance calculations.
          </p>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Student Name
              </label>
              <input
                type="text"
                required
                value={formData.studentName}
                onChange={(e) => setFormData({ ...formData, studentName: e.target.value })}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Roll Number
              </label>
              <input
                type="text"
                required
                value={formData.rollNumber}
                onChange={(e) => setFormData({ ...formData, rollNumber: e.target.value })}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Leave Type
              </label>
              <select
                value={formData.leaveType}
                onChange={(e) => setFormData({ ...formData, leaveType: e.target.value as LeaveType })}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="MEDICAL">Medical Emergency</option>
                <option value="ON_DUTY">On-Duty Official</option>
                <option value="SPORTS">Sports Championship</option>
                <option value="ACADEMIC">Academic Conference</option>
                <option value="CASUAL">Personal / Casual</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Start Date
              </label>
              <input
                type="date"
                required
                value={formData.startDate}
                onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                End Date
              </label>
              <input
                type="date"
                required
                value={formData.endDate}
                onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Detailed Reason / Event Description
            </label>
            <textarea
              required
              rows={3}
              value={formData.reason}
              onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
              placeholder="e.g. Hospitalized with dengue fever at Apollo Hospitals; medical certificate verified by medical officer."
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Supporting Document (Optional filename)
            </label>
            <input
              type="text"
              value={formData.supportingDocName}
              onChange={(e) => setFormData({ ...formData, supportingDocName: e.target.value })}
              placeholder="Medical_Certificate_Oct26.pdf"
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={submitting}>
              {submitting ? "Submitting..." : "Submit Application"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Review Leave Modal */}
      <Dialog
        open={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        title="Leave Request Review & Sign-off"
      >
        <form onSubmit={handleReviewLeave} className="space-y-4 text-xs">
          {selectedLeave && (
            <div className="rounded-lg bg-slate-50 p-3 border border-slate-200 dark:bg-slate-800 dark:border-slate-700 space-y-2">
              <div className="flex justify-between">
                <span className="font-semibold text-slate-900 dark:text-white">{selectedLeave.studentName}</span>
                <span className="text-slate-500">{selectedLeave.rollNumber}</span>
              </div>
              <div className="text-slate-600 dark:text-slate-400">
                <strong>Type: </strong>{selectedLeave.leaveType} • <strong>Duration: </strong>{selectedLeave.startDate} to {selectedLeave.endDate} ({selectedLeave.totalDays} Days)
              </div>
              <div className="text-slate-700 dark:text-slate-300 pt-1 border-t border-slate-200 dark:border-slate-700">
                <strong>Reason: </strong>{selectedLeave.reason}
              </div>
              {selectedLeave.supportingDocName && (
                <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400 font-medium">
                  <FileText className="h-3.5 w-3.5" />
                  Attachment: {selectedLeave.supportingDocName}
                </div>
              )}
            </div>
          )}

          {selectedLeave?.status === "PENDING" && (
            <>
              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Review Decision
                </label>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-2 cursor-pointer font-medium text-emerald-700">
                    <input
                      type="radio"
                      name="decision"
                      value="APPROVED"
                      checked={reviewAction === "APPROVED"}
                      onChange={() => setReviewAction("APPROVED")}
                    />
                    Approve Exemption
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer font-medium text-rose-700">
                    <input
                      type="radio"
                      name="decision"
                      value="REJECTED"
                      checked={reviewAction === "REJECTED"}
                      onChange={() => setReviewAction("REJECTED")}
                    />
                    Reject Application
                  </label>
                </div>
              </div>

              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Reviewer Notes / Feedback
                </label>
                <textarea
                  rows={2}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="e.g. Medical certificate verified with university medical officer."
                  className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setReviewModalOpen(false)}
                >
                  Close
                </Button>
                <Button
                  type="submit"
                  variant={reviewAction === "APPROVED" ? "primary" : "destructive"}
                  disabled={reviewing}
                >
                  {reviewing ? "Processing..." : `Confirm ${reviewAction}`}
                </Button>
              </div>
            </>
          )}

          {selectedLeave?.status !== "PENDING" && (
            <div className="pt-2 flex justify-end">
              <Button type="button" variant="outline" onClick={() => setReviewModalOpen(false)}>
                Close
              </Button>
            </div>
          )}
        </form>
      </Dialog>
    </div>
  );
}

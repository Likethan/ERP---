"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import {
  AttendanceLeave,
  AttendanceLeaveStatus,
  LeaveType,
} from "@/types/attendance";
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
  GraduationCap,
  Briefcase,
  ShieldCheck,
} from "lucide-react";

export default function LeaveManagementPage() {
  const { user, activePersona } = useAuth();
  const { showToast } = useToast();

  const userRole = (activePersona?.role ||
    user?.roles?.[0]?.name ||
    "STUDENT") as string;
  const isFaculty = userRole === "FACULTY";
  const isStudent = userRole === "STUDENT";
  const isHOD =
    userRole === "HOD" ||
    userRole === "PRINCIPAL" ||
    userRole === "SUPER_ADMIN" ||
    userRole === "ADMIN";

  const [loading, setLoading] = useState(true);
  const [leaves, setLeaves] = useState<AttendanceLeave[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [categoryFilter, setCategoryFilter] = useState<
    "ALL" | "STUDENT" | "FACULTY"
  >("ALL");

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
    applicantType: "STUDENT" as "STUDENT" | "FACULTY",
  });

  // Review Modal
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedLeave, setSelectedLeave] = useState<AttendanceLeave | null>(
    null,
  );
  const [reviewAction, setReviewAction] = useState<"APPROVED" | "REJECTED">(
    "APPROVED",
  );
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const loadLeaves = async () => {
    try {
      setLoading(true);
      const res = await attendanceService.getLeaves({
        status: statusFilter !== "ALL" ? statusFilter : undefined,
        applicantType: categoryFilter !== "ALL" ? categoryFilter : undefined,
      });
      if (res.success) {
        setLeaves(res.data);
      }
    } catch (err) {
      console.error("Failed to load leaves", err);
      showToast({
        type: "error",
        title: "Load Error",
        message: "Failed to load leave requests.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeaves();
  }, [statusFilter, categoryFilter]);

  const handleOpenCreateModal = () => {
    if (isFaculty) {
      setFormData({
        studentName: activePersona?.name || "Dr. Rajesh Sharma",
        rollNumber: "EMP-CSE-01",
        department:
          activePersona?.department || "Computer Science & Engineering",
        section: "Faculty Staff",
        leaveType: "CASUAL",
        startDate: new Date().toISOString().split("T")[0],
        endDate: new Date().toISOString().split("T")[0],
        totalDays: 1,
        reason: "",
        supportingDocName: "",
        applicantType: "FACULTY",
      });
    } else if (isStudent) {
      setFormData({
        studentName: activePersona?.name || "Aarav Patel",
        rollNumber: "24CSE0101",
        department: "Computer Science & Engineering",
        section: "A",
        leaveType: "MEDICAL",
        startDate: new Date().toISOString().split("T")[0],
        endDate: new Date().toISOString().split("T")[0],
        totalDays: 1,
        reason: "",
        supportingDocName: "",
        applicantType: "STUDENT",
      });
    } else {
      setFormData({
        studentName: activePersona?.name || "Dr. K. S. Anand",
        rollNumber: "HOD-CSE-01",
        department:
          activePersona?.department || "Computer Science & Engineering",
        section: "Department Head",
        leaveType: "CASUAL",
        startDate: new Date().toISOString().split("T")[0],
        endDate: new Date().toISOString().split("T")[0],
        totalDays: 1,
        reason: "",
        supportingDocName: "",
        applicantType: "FACULTY",
      });
    }
    setCreateModalOpen(true);
  };

  const handleCreateLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const res = await attendanceService.submitLeave(formData);
      if (res.success) {
        const dest =
          formData.applicantType === "FACULTY"
            ? "Submitted to HOD (Dr. K. S. Anand) for departmental endorsement."
            : "Submitted to Course Faculty for attendance exemption approval.";

        showToast({
          type: "success",
          title: "Leave Application Submitted",
          message: dest,
        });
        setCreateModalOpen(false);
        setFormData({ ...formData, reason: "", supportingDocName: "" });
        await loadLeaves();
      }
    } catch (err) {
      console.error("Failed to submit leave", err);
      showToast({
        type: "error",
        title: "Submission Failed",
        message: "Could not submit leave request.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReviewLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLeave) return;
    try {
      setReviewing(true);
      const isTargetFacultyLeave = selectedLeave.applicantType === "FACULTY";
      const reviewerSignature = isTargetFacultyLeave
        ? `${activePersona?.name || "Dr. K. S. Anand"} (HOD - CSE)`
        : `${activePersona?.name || "Dr. Rajesh Sharma"} (Faculty - CSE)`;

      const res = await attendanceService.updateLeaveStatus(
        selectedLeave.id,
        reviewAction,
        reviewNotes,
        reviewerSignature,
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
      showToast({
        type: "error",
        title: "Update Failed",
        message: "Could not update leave status.",
      });
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
        id: "applicant",
        header: "Applicant Name & ID",
        cell: (row) => {
          const isFac = row.applicantType === "FACULTY";
          return (
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-slate-900 dark:text-white">
                  {row.studentName}
                </span>
                {isFac ? (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300">
                    FACULTY
                  </span>
                ) : (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
                    STUDENT
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                {row.rollNumber} •{" "}
                {isFac ? row.department : `Sec ${row.section}`}
              </div>
            </div>
          );
        },
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
        header: "Approval & Routing",
        cell: (row) => {
          const isFac = row.applicantType === "FACULTY";
          return (
            <div className="text-xs text-slate-600 dark:text-slate-400">
              {row.reviewedBy ? (
                <div>
                  <div className="font-medium text-slate-800 dark:text-slate-200">
                    {row.reviewedBy}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {new Date(row.reviewedAt || "").toLocaleDateString()}
                  </div>
                </div>
              ) : (
                <span className="text-amber-600 dark:text-amber-400 font-medium">
                  {isFac
                    ? "Awaiting HOD sign-off"
                    : "Awaiting Faculty sign-off"}
                </span>
              )}
            </div>
          );
        },
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => {
          const isFacLeave = row.applicantType === "FACULTY";
          // Faculty can review Student leaves; HOD can review Faculty and Student leaves
          const canReview =
            row.status === "PENDING" &&
            ((isFaculty && !isFacLeave) || (isHOD && isFacLeave) || isHOD);

          return (
            <div className="flex items-center gap-2">
              {canReview && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => {
                    setSelectedLeave(row);
                    setReviewAction("APPROVED");
                    setReviewModalOpen(true);
                  }}
                  className="h-7 text-xs"
                >
                  {isFacLeave
                    ? "Endorse Faculty Leave"
                    : "Approve Student Leave"}
                </Button>
              )}
              {!canReview && (
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
          );
        },
      },
    ],
    [isFaculty, isHOD],
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
              {isFaculty
                ? "Faculty Portal • Leave Operations"
                : isStudent
                  ? "Student Portal • Leave Exemption"
                  : "Department Governance • Leave Endorsements"}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {isFaculty
                ? "Student Approvals & HOD Submissions"
                : isStudent
                  ? "Excused Absence Workflow"
                  : "Academic & Staff Leave Registry"}
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {isFaculty
              ? "Faculty Leave & Student Approvals"
              : isStudent
                ? "Student Leave Application"
                : "Department Leave Endorsements & Governance"}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {isFaculty
              ? "Review student absence applications for your courses and apply for faculty leave to the HOD."
              : isStudent
                ? "Submit medical, sports, and official on-duty leave applications to your course faculty for attendance exemption."
                : "Review and endorse departmental faculty leave applications and student attendance escalations."}
          </p>
        </div>

        <Button
          variant="primary"
          className="gap-2"
          onClick={handleOpenCreateModal}
        >
          <Plus className="h-4 w-4" />
          {isFaculty ? "Apply for Faculty Leave (to HOD)" : "Apply for Leave"}
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-slate-500 font-medium">
            <Filter className="h-3.5 w-3.5" />
            Category:
          </div>
          <div className="flex items-center gap-1 bg-white p-0.5 rounded-lg border border-slate-200 dark:bg-slate-800 dark:border-slate-700">
            <button
              type="button"
              onClick={() => setCategoryFilter("ALL")}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                categoryFilter === "ALL"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900"
              }`}
            >
              All Records ({leaves.length})
            </button>
            <button
              type="button"
              onClick={() => setCategoryFilter("STUDENT")}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                categoryFilter === "STUDENT"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900"
              }`}
            >
              Student Leaves
            </button>
            <button
              type="button"
              onClick={() => setCategoryFilter("FACULTY")}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                categoryFilter === "FACULTY"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900"
              }`}
            >
              Faculty Leaves (to HOD)
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-500 font-medium">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending Review</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<AttendanceLeave>
        data={leaves}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search leaves by applicant name, roll / employee code, or reason..."
        emptyTitle="No leave requests found"
        emptyDescription="Submit a new application or adjust status filters."
      />

      {/* Apply Leave Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title={
          isFaculty
            ? "Submit Faculty Leave Application (to HOD)"
            : "Submit Excused Leave Application"
        }
      >
        <form onSubmit={handleCreateLeave} className="space-y-4 text-xs">
          <div className="p-2.5 rounded-lg bg-blue-50/80 border border-blue-200 text-blue-900 dark:bg-blue-950/40 dark:border-blue-800 dark:text-blue-300">
            {isFaculty ? (
              <span>
                <strong>Routing Note: </strong>This application will be
                forwarded directly to{" "}
                <strong>Dr. K. S. Anand (HOD - CSE)</strong> for departmental
                sanction and workload arrangement.
              </span>
            ) : (
              <span>
                <strong>Routing Note: </strong>Approved leaves are counted as
                valid attendance percentage exemptions and sent to your Course
                Faculty.
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                {isFaculty ? "Faculty Name" : "Student Name"}
              </label>
              <input
                type="text"
                required
                value={formData.studentName}
                onChange={(e) =>
                  setFormData({ ...formData, studentName: e.target.value })
                }
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                {isFaculty ? "Employee Code / ID" : "Roll Number"}
              </label>
              <input
                type="text"
                required
                value={formData.rollNumber}
                onChange={(e) =>
                  setFormData({ ...formData, rollNumber: e.target.value })
                }
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
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    leaveType: e.target.value as LeaveType,
                  })
                }
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="CASUAL">Personal / Casual</option>
                <option value="MEDICAL">Medical Emergency</option>
                <option value="ON_DUTY">On-Duty Official</option>
                <option value="ACADEMIC">Academic / Conference</option>
                <option value="SPORTS">Sports Championship</option>
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
                onChange={(e) =>
                  setFormData({ ...formData, startDate: e.target.value })
                }
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
                onChange={(e) =>
                  setFormData({ ...formData, endDate: e.target.value })
                }
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
              onChange={(e) =>
                setFormData({ ...formData, reason: e.target.value })
              }
              placeholder={
                isFaculty
                  ? "e.g. Attending NBA accreditation workshop at Anna University; lecture sessions rescheduled to Saturday."
                  : "e.g. Hospitalized with viral fever at Apollo Hospitals; medical certificate verified."
              }
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Supporting Document (Optional attachment name)
            </label>
            <input
              type="text"
              value={formData.supportingDocName}
              onChange={(e) =>
                setFormData({ ...formData, supportingDocName: e.target.value })
              }
              placeholder={
                isFaculty
                  ? "Workshop_Invite_Nov26.pdf"
                  : "Medical_Certificate_Oct26.pdf"
              }
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
              {submitting
                ? "Submitting..."
                : isFaculty
                  ? "Submit Application to HOD"
                  : "Submit Application"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Review Leave Modal */}
      <Dialog
        open={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        title="Leave Request Review & Endorsement"
      >
        <form onSubmit={handleReviewLeave} className="space-y-4 text-xs">
          {selectedLeave && (
            <div className="rounded-lg bg-slate-50 p-3 border border-slate-200 dark:bg-slate-800 dark:border-slate-700 space-y-2">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900 dark:text-white text-sm">
                    {selectedLeave.studentName}
                  </span>
                  {selectedLeave.applicantType === "FACULTY" ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300">
                      FACULTY LEAVE
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
                      STUDENT LEAVE
                    </span>
                  )}
                </div>
                <span className="text-slate-500 font-mono">
                  {selectedLeave.rollNumber}
                </span>
              </div>
              <div className="text-slate-600 dark:text-slate-400">
                <strong>Type: </strong>
                {selectedLeave.leaveType} • <strong>Duration: </strong>
                {selectedLeave.startDate} to {selectedLeave.endDate} (
                {selectedLeave.totalDays} Days)
              </div>
              <div className="text-slate-700 dark:text-slate-300 pt-1 border-t border-slate-200 dark:border-slate-700">
                <strong>Reason: </strong>
                {selectedLeave.reason}
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
                  placeholder={
                    selectedLeave?.applicantType === "FACULTY"
                      ? "e.g. Approved by HOD. Substitute lectures confirmed."
                      : "e.g. Medical certificate verified with university medical officer."
                  }
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
                  variant={
                    reviewAction === "APPROVED" ? "primary" : "destructive"
                  }
                  disabled={reviewing}
                >
                  {reviewing ? "Processing..." : `Confirm ${reviewAction}`}
                </Button>
              </div>
            </>
          )}

          {selectedLeave?.status !== "PENDING" && (
            <div className="pt-2 flex justify-end">
              <Button
                type="button"
                variant="outline"
                onClick={() => setReviewModalOpen(false)}
              >
                Close
              </Button>
            </div>
          )}
        </form>
      </Dialog>
    </div>
  );
}

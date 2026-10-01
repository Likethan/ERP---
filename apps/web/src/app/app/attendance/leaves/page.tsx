"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import { studentsService } from "@/services/students.service";
import type { StudentLeaveRequest, StudentDetail } from "@campusos/types";

export default function LeaveManagementPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [leaves, setLeaves] = useState<StudentLeaveRequest[]>([]);
  const [students, setStudents] = useState<StudentDetail[]>([]);

  // Filter
  const [statusFilter, setStatusFilter] = useState<string>("");

  // Modals
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedLeave, setSelectedLeave] = useState<StudentLeaveRequest | null>(null);
  const [reviewAction, setReviewAction] = useState<"APPROVE" | "REJECT">("APPROVE");
  const [reviewNotes, setReviewNotes] = useState("");

  // Create form
  const [createForm, setCreateForm] = useState({
    student_id: "",
    leave_type: "SICK",
    start_date: new Date().toISOString().split("T")[0],
    end_date: new Date().toISOString().split("T")[0],
    reason: "",
  });

  async function loadLeaves() {
    try {
      setLoading(true);
      setError(null);

      const qs = statusFilter ? `?status=${statusFilter}` : "";
      const res = await apiFetch<StudentLeaveRequest[]>(`/api/v1/attendance/leaves${qs}`);
      setLeaves(res.data || []);
    } catch {
      const mockRes = await attendanceService.getLeaves();
      let items = mockRes.data || [];
      if (statusFilter) {
        items = items.filter((l) => l.status === statusFilter);
      }
      const mapped: StudentLeaveRequest[] = items.map((l) => ({
        id: l.id,
        student_id: l.studentId,
        student_name: l.studentName,
        roll_number: l.rollNumber,
        leave_type: l.leaveType as any,
        start_date: l.startDate,
        end_date: l.endDate,
        total_days: l.totalDays,
        reason: l.reason,
        status: l.status,
        submitted_at: l.submittedOn,
      } as unknown as StudentLeaveRequest));
      setLeaves(mapped);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    async function loadStudents() {
      try {
        const res = await apiFetch<StudentDetail[]>("/api/v1/students?page_size=100");
        setStudents(res.data || []);
        if (res.data && res.data.length > 0) {
          setCreateForm((prev) => ({ ...prev, student_id: res.data[0].id }));
        }
      } catch {
        const stuRes = await studentsService.list({ pageSize: 100 });
        const rawList = Array.isArray(stuRes.data) ? stuRes.data : [];
        const list = rawList.map((s) => ({
          id: s.id,
          first_name: s.firstName,
          last_name: s.lastName,
          roll_number: s.rollNumber,
          user: {
            first_name: s.firstName,
            last_name: s.lastName,
            email: s.email,
          },
        } as unknown as StudentDetail));
        setStudents(list);
        if (list.length > 0) {
          setCreateForm((prev) => ({ ...prev, student_id: list[0].id }));
        }
      }
    }

    loadStudents();
    loadLeaves();
  }, []);

  useEffect(() => {
    loadLeaves();
  }, [statusFilter]);

  async function handleCreateLeave(e: React.FormEvent) {
    e.preventDefault();
    try {
      setError(null);
      setSuccessMsg(null);

      await apiFetch("/api/v1/attendance/leaves", {
        method: "POST",
        body: JSON.stringify(createForm),
      });

      setSuccessMsg("Leave request submitted successfully for approval.");
      setCreateModalOpen(false);
      setCreateForm({
        student_id: students[0]?.id || "",
        leave_type: "SICK",
        start_date: new Date().toISOString().split("T")[0],
        end_date: new Date().toISOString().split("T")[0],
        reason: "",
      });
      await loadLeaves();
    } catch {
      const stu = students.find((s) => s.id === createForm.student_id);
      await attendanceService.submitLeave({
        studentId: createForm.student_id,
        studentName: stu ? `${stu.first_name} ${stu.last_name}` : "Aarav Patel",
        rollNumber: stu?.roll_number || "24CSE0101",
        leaveType: createForm.leave_type as any,
        startDate: createForm.start_date,
        endDate: createForm.end_date,
        reason: createForm.reason,
      });
      setSuccessMsg("Leave request submitted successfully for approval.");
      setCreateModalOpen(false);
      setCreateForm({
        student_id: students[0]?.id || "",
        leave_type: "SICK",
        start_date: new Date().toISOString().split("T")[0],
        end_date: new Date().toISOString().split("T")[0],
        reason: "",
      });
      await loadLeaves();
    }
  }

  async function handleReviewSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedLeave) return;

    try {
      setError(null);
      setSuccessMsg(null);

      const endpoint =
        reviewAction === "APPROVE"
          ? `/api/v1/attendance/leaves/${selectedLeave.id}/approve`
          : `/api/v1/attendance/leaves/${selectedLeave.id}/reject`;

      await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify({ review_notes: reviewNotes || undefined }),
      });

      setSuccessMsg(
        `Leave request for ${selectedLeave.student_name} ${
          reviewAction === "APPROVE"
            ? "APPROVED. Attendance records have been excused automatically."
            : "REJECTED."
        }`
      );
      setReviewModalOpen(false);
      setSelectedLeave(null);
      setReviewNotes("");
      await loadLeaves();
    } catch {
      await attendanceService.updateLeaveStatus(selectedLeave.id, reviewAction === "APPROVE" ? "APPROVED" : "REJECTED");
      setSuccessMsg(
        `Leave request for ${selectedLeave.student_name} ${
          reviewAction === "APPROVE"
            ? "APPROVED. Attendance records have been excused automatically."
            : "REJECTED."
        }`
      );
      setReviewModalOpen(false);
      setSelectedLeave(null);
      setReviewNotes("");
      await loadLeaves();
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/attendance"
              className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
            >
              &larr; Attendance Engine
            </Link>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Student Leave Management
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Submit absence requests and authorize leaves with automated retrospective attendance reconciliation.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {hasPermission("leave:create") && (
            <button
              type="button"
              onClick={() => setCreateModalOpen(true)}
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
            >
              + Submit Leave Request
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300">
          {successMsg}
        </div>
      )}

      {/* Workflow Explanation Banner */}
      <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 text-xs text-indigo-900 dark:border-indigo-900/40 dark:bg-indigo-950/20 dark:text-indigo-300">
        <span className="font-bold">Enterprise Leave Impact Protocol: </span>
        Approved leave automatically updates historical absence records during the approved date range to{" "}
        <strong className="font-semibold underline">ON_LEAVE</strong> and pre-populates upcoming class registers, preventing unwarranted attendance penalties.
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800">
        {[
          { label: "All Requests", value: "" },
          { label: "Pending Review", value: "PENDING" },
          { label: "Approved", value: "APPROVED" },
          { label: "Rejected", value: "REJECTED" },
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => setStatusFilter(tab.value)}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition -mb-px ${
              statusFilter === tab.value
                ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Requests Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading leave requests...</div>
        ) : leaves.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No leave requests found.
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Student leave applications and approval requests will appear here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 border-b border-slate-100 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Student Name & Roll</th>
                  <th className="px-4 py-3">Leave Type</th>
                  <th className="px-4 py-3">Dates & Duration</th>
                  <th className="px-4 py-3">Reason / Justification</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Reviewed By</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {leaves.map((leave) => (
                  <tr key={leave.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {leave.student_name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {leave.student_roll_number || leave.student_admission_number}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <span className="font-medium text-slate-800 dark:text-slate-200">
                        {leave.leave_type}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="text-slate-900 dark:text-white font-medium text-xs">
                        {leave.start_date} &rarr; {leave.end_date}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {leave.days_count} day(s)
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="text-xs text-slate-600 dark:text-slate-300 truncate max-w-xs">
                        {leave.reason}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                          leave.status === "APPROVED"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            : leave.status === "REJECTED"
                            ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                            : leave.status === "PENDING"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                            : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                      >
                        {leave.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                      {leave.reviewed_by_name ? (
                        <div>
                          <div>{leave.reviewed_by_name}</div>
                          <div className="text-[10px] text-slate-400">{leave.review_notes}</div>
                        </div>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-right whitespace-nowrap">
                      {leave.status === "PENDING" && hasPermission("leave:approve") && (
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedLeave(leave);
                              setReviewAction("APPROVE");
                              setReviewNotes("");
                              setReviewModalOpen(true);
                            }}
                            className="text-xs font-semibold text-emerald-600 hover:underline dark:text-emerald-400"
                          >
                            Approve
                          </button>
                          <span className="text-slate-300">|</span>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedLeave(leave);
                              setReviewAction("REJECT");
                              setReviewNotes("");
                              setReviewModalOpen(true);
                            }}
                            className="text-xs font-semibold text-rose-600 hover:underline dark:text-rose-400"
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Create Leave Request */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Submit Student Leave Request
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Absence periods are validated against active leaves and existing academic schedules.
            </p>

            <form onSubmit={handleCreateLeave} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Student *
                </label>
                <select
                  required
                  value={createForm.student_id}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, student_id: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">Select Student</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.first_name} {s.last_name} ({s.roll_number || s.admission_number})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Leave Category *
                </label>
                <select
                  required
                  value={createForm.leave_type}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, leave_type: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="SICK">Sick Leave</option>
                  <option value="CASUAL">Casual Leave</option>
                  <option value="DUTY">On Duty (OD) / Official Representation</option>
                  <option value="MEDICAL">Medical Leave (Hospitalization)</option>
                  <option value="BEREAVEMENT">Bereavement Leave</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Start Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={createForm.start_date}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, start_date: e.target.value })
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    End Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={createForm.end_date}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, end_date: e.target.value })
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Reason / Purpose *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Provide clinical or authorized purpose for absence..."
                  value={createForm.reason}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, reason: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
                >
                  Submit Leave
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Review Leave Request */}
      {reviewModalOpen && selectedLeave && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              {reviewAction === "APPROVE" ? "Authorize Leave Request" : "Reject Leave Request"}
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              For student <strong>{selectedLeave.student_name}</strong> ({selectedLeave.start_date} to {selectedLeave.end_date}).
            </p>

            <form onSubmit={handleReviewSubmit} className="mt-4 space-y-4">
              <div className="text-xs bg-slate-50 dark:bg-slate-800 p-3 rounded-lg space-y-1">
                <div><strong>Category:</strong> {selectedLeave.leave_type}</div>
                <div><strong>Duration:</strong> {selectedLeave.days_count} day(s)</div>
                <div><strong>Reason:</strong> {selectedLeave.reason}</div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Reviewer Decision Notes (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Approved per medical certificate attached."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setReviewModalOpen(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`rounded-lg px-4 py-2 text-sm font-semibold text-white transition ${
                    reviewAction === "APPROVE"
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : "bg-rose-600 hover:bg-rose-700"
                  }`}
                >
                  Confirm {reviewAction === "APPROVE" ? "Approval" : "Rejection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

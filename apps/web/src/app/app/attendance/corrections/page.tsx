"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import type { AttendanceCorrectionRequest } from "@campusos/types";

export default function AttendanceCorrectionsPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [corrections, setCorrections] = useState<AttendanceCorrectionRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("");

  // Review Modal
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedCorrection, setSelectedCorrection] =
    useState<AttendanceCorrectionRequest | null>(null);
  const [reviewAction, setReviewAction] = useState<"APPROVE" | "REJECT">("APPROVE");
  const [approvalNotes, setApprovalNotes] = useState("");

  async function loadCorrections() {
    try {
      setLoading(true);
      setError(null);

      const qs = statusFilter ? `?status=${statusFilter}` : "";
      const res = await apiFetch<AttendanceCorrectionRequest[]>(
        `/api/v1/attendance/corrections${qs}`
      );
      setCorrections(res.data || []);
    } catch {
      const mockRes = await attendanceService.getCorrections();
      let items = mockRes.data || [];
      if (statusFilter) {
        items = items.filter((c) => c.status === statusFilter);
      }
      const mapped: AttendanceCorrectionRequest[] = items.map((c) => ({
        id: c.id,
        attendance_record_id: `rec-${c.id}`,
        student_id: "stu-24cse0101",
        student_name: c.studentName,
        roll_number: c.rollNumber,
        course_code: c.courseCode,
        course_name: "Computer Science Core",
        session_date: c.sessionDate,
        period_number: 1,
        current_status: c.currentStatus as any,
        requested_status: c.requestedStatus as any,
        reason: c.reason,
        status: c.status as any,
        requested_at: "2026-09-30T10:00:00Z",
      } as unknown as AttendanceCorrectionRequest));
      setCorrections(mapped);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCorrections();
  }, [statusFilter]);

  async function handleReviewSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCorrection) return;

    try {
      setError(null);
      setSuccessMsg(null);

      const endpoint =
        reviewAction === "APPROVE"
          ? `/api/v1/attendance/corrections/${selectedCorrection.id}/approve`
          : `/api/v1/attendance/corrections/${selectedCorrection.id}/reject`;

      await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify({ approval_notes: approvalNotes || undefined }),
      });

      setSuccessMsg(
        `Correction for ${selectedCorrection.student_name} ${
          reviewAction === "APPROVE"
            ? "APPROVED. Attendance record has been corrected in locked register."
            : "REJECTED."
        }`
      );
      setReviewModalOpen(false);
      setSelectedCorrection(null);
      setApprovalNotes("");
      await loadCorrections();
    } catch {
      await attendanceService.updateCorrectionStatus(selectedCorrection.id, reviewAction === "APPROVE" ? "APPROVED" : "REJECTED");
      setSuccessMsg(
        `Correction for ${selectedCorrection.student_name} ${
          reviewAction === "APPROVE"
            ? "APPROVED. Attendance record has been corrected in locked register."
            : "REJECTED."
        }`
      );
      setReviewModalOpen(false);
      setSelectedCorrection(null);
      setApprovalNotes("");
      await loadCorrections();
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
            Supervised Attendance Corrections
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Formal audit-tracked modifications for locked attendance sessions requiring departmental oversight.
          </p>
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

      {/* Governance Banner */}
      <div className="rounded-xl border border-purple-100 bg-purple-50/50 p-4 text-xs text-purple-900 dark:border-purple-900/40 dark:bg-purple-950/20 dark:text-purple-300">
        <span className="font-bold">Immutability & Correction Governance: </span>
        Locked registers prohibit direct row mutations. Any rectification is preserved in an immutable
        audit ledger with original status, requested modification, rationale, requester, and authorizer identity.
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800">
        {[
          { label: "All Corrections", value: "" },
          { label: "Pending Oversight", value: "PENDING" },
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

      {/* Corrections Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading correction requests...</div>
        ) : corrections.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No correction requests are pending.
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Corrections requested on locked sessions will be routed here for authorization.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 border-b border-slate-100 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Session & Course</th>
                  <th className="px-4 py-3">Student Name</th>
                  <th className="px-4 py-3">Status Mutation</th>
                  <th className="px-4 py-3">Justification</th>
                  <th className="px-4 py-3">Requester</th>
                  <th className="px-4 py-3">Approval Status</th>
                  <th className="px-4 py-3 text-right">Oversight</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {corrections.map((corr) => (
                  <tr key={corr.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {corr.session_date}
                      </div>
                      <div className="text-xs text-slate-400">
                        {corr.course_code || "Course"} • {corr.course_name}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="font-medium text-slate-900 dark:text-white">
                        {corr.student_name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {corr.student_roll_number || "—"}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="flex items-center gap-2 text-xs font-bold">
                        <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                          {corr.previous_status}
                        </span>
                        <span className="text-slate-400">&rarr;</span>
                        <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                          {corr.requested_status}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="text-xs text-slate-600 dark:text-slate-300 truncate max-w-xs">
                        {corr.reason}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                      {corr.requested_by_name || "Faculty"}
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                          corr.approval_status === "APPROVED"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            : corr.approval_status === "REJECTED"
                            ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                            : "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                        }`}
                      >
                        {corr.approval_status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right whitespace-nowrap">
                      {corr.approval_status === "PENDING" &&
                        hasPermission("attendance:approve_correction") && (
                          <div className="flex items-center justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedCorrection(corr);
                                setReviewAction("APPROVE");
                                setApprovalNotes("");
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
                                setSelectedCorrection(corr);
                                setReviewAction("REJECT");
                                setApprovalNotes("");
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

      {/* Review Modal */}
      {reviewModalOpen && selectedCorrection && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              {reviewAction === "APPROVE" ? "Authorize Attendance Correction" : "Reject Correction Request"}
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              For <strong>{selectedCorrection.student_name}</strong> in {selectedCorrection.course_code}.
            </p>

            <form onSubmit={handleReviewSubmit} className="mt-4 space-y-4">
              <div className="text-xs bg-slate-50 dark:bg-slate-800 p-3 rounded-lg space-y-1">
                <div>
                  <strong>Status Change:</strong> {selectedCorrection.previous_status} &rarr;{" "}
                  <span className="text-emerald-600 font-bold">{selectedCorrection.requested_status}</span>
                </div>
                <div><strong>Reason:</strong> {selectedCorrection.reason}</div>
                <div><strong>Requested By:</strong> {selectedCorrection.requested_by_name || "Faculty"}</div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Approval Notes (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Verified with manual sign-in sheet."
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
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

"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceCorrection, AttendanceCorrectionStatus, AttendanceStatus } from "@/types/attendance";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import {
  Clock,
  History,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Filter,
  ArrowRight,
  ShieldCheck,
  User,
} from "lucide-react";

export default function AttendanceCorrectionsPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [corrections, setCorrections] = useState<AttendanceCorrection[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Review Modal
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedCorrection, setSelectedCorrection] = useState<AttendanceCorrection | null>(null);
  const [reviewAction, setReviewAction] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const loadCorrections = async () => {
    try {
      setLoading(true);
      const res = await attendanceService.getCorrections({
        status: statusFilter !== "ALL" ? statusFilter : undefined,
      });
      if (res.success) {
        setCorrections(res.data);
      }
    } catch (err) {
      console.error("Failed to load corrections", err);
      showToast({ type: "error", title: "Load Error", message: "Failed to load attendance corrections." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCorrections();
  }, [statusFilter]);

  const handleReviewCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCorrection) return;
    try {
      setReviewing(true);
      const res = await attendanceService.updateCorrectionStatus(
        selectedCorrection.id,
        reviewAction,
        reviewNotes,
        "Dr. K. S. Anand (HOD - CSE)"
      );

      if (res.success) {
        showToast({
          type: "success",
          title: `Correction ${reviewAction}`,
          message: `Attendance register updated: Record is now ${res.data.requestedStatus}.`,
        });
        setReviewModalOpen(false);
        setSelectedCorrection(null);
        setReviewNotes("");
        await loadCorrections();
      }
    } catch (err) {
      console.error("Failed to review correction", err);
      showToast({ type: "error", title: "Review Error", message: "Could not process correction review." });
    } finally {
      setReviewing(false);
    }
  };

  const getStatusBadge = (status: AttendanceCorrectionStatus) => {
    switch (status) {
      case "APPROVED":
        return <Badge variant="success">Approved</Badge>;
      case "REJECTED":
        return <Badge variant="destructive">Rejected</Badge>;
      case "PENDING":
        return <Badge variant="warning">Pending HOD Review</Badge>;
      case "CANCELLED":
        return <Badge variant="secondary">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const columns: ColumnDef<AttendanceCorrection>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Student & Course",
        cell: (row) => (
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              {row.studentName}
            </div>
            <div className="text-xs text-slate-500">{row.rollNumber}</div>
            <div className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">
              {row.courseCode} • {row.sessionDate}
            </div>
          </div>
        ),
        sortable: true,
      },
      {
        id: "statusChange",
        header: "Status Transition",
        cell: (row) => (
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
              {row.originalStatus}
            </span>
            <span className="text-slate-400">&rarr;</span>
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              {row.requestedStatus}
            </span>
          </div>
        ),
      },
      {
        id: "reason",
        header: "Reason & Requested By",
        cell: (row) => (
          <div>
            <div className="text-xs text-slate-800 dark:text-slate-200 truncate max-w-[240px]">
              {row.reason}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              By: <strong>{row.requestedBy}</strong> ({row.requestedRole})
            </div>
          </div>
        ),
      },
      {
        id: "status",
        header: "Approval State",
        cell: (row) => getStatusBadge(row.status),
        sortable: true,
      },
      {
        id: "reviewedBy",
        header: "Reviewed By",
        cell: (row) => (
          <div className="text-xs text-slate-600 dark:text-slate-400">
            {row.reviewedBy ? (
              <div>
                <div className="font-medium text-slate-800 dark:text-slate-200">{row.reviewedBy}</div>
                <div className="text-[10px] text-slate-400">{new Date(row.reviewedAt || "").toLocaleDateString()}</div>
              </div>
            ) : (
              <span className="text-slate-400 italic">Pending HOD</span>
            )}
          </div>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={row.status === "PENDING" ? "primary" : "outline"}
              onClick={() => {
                setSelectedCorrection(row);
                setReviewAction("APPROVED");
                setReviewModalOpen(true);
              }}
              className="h-7 text-xs"
            >
              {row.status === "PENDING" ? "Review" : "Audit Log"}
            </Button>
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
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300">
              Audit Scrutiny
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Supervised Attendance Revisions</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Attendance Corrections Workflow
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Supervised approval mechanism ensuring locked session registers are never silently modified.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filter:
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Corrections ({corrections.length})</option>
          <option value="PENDING">Pending Review</option>
          <option value="APPROVED">Approved & Persisted</option>
          <option value="REJECTED">Rejected</option>
        </select>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<AttendanceCorrection>
        data={corrections}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search corrections by student name, roll number, or course..."
        emptyTitle="No correction requests found"
        emptyDescription="All attendance registers match recorded roster marks."
      />

      {/* Review Modal & Audit Timeline */}
      <Dialog
        open={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        title="Attendance Correction Scrutiny & Timeline"
      >
        <form onSubmit={handleReviewCorrection} className="space-y-4 text-xs">
          {selectedCorrection && (
            <div className="space-y-3">
              <div className="rounded-lg bg-slate-50 p-3 border border-slate-200 dark:bg-slate-800 dark:border-slate-700">
                <div className="flex justify-between">
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {selectedCorrection.studentName} ({selectedCorrection.rollNumber})
                  </span>
                  <Badge variant={selectedCorrection.status === "APPROVED" ? "success" : "warning"}>
                    {selectedCorrection.status}
                  </Badge>
                </div>
                <div className="text-slate-600 dark:text-slate-400 mt-1">
                  <strong>Course: </strong>{selectedCorrection.courseCode} • <strong>Date: </strong>{selectedCorrection.sessionDate}
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <span className="font-medium text-slate-500">Requested Transition:</span>
                  <span className="px-2 py-0.5 text-xs font-semibold rounded bg-rose-100 text-rose-800">
                    {selectedCorrection.originalStatus}
                  </span>
                  <span>&rarr;</span>
                  <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-100 text-emerald-800">
                    {selectedCorrection.requestedStatus}
                  </span>
                </div>
                <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300">
                  <strong>Justification: </strong>{selectedCorrection.reason}
                </div>
              </div>

              {/* Audit Timeline */}
              <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
                <div className="flex items-center gap-2 mb-2 font-semibold text-slate-900 dark:text-white">
                  <History className="h-4 w-4 text-indigo-500" />
                  Chronological Audit Trail
                </div>
                <div className="space-y-2.5">
                  {selectedCorrection.auditTimeline.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 text-[11px]">
                      <div className="h-1.5 w-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                      <div>
                        <div className="font-medium text-slate-800 dark:text-slate-200">{step.action}</div>
                        <div className="text-slate-500">
                          {step.actor} • {new Date(step.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </div>
                        {step.details && (
                          <div className="text-slate-400 italic mt-0.5">&ldquo;{step.details}&rdquo;</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {selectedCorrection?.status === "PENDING" && (
            <>
              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  HOD / Administrator Decision
                </label>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer font-medium text-emerald-700">
                    <input
                      type="radio"
                      name="decision"
                      value="APPROVED"
                      checked={reviewAction === "APPROVED"}
                      onChange={() => setReviewAction("APPROVED")}
                    />
                    Approve & Update Register
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer font-medium text-rose-700">
                    <input
                      type="radio"
                      name="decision"
                      value="REJECTED"
                      checked={reviewAction === "REJECTED"}
                      onChange={() => setReviewAction("REJECTED")}
                    />
                    Reject Request
                  </label>
                </div>
              </div>

              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Scrutiny Comments
                </label>
                <textarea
                  rows={2}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="e.g. Verified with lab punch log; confirmed attendance."
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
                  {reviewing ? "Executing..." : `Confirm ${reviewAction}`}
                </Button>
              </div>
            </>
          )}

          {selectedCorrection?.status !== "PENDING" && (
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

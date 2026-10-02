"use client";

import React, { useEffect, useState, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import {
  Assessment,
  Mark,
  MarkStatus,
} from "@/types/examinations";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  FileSpreadsheet,
  Save,
  Lock,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  UserX,
  History,
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";

function MarksEntryRosterContent() {
  const { hasPermission } = useAuth();
  const searchParams = useSearchParams();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  // Aux state
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>(
    searchParams.get("assessment_id") || "asm-cs301-internal"
  );

  // Local Editable Marks Roster
  const [marks, setMarks] = useState<Mark[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Finalization Modal State
  const [finalizeModalOpen, setFinalizeModalOpen] = useState(false);
  const [finalizing, setFinalizing] = useState(false);

  // Correction Modal State
  const [correctionModalOpen, setCorrectionModalOpen] = useState(false);
  const [selectedMarkForCorrection, setSelectedMarkForCorrection] = useState<Mark | null>(null);
  const [newScore, setNewScore] = useState<number | "">("");
  const [newStatus, setNewStatus] = useState<MarkStatus>("ENTERED");
  const [correctionReason, setCorrectionReason] = useState("");
  const [submittingCorrection, setSubmittingCorrection] = useState(false);

  const selectedAssessment = assessments.find((a) => a.id === selectedAssessmentId);

  const loadData = async () => {
    try {
      setLoading(true);
      const [asmRes, marksRes] = await Promise.all([
        examinationsService.getAssessments(),
        examinationsService.getMarks(selectedAssessmentId),
      ]);
      setAssessments(asmRes.data);
      setMarks(marksRes.data);
      setIsDirty(false);
    } catch {
      showToast({ title: "Error", message: "Failed to load marks roster", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedAssessmentId]);

  // Handle in-line score change
  const handleScoreChange = (markId: string, val: string) => {
    if (selectedAssessment?.isFinalized) return;

    setIsDirty(true);
    setMarks((prev) =>
      prev.map((m) => {
        if (m.id === markId) {
          if (val === "") {
            return { ...m, marksObtained: null, status: "NOT_ENTERED" };
          }
          const numeric = Number(val);
          return {
            ...m,
            marksObtained: numeric,
            status: "ENTERED",
            isAbsent: false,
          };
        }
        return m;
      })
    );
  };

  // Quick mark status toggle (Absent, Malpractice, Clear)
  const handleQuickStatus = (markId: string, targetStatus: MarkStatus) => {
    if (selectedAssessment?.isFinalized) return;

    setIsDirty(true);
    setMarks((prev) =>
      prev.map((m) => {
        if (m.id === markId) {
          if (targetStatus === "ABSENT") {
            return { ...m, marksObtained: 0, status: "ABSENT", isAbsent: true };
          }
          if (targetStatus === "MALPRACTICE") {
            return { ...m, marksObtained: 0, status: "MALPRACTICE", isAbsent: false, remarks: "Incident reported to proctor" };
          }
          if (targetStatus === "NOT_ENTERED") {
            return { ...m, marksObtained: null, status: "NOT_ENTERED", isAbsent: false, remarks: "" };
          }
          return { ...m, status: targetStatus };
        }
        return m;
      })
    );
  };

  // Bulk quick action: Mark all unentered as Absent or Zero
  const handleMarkAllUnenteredAbsent = () => {
    if (selectedAssessment?.isFinalized) return;
    setIsDirty(true);
    setMarks((prev) =>
      prev.map((m) => {
        if (m.status === "NOT_ENTERED") {
          return { ...m, marksObtained: 0, status: "ABSENT", isAbsent: true };
        }
        return m;
      })
    );
  };

  // Discard local edits
  const handleDiscard = () => {
    loadData();
    setIsDirty(false);
    showToast({ title: "Discarded", message: "Reverted local marks modifications.", type: "info" });
  };

  // Save Marks Draft
  const handleSaveMarks = async () => {
    if (!selectedAssessment) return;

    // Check bounds validation
    const max = selectedAssessment.maxMarks;
    const invalid = marks.find(
      (m) => m.marksObtained !== null && (m.marksObtained < 0 || m.marksObtained > max)
    );

    if (invalid) {
      showToast({
        title: "Validation Violation",
        message: `Mark for ${invalid.studentName} must be between 0 and ${max}`,
        type: "error",
      });
      return;
    }

    try {
      setSaving(true);
      await examinationsService.saveMarks(
        selectedAssessment.id,
        marks.map((m) => ({
          studentId: m.studentId,
          marksObtained: m.marksObtained,
          status: m.status,
          remarks: m.remarks,
        }))
      );
      setIsDirty(false);
      showToast({ title: "Saved", message: "Marks roster saved successfully.", type: "success" });
    } catch (err: unknown) {
      showToast({
        title: "Save Failed",
        message: err instanceof Error ? err.message : "Error saving marks",
        type: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  // Submit Finalization
  const handleFinalizeRoster = async () => {
    if (!selectedAssessment) return;
    try {
      setFinalizing(true);
      await examinationsService.finalizeAssessment(selectedAssessment.id);
      showToast({ title: "Finalized", message: "Marks locked and finalized.", type: "success" });
      setFinalizeModalOpen(false);
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Finalization Blocked",
        message: err instanceof Error ? err.message : "Ensure all marks are entered.",
        type: "error",
      });
    } finally {
      setFinalizing(false);
    }
  };

  // Request Mark Correction
  const handleRequestCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMarkForCorrection) return;

    try {
      setSubmittingCorrection(true);
      await examinationsService.requestMarkCorrection({
        markId: selectedMarkForCorrection.id,
        requestedMark: newScore === "" ? null : Number(newScore),
        requestedStatus: newStatus,
        reason: correctionReason,
        requestedBy: selectedAssessment?.facultyName || "Faculty Instructor",
      });

      showToast({ title: "Submitted", message: "Correction request submitted for HOD review.", type: "success" });
      setCorrectionModalOpen(false);
      setCorrectionReason("");
    } catch (err: unknown) {
      showToast({
        title: "Error",
        message: err instanceof Error ? err.message : "Failed to request correction",
        type: "error",
      });
    } finally {
      setSubmittingCorrection(false);
    }
  };

  // Filtered marks
  const filteredMarks = useMemo(() => {
    return marks.filter((m) => {
      const matchSearch =
        m.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.rollNumber.toLowerCase().includes(searchQuery.toLowerCase());
      const matchStatus = statusFilter === "ALL" || m.status === statusFilter;
      return matchSearch && matchStatus;
    });
  }, [marks, searchQuery, statusFilter]);

  // Validation Summary Stats
  const enteredCount = marks.filter((m) => m.status === "ENTERED").length;
  const absentCount = marks.filter((m) => m.status === "ABSENT").length;
  const unenteredCount = marks.filter((m) => m.status === "NOT_ENTERED").length;
  const malpracticeCount = marks.filter((m) => m.status === "MALPRACTICE").length;
  const max = selectedAssessment?.maxMarks || 100;
  const invalidCount = marks.filter(
    (m) => m.marksObtained !== null && (m.marksObtained < 0 || m.marksObtained > max)
  ).length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300">
              Score Ledger
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Class Roster Marks Scoring</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Marks Entry & Grading Matrix
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Rapid numeric entry, non-numeric status flags (ABSENT, MALPRACTICE), draft auto-save, and locked finalization.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {isDirty && (
            <Button variant="outline" size="sm" onClick={handleDiscard} className="gap-1.5 text-xs">
              <RotateCcw className="h-3.5 w-3.5" />
              Discard
            </Button>
          )}

          {!selectedAssessment?.isFinalized && (
            <>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveMarks}
                disabled={saving || !isDirty}
                className="gap-1.5 text-xs"
              >
                <Save className="h-3.5 w-3.5" />
                {saving ? "Saving..." : "Save Draft"}
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setFinalizeModalOpen(true)}
                disabled={unenteredCount > 0 || invalidCount > 0}
                className="gap-1.5 text-xs bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900"
              >
                <Lock className="h-3.5 w-3.5" />
                Finalize Marks
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Unsaved Changes Banner */}
      {isDirty && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-3.5 flex items-center justify-between dark:border-amber-900/60 dark:bg-amber-950/40">
          <div className="flex items-center gap-2.5 text-xs text-amber-900 dark:text-amber-200">
            <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
            <span>
              <strong>Unsaved marks detected.</strong> Save your changes to avoid losing student scores.
            </span>
          </div>
          <Button size="sm" variant="primary" onClick={handleSaveMarks} disabled={saving} className="h-7 text-xs bg-amber-600 hover:bg-amber-700">
            Save Changes
          </Button>
        </div>
      )}

      {/* Course & Assessment Selector Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50/70 p-4 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div>
          <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Active Assessment Scheme:
          </label>
          <select
            value={selectedAssessmentId}
            onChange={(e) => setSelectedAssessmentId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            {assessments.map((a) => (
              <option key={a.id} value={a.id}>
                {a.courseCode} - {a.name} ({a.isFinalized ? "LOCKED" : a.status})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Course & Section Context:
          </label>
          <div className="p-2 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
            {selectedAssessment?.courseCode} - Section {selectedAssessment?.section} ({selectedAssessment?.facultyName})
          </div>
        </div>

        <div>
          <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Maximum & Passing Mark:
          </label>
          <div className="p-2 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-800 flex justify-between font-mono">
            <span>Max: <strong>{selectedAssessment?.maxMarks}</strong> pts</span>
            <span>Pass: <strong>{selectedAssessment?.passingMarks}</strong> pts</span>
            <span className="text-indigo-600 font-bold">Weight: {selectedAssessment?.weightage}%</span>
          </div>
        </div>
      </div>

      {/* Validation Summary Stat Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-3 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 text-center">
          <span className="text-[11px] text-slate-400">Total Enrolled</span>
          <p className="text-lg font-bold text-slate-900 dark:text-white">{marks.length}</p>
        </div>
        <div className="p-3 rounded-lg border border-emerald-200 bg-emerald-50/50 dark:border-emerald-950 dark:bg-emerald-950/20 text-center">
          <span className="text-[11px] text-emerald-600">Scored / Entered</span>
          <p className="text-lg font-bold text-emerald-700 dark:text-emerald-400">{enteredCount}</p>
        </div>
        <div className="p-3 rounded-lg border border-amber-200 bg-amber-50/50 dark:border-amber-950 dark:bg-amber-950/20 text-center">
          <span className="text-[11px] text-amber-600">Unentered</span>
          <p className="text-lg font-bold text-amber-700 dark:text-amber-400">{unenteredCount}</p>
        </div>
        <div className="p-3 rounded-lg border border-rose-200 bg-rose-50/50 dark:border-rose-950 dark:bg-rose-950/20 text-center">
          <span className="text-[11px] text-rose-600">Absent</span>
          <p className="text-lg font-bold text-rose-700 dark:text-rose-400">{absentCount}</p>
        </div>
        <div className="p-3 rounded-lg border border-purple-200 bg-purple-50/50 dark:border-purple-950 dark:bg-purple-950/20 text-center">
          <span className="text-[11px] text-purple-600">Validation Flags</span>
          <p className="text-lg font-bold text-purple-700 dark:text-purple-400">{invalidCount + malpracticeCount}</p>
        </div>
      </div>

      {/* Roster Controls: Search & Bulk Action Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="h-3.5 w-3.5 absolute left-2.5 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search student or roll number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-slate-300 bg-white text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <option value="ALL">All Statuses ({marks.length})</option>
            <option value="ENTERED">Entered</option>
            <option value="NOT_ENTERED">Not Entered</option>
            <option value="ABSENT">Absent</option>
            <option value="MALPRACTICE">Malpractice</option>
          </select>
        </div>

        {!selectedAssessment?.isFinalized && unenteredCount > 0 && (
          <Button
            size="sm"
            variant="outline"
            onClick={handleMarkAllUnenteredAbsent}
            className="text-xs h-8 gap-1.5 text-rose-600 hover:text-rose-700 hover:bg-rose-50"
          >
            <UserX className="h-3.5 w-3.5" />
            Mark Remaining ({unenteredCount}) as Absent
          </Button>
        )}
      </div>

      {/* High-Speed Editable Marks Matrix Table */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:border-slate-800 dark:bg-slate-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700 font-semibold">
              <tr>
                <th className="p-3 w-12">#</th>
                <th className="p-3">Roll Number</th>
                <th className="p-3">Student Name</th>
                <th className="p-3 w-32">Marks / {max}</th>
                <th className="p-3 w-36">Status</th>
                <th className="p-3">Quick Flags</th>
                <th className="p-3">Remarks / Reason</th>
                {selectedAssessment?.isFinalized && <th className="p-3 w-28">Supervised</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredMarks.map((m, idx) => {
                const isOutOfRange = m.marksObtained !== null && (m.marksObtained < 0 || m.marksObtained > max);
                return (
                  <tr
                    key={m.id}
                    className={`hover:bg-slate-50/70 dark:hover:bg-slate-800/40 ${
                      isOutOfRange ? "bg-rose-50/50 dark:bg-rose-950/20" : ""
                    }`}
                  >
                    <td className="p-3 font-mono text-slate-400">{idx + 1}</td>
                    <td className="p-3 font-mono font-medium text-slate-700 dark:text-slate-200">{m.rollNumber}</td>
                    <td className="p-3 font-semibold text-slate-900 dark:text-white">{m.studentName}</td>
                    <td className="p-3">
                      <input
                        type="number"
                        disabled={selectedAssessment?.isFinalized}
                        min={0}
                        max={max}
                        value={m.marksObtained !== null ? m.marksObtained : ""}
                        onChange={(e) => handleScoreChange(m.id, e.target.value)}
                        placeholder="—"
                        className={`w-24 px-2.5 py-1 text-xs rounded border font-mono font-bold focus:outline-none focus:ring-1 ${
                          isOutOfRange
                            ? "border-rose-500 bg-rose-50 text-rose-700"
                            : m.status === "ABSENT"
                            ? "border-slate-300 bg-slate-100 text-slate-400"
                            : "border-slate-300 bg-white text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                        }`}
                      />
                    </td>
                    <td className="p-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                          m.status === "ENTERED"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                            : m.status === "ABSENT"
                            ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                            : m.status === "MALPRACTICE"
                            ? "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300"
                            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                        }`}
                      >
                        {m.status}
                      </span>
                    </td>
                    <td className="p-3">
                      {!selectedAssessment?.isFinalized ? (
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleQuickStatus(m.id, "ABSENT")}
                            className="px-1.5 py-0.5 rounded border border-rose-200 text-rose-600 hover:bg-rose-50 text-[10px] font-medium"
                          >
                            Absent
                          </button>
                          <button
                            type="button"
                            onClick={() => handleQuickStatus(m.id, "MALPRACTICE")}
                            className="px-1.5 py-0.5 rounded border border-purple-200 text-purple-600 hover:bg-purple-50 text-[10px] font-medium"
                          >
                            Malpractice
                          </button>
                          <button
                            type="button"
                            onClick={() => handleQuickStatus(m.id, "NOT_ENTERED")}
                            className="px-1.5 py-0.5 rounded border border-slate-200 text-slate-500 hover:bg-slate-50 text-[10px]"
                          >
                            Clear
                          </button>
                        </div>
                      ) : (
                        <span className="text-slate-400 text-[11px]">Locked</span>
                      )}
                    </td>
                    <td className="p-3 text-slate-400 text-[11px] truncate max-w-xs">{m.remarks || "—"}</td>
                    {selectedAssessment?.isFinalized && (
                      <td className="p-3">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedMarkForCorrection(m);
                            setNewScore(m.marksObtained !== null ? m.marksObtained : "");
                            setNewStatus(m.status);
                            setCorrectionModalOpen(true);
                          }}
                          className="h-6 text-[10px] px-2"
                        >
                          Request Correction
                        </Button>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Marks Finalization Confirmation Modal */}
      <Dialog open={finalizeModalOpen} onClose={() => setFinalizeModalOpen(false)}>
        <div className="p-6 space-y-4 max-w-md">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-full bg-slate-900 text-white dark:bg-white dark:text-slate-900">
              <Lock className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Finalize & Lock Marks
              </h2>
              <p className="text-xs text-slate-400">Lock score matrix permanently</p>
            </div>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/60 text-xs space-y-2">
            <div className="flex justify-between">
              <span>Total Candidates:</span>
              <span className="font-bold">{marks.length}</span>
            </div>
            <div className="flex justify-between text-emerald-600 font-medium">
              <span>Entered Marks:</span>
              <span>{enteredCount}</span>
            </div>
            <div className="flex justify-between text-rose-600 font-medium">
              <span>Absent Students:</span>
              <span>{absentCount}</span>
            </div>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            Finalization prevents further direct edits to this assessment. Subsequent adjustments will require a formal <strong>Mark Correction</strong> request signed off by the Department HOD.
          </p>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button variant="outline" onClick={() => setFinalizeModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleFinalizeRoster}
              disabled={finalizing}
              className="bg-slate-900 text-white hover:bg-slate-800"
            >
              {finalizing ? "Locking..." : "Confirm & Lock Marks"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Mark Correction Modal */}
      <Dialog open={correctionModalOpen} onClose={() => setCorrectionModalOpen(false)}>
        <form onSubmit={handleRequestCorrection} className="p-6 space-y-5 max-w-md">
          <div className="border-b border-slate-200 pb-3 dark:border-slate-800">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <History className="h-5 w-5 text-indigo-600" />
              Request Mark Correction
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Finalized marks require an audited correction petition for HOD approval.
            </p>
          </div>

          {selectedMarkForCorrection && (
            <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/60 text-xs space-y-1">
              <p><strong>Candidate:</strong> {selectedMarkForCorrection.studentName} ({selectedMarkForCorrection.rollNumber})</p>
              <p><strong>Current Score:</strong> {selectedMarkForCorrection.marksObtained ?? "N/A"} / {selectedMarkForCorrection.maxMarks} ({selectedMarkForCorrection.status})</p>
            </div>
          )}

          <div className="space-y-4 text-xs">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Requested New Score *
              </label>
              <input
                type="number"
                min={0}
                max={selectedMarkForCorrection?.maxMarks || 100}
                required
                value={newScore}
                onChange={(e) => setNewScore(e.target.value === "" ? "" : Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Requested Status *
              </label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value as MarkStatus)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="ENTERED">Entered / Present</option>
                <option value="ABSENT">Absent</option>
                <option value="WITHHELD">Withheld</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Academic Justification / Error Rationale *
              </label>
              <textarea
                rows={3}
                required
                value={correctionReason}
                onChange={(e) => setCorrectionReason(e.target.value)}
                placeholder="e.g. Re-totalling omission in Section B Question 3; answer script re-verified."
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button type="button" variant="outline" onClick={() => setCorrectionModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={submittingCorrection}>
              {submittingCorrection ? "Submitting..." : "Submit to HOD"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}

export default function MarksEntryRosterPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading marks matrix...</div>}>
      <MarksEntryRosterContent />
    </Suspense>
  );
}

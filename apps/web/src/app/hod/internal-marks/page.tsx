"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import {
  hodService,
  HodInternalMarksData,
  HodInternalMarkRecord,
} from "@/services/hod.service";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import {
  ClipboardList,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Award,
  Sparkles,
  Download,
  AlertCircle,
  Edit3,
  X,
  ShieldAlert,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function HodInternalMarksPage() {
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [data, setData] = useState<HodInternalMarksData | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCourse, setSelectedCourse] = useState("ALL");
  const [selectedSemester, setSelectedSemester] = useState<number | "ALL">(5);

  // Correction Request Modal
  const [correctionTarget, setCorrectionTarget] = useState<HodInternalMarkRecord | null>(null);
  const [requestedMark, setRequestedMark] = useState<number>(0);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await hodService.getInternalMarks(
          selectedSemester === "ALL" ? undefined : selectedSemester,
          selectedCourse === "ALL" ? undefined : selectedCourse
        );
        if (res.success && res.data) {
          setData(res.data);
        }
      } catch (err) {
        console.error("Failed to load internal marks", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [selectedSemester, selectedCourse]);

  const filteredRecords = (data?.records || []).filter((r) => {
    const q = search.toLowerCase();
    return (
      r.studentName.toLowerCase().includes(q) ||
      r.rollNumber.toLowerCase().includes(q) ||
      r.courseCode.toLowerCase().includes(q)
    );
  });

  const openCorrectionModal = (record: HodInternalMarkRecord) => {
    setCorrectionTarget(record);
    setRequestedMark(record.totalInternal);
    setReason("");
  };

  const handleCorrectionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!correctionTarget) return;

    setSubmitting(true);
    try {
      const res = await hodService.requestMarkCorrection({
        studentId: correctionTarget.studentId,
        assessmentId: "asm-internal-2026",
        courseCode: correctionTarget.courseCode,
        originalMark: correctionTarget.totalInternal,
        requestedMark: Number(requestedMark),
        reason: reason.trim() || "Marks retotalling discrepancy verified against answer script.",
      });

      if (res.success) {
        setToastMessage(
          `Correction request submitted for ${correctionTarget.studentName} (${correctionTarget.rollNumber}). Recorded in audit ledger.`
        );
        setCorrectionTarget(null);
      }
    } catch (err) {
      alert("Failed to submit correction request.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-300 text-emerald-900 rounded-lg text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-emerald-700 hover:text-emerald-900">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-yellow-800 bg-yellow-100 px-2 py-0.5 rounded-full border border-yellow-300">
              Academic Assessment
            </span>
            <span className="text-[11px] font-mono text-slate-500">Continuous Evaluation Scheme</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <ClipboardList className="h-6 w-6 text-yellow-600" />
            Internal Marks Management & Attention Radar
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Department internal assessment ledger, component breakdown (IA1, IA2, IA3, assignments, attendance), and audited correction workflows.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="text-xs bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            onClick={() => alert("Downloading Department Consolidated Internal Marks Ledger (Excel)...")}
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export Marks Ledger
          </Button>
        </div>
      </div>

      {/* KPI Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Evaluated Records
              </span>
              <ClipboardList className="h-4 w-4 text-blue-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.summary.totalRecords || 5}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Active Department Students</div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Average Internal Score
              </span>
              <Sparkles className="h-4 w-4 text-yellow-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.summary.averagePercentage || 76.0}%
            </div>
            <div className="text-[11px] text-emerald-600 font-semibold mt-1">
              Class Average: 38.0 / 50.0 Marks
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Requires Attention (&lt;50%)
              </span>
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </div>
            <div className="text-2xl font-black text-red-600 mt-2">
              {data?.summary.studentsRequiringAttention || 1}
            </div>
            <div className="text-[11px] text-red-700 font-bold mt-1">
              Eligible for remedial coaching
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Missing Marks Entries
              </span>
              <AlertCircle className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-2xl font-black text-amber-700 mt-2">
              {data?.summary.missingMarksCount || 1}
            </div>
            <div className="text-[11px] text-amber-700 font-medium mt-1">
              In CS303 Computer Networks
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Attention Alert Banner if students below threshold exist */}
      {(data?.attentionList || []).length > 0 && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-950 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-red-100 flex items-center justify-center text-red-700 shrink-0 border border-red-200 font-bold">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-black uppercase tracking-wider text-red-800">
                Academic Attention Radar ({data?.attentionList.length} Student Flagged)
              </div>
              <div className="text-xs text-red-700 mt-0.5">
                Students scoring below 50% total internal assessment in core subjects. Remedial mentoring prescribed.
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            {data?.attentionList.map((stu) => (
              <span
                key={stu.id}
                className="px-2.5 py-1 rounded bg-white font-mono text-xs font-bold text-red-700 border border-red-300 shadow-xs"
              >
                {stu.studentName} ({stu.rollNumber}) — {stu.percentage}% in {stu.courseCode}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-3 rounded-lg border border-slate-200">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <Input
            placeholder="Search student roll, name, subject..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 text-xs h-9"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-bold text-slate-500">Course:</span>
            <select
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 font-bold text-slate-800 focus:outline-none"
            >
              <option value="ALL">All Subjects</option>
              <option value="CS301">CS301 (DSA)</option>
              <option value="CS302">CS302 (DBMS)</option>
              <option value="CS303">CS303 (Networks)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Marks Ledger Table */}
      <Card className="border-slate-200 bg-white shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/75 text-[10px] font-bold uppercase tracking-wider text-slate-600">
                <th className="py-3 px-4">Student Name & Roll No</th>
                <th className="py-3 px-4">Subject & Faculty</th>
                <th className="py-3 px-3 text-center">IA-1 (25)</th>
                <th className="py-3 px-3 text-center">IA-2 (25)</th>
                <th className="py-3 px-3 text-center">Model (50)</th>
                <th className="py-3 px-3 text-center">Assign (20)</th>
                <th className="py-3 px-3 text-center">Att (10)</th>
                <th className="py-3 px-4 text-center">Total (50)</th>
                <th className="py-3 px-4 text-center">% Score</th>
                <th className="py-3 px-4 text-right">HOD Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-slate-400">
                    <EmptyState
                      title="No marks records found"
                      description="Try adjusting your course or search filters."
                    />
                  </td>
                </tr>
              ) : (
                filteredRecords.map((r) => (
                  <tr
                    key={r.id}
                    className={cn(
                      "transition-colors",
                      r.requiresAttention || r.percentage < 50.0
                        ? "bg-red-50/40 hover:bg-red-50/60"
                        : "hover:bg-yellow-50/30"
                    )}
                  >
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{r.studentName}</div>
                      <div className="font-mono text-[11px] text-slate-500 font-semibold">
                        {r.rollNumber} • Sec {r.section}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{r.courseName}</div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <span className="font-mono font-bold text-yellow-800 bg-yellow-100 px-1 rounded">
                          {r.courseCode}
                        </span>
                        • {r.facultyName}
                      </div>
                    </td>
                    <td className="py-3 px-3 text-center font-mono font-bold text-slate-800">
                      {r.ia1}
                    </td>
                    <td className="py-3 px-3 text-center font-mono font-bold text-slate-800">
                      {r.ia2}
                    </td>
                    <td className="py-3 px-3 text-center font-mono font-bold text-slate-800">
                      {r.ia3Model}
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-600">
                      {r.assignments}
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-600">
                      {r.attendanceScore}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="font-mono font-black text-sm text-slate-900">
                        {r.totalInternal}
                      </span>
                      <span className="text-[10px] text-slate-400"> / {r.maxInternal}</span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded text-[11px] font-mono font-bold",
                          r.percentage >= 85
                            ? "bg-emerald-100 text-emerald-800"
                            : r.percentage >= 50
                            ? "bg-yellow-100 text-yellow-900"
                            : "bg-red-100 text-red-800"
                        )}
                      >
                        {r.percentage}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openCorrectionModal(r)}
                        className="text-[11px] text-yellow-800 hover:text-yellow-950 hover:bg-yellow-100 font-bold h-7 px-2"
                      >
                        <Edit3 className="h-3 w-3 mr-1" />
                        Audit Correction
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Marks Correction Modal */}
      {correctionTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-yellow-50/50">
              <div className="flex items-center gap-2">
                <Edit3 className="h-4 w-4 text-yellow-700" />
                <h3 className="font-black text-sm text-slate-900">
                  Request Internal Mark Correction
                </h3>
              </div>
              <button
                onClick={() => setCorrectionTarget(null)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCorrectionSubmit} className="p-4 space-y-3.5 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                <div className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">
                  Target Student & Assessment
                </div>
                <div className="font-bold text-slate-900 text-sm">
                  {correctionTarget.studentName} ({correctionTarget.rollNumber})
                </div>
                <div className="text-slate-600 font-mono text-[11px]">
                  {correctionTarget.courseCode} - {correctionTarget.courseName}
                </div>
                <div className="text-slate-600">
                  Current Recorded Mark:{" "}
                  <span className="font-mono font-bold text-slate-900">
                    {correctionTarget.totalInternal} / {correctionTarget.maxInternal}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                  Proposed Corrected Mark (out of {correctionTarget.maxInternal})
                </label>
                <Input
                  type="number"
                  step="0.5"
                  min="0"
                  max={correctionTarget.maxInternal}
                  value={requestedMark}
                  onChange={(e) => setRequestedMark(parseFloat(e.target.value) || 0)}
                  required
                  className="font-mono text-sm font-bold"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                  Justification & Answer Script Verification Details
                </label>
                <textarea
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Question 4(b) answer script retotalling verified with faculty Dr. Sharma."
                  required
                  className="w-full text-xs p-2.5 rounded-md border border-slate-300 focus:outline-none focus:ring-1 focus:ring-yellow-500"
                />
              </div>

              <div className="p-2.5 bg-yellow-50 rounded text-[11px] text-yellow-900 flex items-start gap-2 border border-yellow-200">
                <ShieldAlert className="h-4 w-4 shrink-0 text-yellow-700 mt-0.5" />
                <span>
                  HOD cannot overwrite marks directly. This submission enters the departmental audit log and notifies the Controller of Examinations.
                </span>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCorrectionTarget(null)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={submitting}
                  className="bg-yellow-400 text-slate-950 font-bold hover:bg-yellow-500 text-xs shadow-xs"
                >
                  {submitting ? "Submitting..." : "Submit to Audit Ledger"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

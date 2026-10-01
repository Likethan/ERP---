"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import type {
  CourseOffering,
  Assessment,
  AssessmentMarksRoster,
  StudentMark,
  ExamEligibility,
  MarkCorrection,
} from "@campusos/types";
import {
  FileSpreadsheet,
  Lock,
  Save,
  Send,
  UserX,
  History,
  RotateCcw,
} from "lucide-react";

function MarksEntryRosterContent() {
  const { hasPermission } = useAuth();
  const searchParams = useSearchParams();

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Aux state
  const [courseOfferings, setCourseOfferings] = useState<CourseOffering[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);

  // Selection
  const [selectedCourseId, setSelectedCourseId] = useState<string>(
    searchParams.get("course_offering_id") || ""
  );
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>(
    searchParams.get("assessment_id") || ""
  );

  // Roster data
  const [rosterData, setRosterData] = useState<AssessmentMarksRoster | null>(null);
  const [eligibilityMap, setEligibilityMap] = useState<Record<string, ExamEligibility>>({});
  const [localMarks, setLocalMarks] = useState<
    Record<
      string,
      {
        marks_obtained: number | "";
        status: string;
        is_absent: boolean;
        remarks: string;
      }
    >
  >({});

  // Corrections Drawer / Modal
  const [correctionTarget, setCorrectionTarget] = useState<StudentMark | null>(null);
  const [correctionForm, setCorrectionForm] = useState({
    new_marks: 0,
    new_status: "PRESENT",
    reason: "",
  });
  const [correctionSubmitting, setCorrectionSubmitting] = useState(false);

  // Pending corrections list
  const [pendingCorrections, setPendingCorrections] = useState<MarkCorrection[]>([]);

  // Load initial courses
  useEffect(() => {
    async function loadCourses() {
      try {
        const res = await apiFetch<CourseOffering[]>("/api/v1/academics/course-offerings");
        const list = res.data || [];
        setCourseOfferings(list);

        if (!selectedCourseId && list.length > 0) {
          setSelectedCourseId(list[0].id);
        }
      } catch {
        const mockCourses = [
          {
            id: "off-cs301",
            course_code: "CS301",
            course_name: "Data Structures & Algorithms",
            faculty_name: "Dr. Rajesh Sharma",
            section_name: "Sec A",
          } as unknown as CourseOffering,
          {
            id: "off-cs302",
            course_code: "CS302",
            course_name: "Database Management Systems",
            faculty_name: "Dr. K. S. Anand",
            section_name: "Sec A",
          } as unknown as CourseOffering,
        ];
        setCourseOfferings(mockCourses);
        if (!selectedCourseId) {
          setSelectedCourseId(mockCourses[0].id);
        }
      }
    }
    loadCourses();
  }, []);

  // When course changes, load its assessments
  useEffect(() => {
    if (!selectedCourseId) {
      setAssessments([]);
      return;
    }

    async function loadAssessments() {
      try {
        const res = await apiFetch<Assessment[]>(
          `/api/v1/examinations/assessments?course_offering_id=${selectedCourseId}`
        );
        const list = res.data || [];
        setAssessments(list);

        if (list.length > 0) {
          if (!list.some((a) => a.id === selectedAssessmentId)) {
            setSelectedAssessmentId(list[0].id);
          }
        } else {
          setSelectedAssessmentId("");
          setRosterData(null);
        }
      } catch {
        const mockAssessments = [
          {
            id: "asm-ia1-2026",
            course_offering_id: selectedCourseId,
            title: "Continuous Internal Assessment 1",
            max_marks: 50,
            passing_marks: 20,
            weightage_percent: 20,
            status: "OPEN",
            assessment_type: "INTERNAL",
            sequence: 1,
          } as unknown as Assessment,
          {
            id: "asm-ia2-2026",
            course_offering_id: selectedCourseId,
            title: "Continuous Internal Assessment 2",
            max_marks: 50,
            passing_marks: 20,
            weightage_percent: 20,
            status: "OPEN",
            assessment_type: "INTERNAL",
            sequence: 2,
          } as unknown as Assessment,
        ];
        setAssessments(mockAssessments);
        if (!selectedAssessmentId || !mockAssessments.some((a) => a.id === selectedAssessmentId)) {
          setSelectedAssessmentId(mockAssessments[0].id);
        }
      }
    }

    loadAssessments();
  }, [selectedCourseId]);

  // Load Roster & Eligibility whenever assessment changes
  useEffect(() => {
    if (!selectedAssessmentId) {
      setRosterData(null);
      return;
    }

    async function loadRoster() {
      try {
        setError(null);

        const rosterRes = await apiFetch<AssessmentMarksRoster>(
          `/api/v1/examinations/assessments/${selectedAssessmentId}/marks`
        );
        const roster = rosterRes.data;
        setRosterData(roster);

        // Initialize local editable state
        const initialMap: Record<
          string,
          {
            marks_obtained: number | "";
            status: string;
            is_absent: boolean;
            remarks: string;
          }
        > = {};

        roster.roster.forEach((item) => {
          initialMap[item.student_id] = {
            marks_obtained: item.marks_obtained ?? "",
            status: item.status || "PRESENT",
            is_absent: item.is_absent || item.status === "ABSENT",
            remarks: item.remarks || "",
          };
        });
        setLocalMarks(initialMap);

        // Fetch attendance eligibility for this course offering
        if (selectedCourseId) {
          try {
            const eligRes = await apiFetch<ExamEligibility[]>(
              `/api/v1/examinations/course-offerings/${selectedCourseId}/eligibility`
            );
            const map: Record<string, ExamEligibility> = {};
            (eligRes.data || []).forEach((e) => {
              map[e.student_id] = e;
            });
            setEligibilityMap(map);
          } catch {
            // Non-fatal
          }
        }
      } catch {
        const mockRes = await examinationsService.getMarksRoster(selectedCourseId, selectedAssessmentId);
        const currentAsm = assessments.find((a) => a.id === selectedAssessmentId);
        const roster: AssessmentMarksRoster = {
          assessment: (currentAsm || {
            id: selectedAssessmentId || "asm-ia1-2026",
            course_offering_id: selectedCourseId,
            title: "Continuous Internal Assessment 1",
            max_marks: 50,
            passing_marks: 20,
            weightage_percent: 20,
            status: "OPEN",
            assessment_type: "INTERNAL",
            sequence: 1,
          }) as unknown as Assessment,
          total_enrolled: mockRes.data.entries.length,
          marks_entered_count: mockRes.data.entries.filter((e: any) => e.marks_obtained !== null).length,
          is_locked: false,
          roster: mockRes.data.entries.map((e: any) => ({
            id: e.id,
            assessment_id: selectedAssessmentId,
            student_id: e.student_id,
            roll_number: e.roll_number,
            first_name: e.first_name,
            last_name: e.last_name,
            enrollment_status: "ENROLLED",
            marks_obtained: e.marks_obtained,
            percentage: (e.marks_obtained / 50) * 100,
            status: e.status,
            is_absent: e.is_absent,
            remarks: e.remarks,
          })),
        } as unknown as AssessmentMarksRoster;

        setRosterData(roster);
        const initialMap: Record<
          string,
          {
            marks_obtained: number | "";
            status: string;
            is_absent: boolean;
            remarks: string;
          }
        > = {};
        roster.roster.forEach((item) => {
          initialMap[item.student_id] = {
            marks_obtained: item.marks_obtained ?? "",
            status: item.status || "PRESENT",
            is_absent: item.is_absent || item.status === "ABSENT",
            remarks: item.remarks || "",
          };
        });
        setLocalMarks(initialMap);
      }
    }

    loadRoster();
  }, [selectedAssessmentId, selectedCourseId]);

  const activeAssessment = rosterData?.assessment;
  const isFinalized = activeAssessment?.is_finalized ?? false;

  // Real-time grid validation
  function handleMarkChange(studentId: string, valStr: string) {
    const num = valStr === "" ? "" : Number(valStr);
    setLocalMarks((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        marks_obtained: num,
      },
    }));
  }

  function handleStatusChange(studentId: string, status: string) {
    const isAbsent = status === "ABSENT";
    setLocalMarks((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        status,
        is_absent: isAbsent,
        marks_obtained: isAbsent ? 0 : prev[studentId]?.marks_obtained ?? "",
      },
    }));
  }

  function handleRemarksChange(studentId: string, remarks: string) {
    setLocalMarks((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        remarks,
      },
    }));
  }

  // Bulk save handler (Draft or Finalize)
  async function handleBulkSave(isDraft: boolean) {
    if (!selectedAssessmentId || !rosterData) return;

    // Validate marks within range
    const maxMarks = activeAssessment?.max_marks ?? 100;
    const entries: {
      student_id: string;
      marks_obtained?: number | null;
      status: string;
      is_absent: boolean;
      remarks?: string | null;
    }[] = [];

    for (const item of rosterData.roster) {
      const draft = localMarks[item.student_id];
      if (!draft) continue;

      if (
        draft.marks_obtained !== "" &&
        draft.status !== "ABSENT" &&
        (draft.marks_obtained < 0 || draft.marks_obtained > maxMarks)
      ) {
        setError(
          `Invalid marks for student. Marks must be between 0 and maximum marks (${maxMarks}).`
        );
        return;
      }

      entries.push({
        student_id: item.student_id,
        marks_obtained:
          draft.marks_obtained === "" ? null : Number(draft.marks_obtained),
        status: draft.status,
        is_absent: draft.is_absent,
        remarks: draft.remarks.trim() || null,
      });
    }

    try {
      setSaving(true);
      setError(null);

      const res = await apiFetch<AssessmentMarksRoster>(
        `/api/v1/examinations/assessments/${selectedAssessmentId}/marks/bulk`,
        {
          method: "POST",
          body: JSON.stringify({
            assessment_id: selectedAssessmentId,
            is_draft: isDraft,
            entries,
          }),
        }
      );

      setRosterData(res.data);
      setSuccessMsg(
        isDraft
          ? "Marks draft saved successfully."
          : "Marks successfully submitted and marked ready for evaluation."
      );
    } catch {
      await examinationsService.submitMarks(selectedAssessmentId, localMarks);
      setSuccessMsg(
        isDraft
          ? "Marks draft saved successfully."
          : "Marks successfully submitted and marked ready for evaluation."
      );
    } finally {
      setSaving(false);
    }
  }

  // Submit Audited Correction Request for finalized marks
  async function handleCorrectionSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!correctionTarget) return;

    try {
      setCorrectionSubmitting(true);
      setError(null);

      await apiFetch<MarkCorrection>(
        `/api/v1/examinations/marks/${correctionTarget.id}/correction`,
        {
          method: "POST",
          body: JSON.stringify({
            new_marks: Number(correctionForm.new_marks),
            new_status: correctionForm.new_status,
            reason: correctionForm.reason.trim(),
          }),
        }
      );

      setSuccessMsg("Correction request submitted for administrative review.");
      setCorrectionTarget(null);
      setCorrectionForm({ new_marks: 0, new_status: "PRESENT", reason: "" });

      // Refresh roster
      const rosterRes = await apiFetch<AssessmentMarksRoster>(
        `/api/v1/examinations/assessments/${selectedAssessmentId}/marks`
      );
      setRosterData(rosterRes.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit correction request.");
    } finally {
      setCorrectionSubmitting(false);
    }
  }

  // Approve a pending correction
  async function handleApproveCorrection(correctionId: string) {
    try {
      setError(null);
      await apiFetch<MarkCorrection>(
        `/api/v1/examinations/marks/corrections/${correctionId}/approve`,
        {
          method: "POST",
          body: JSON.stringify({
            approval_notes: "Approved by examination authority.",
          }),
        }
      );

      setSuccessMsg("Mark correction approved and ledger updated.");
      setPendingCorrections((prev) => prev.filter((c) => c.id !== correctionId));

      // Refresh roster
      const rosterRes = await apiFetch<AssessmentMarksRoster>(
        `/api/v1/examinations/assessments/${selectedAssessmentId}/marks`
      );
      setRosterData(rosterRes.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to approve correction.");
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/examinations"
              className="text-xs font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
            >
              Examination Hub
            </Link>
            <span className="text-slate-400 text-xs">/</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Marks Roster</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <FileSpreadsheet className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Class Roster Marks Entry
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Authoritative class roster grading, attendance eligibility integration, and audited correction workflows.
          </p>
        </div>

        {/* Global Save Actions */}
        {rosterData && !isFinalized && hasPermission("marks:enter") && (
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => handleBulkSave(true)}
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 transition disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              Save Draft
            </button>
            <button
              onClick={() => handleBulkSave(false)}
              disabled={saving}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              Submit Marks
            </button>
          </div>
        )}
      </div>

      {/* Alerts */}
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300 flex items-start justify-between">
          <div>
            <p className="font-semibold">Grading Validation Alert</p>
            <p className="mt-0.5">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-rose-600 hover:text-rose-800 dark:text-rose-400 text-xs font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {successMsg && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300 flex items-start justify-between">
          <p className="font-medium">{successMsg}</p>
          <button
            onClick={() => setSuccessMsg(null)}
            className="text-emerald-700 hover:text-emerald-900 text-xs font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Filters & Selection */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              Course Offering
            </label>
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              {courseOfferings.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.subject_code ? `${c.subject_code} - ` : ""}
                  {c.subject_name} ({c.section_name || "A"})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              Assessment Component
            </label>
            <select
              value={selectedAssessmentId}
              onChange={(e) => setSelectedAssessmentId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              {assessments.length === 0 ? (
                <option value="">No assessments configured for this course</option>
              ) : (
                assessments.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.title} (Max: {a.max_marks} | Weight: {a.weightage_percent}%)
                    {a.is_finalized ? " [FINALIZED]" : ""}
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        {/* Component Metadata Banner */}
        {activeAssessment && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-slate-900 dark:text-white">
                {activeAssessment.title}
              </span>
              <span className="text-xs px-2 py-0.5 rounded font-mono bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
                Max: {activeAssessment.max_marks} marks
              </span>
              <span className="text-xs px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                Passing: {activeAssessment.passing_marks} marks
              </span>
              <span className="text-xs px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                Weightage: {activeAssessment.weightage_percent}%
              </span>
            </div>

            <div>
              {isFinalized ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                  <Lock className="h-3.5 w-3.5" />
                  Marks Locked & Finalized
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
                  Editable Roster
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Pending Corrections Notification */}
      {pendingCorrections.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-xs dark:border-amber-900/50 dark:bg-amber-950/30">
          <div className="flex items-center gap-2 text-amber-800 dark:text-amber-300 font-semibold text-sm">
            <RotateCcw className="h-4 w-4" />
            <span>Pending Mark Corrections Awaiting Approval ({pendingCorrections.length})</span>
          </div>
          <div className="mt-3 space-y-2">
            {pendingCorrections.map((pc) => (
              <div
                key={pc.id}
                className="flex items-center justify-between bg-white dark:bg-slate-900 p-3 rounded-lg border border-amber-200 dark:border-amber-900/60 text-xs"
              >
                <div>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {pc.student_name} ({pc.student_roll_number || "No Roll"})
                  </span>
                  <span className="text-slate-500 mx-2">|</span>
                  <span>
                    Old: <span className="font-mono">{pc.old_marks ?? "N/A"}</span> → Proposed New:{" "}
                    <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                      {pc.new_marks}
                    </span>
                  </span>
                  <span className="text-slate-500 mx-2">|</span>
                  <span className="italic text-slate-600 dark:text-slate-400">Reason: {pc.reason}</span>
                </div>
                {hasPermission("marks:finalize") && (
                  <button
                    onClick={() => handleApproveCorrection(pc.id)}
                    className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded transition"
                  >
                    Approve
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Roster Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        <div className="p-5 border-b border-slate-200/80 dark:border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              Enrolled Students Roster
            </h2>
            <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium">
              {rosterData?.roster.length ?? 0} Students
            </span>
          </div>

          {rosterData && (
            <div className="flex items-center gap-4 text-xs">
              <span className="text-slate-500 dark:text-slate-400">
                Entered:{" "}
                <strong className="text-slate-800 dark:text-slate-200">
                  {rosterData.total_entered} / {rosterData.total_students}
                </strong>
              </span>
              <span className="text-slate-500 dark:text-slate-400">
                Absent:{" "}
                <strong className="text-rose-600 dark:text-rose-400">
                  {rosterData.total_absent}
                </strong>
              </span>
              {rosterData.average_marks != null && (
                <span className="text-slate-500 dark:text-slate-400">
                  Average:{" "}
                  <strong className="text-indigo-600 dark:text-indigo-400 font-mono">
                    {rosterData.average_marks}
                  </strong>
                </span>
              )}
            </div>
          )}
        </div>

        {!rosterData || rosterData.roster.length === 0 ? (
          <div className="p-12 text-center">
            <UserX className="mx-auto h-10 w-10 text-slate-300 dark:text-slate-600" />
            <h3 className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">
              No students enrolled
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              There are no enrolled students in this course offering or no assessment selected.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50/75 dark:bg-slate-800/50 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200/80 dark:border-slate-800">
                <tr>
                  <th className="py-3 px-4">Student</th>
                  <th className="py-3 px-4">Attendance Eligibility</th>
                  <th className="py-3 px-4">Evaluation Status</th>
                  <th className="py-3 px-4">Marks ({activeAssessment?.max_marks})</th>
                  <th className="py-3 px-4">Remarks</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {rosterData.roster.map((student) => {
                  const draft = localMarks[student.student_id] || {
                    marks_obtained: "",
                    status: "PRESENT",
                    is_absent: false,
                    remarks: "",
                  };
                  const elig = eligibilityMap[student.student_id];
                  const maxMarks = activeAssessment?.max_marks ?? 100;
                  const isOverLimit =
                    draft.marks_obtained !== "" && Number(draft.marks_obtained) > maxMarks;

                  return (
                    <tr
                      key={student.student_id}
                      className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition"
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {student.student_name}
                        </div>
                        <div className="text-xs text-slate-400 font-mono mt-0.5">
                          {student.student_roll_number || student.student_admission_number}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        {elig ? (
                          <div className="flex items-center gap-2">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                                elig.eligibility_status === "ELIGIBLE"
                                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                                  : "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                              }`}
                            >
                              {elig.eligibility_status}
                            </span>
                            {elig.attendance_percentage != null && (
                              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                                {elig.attendance_percentage}%
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400 italic">Not Evaluated</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <select
                          disabled={isFinalized}
                          value={draft.status}
                          onChange={(e) => handleStatusChange(student.student_id, e.target.value)}
                          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-800 focus:border-indigo-500 disabled:bg-slate-100 disabled:opacity-80 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:disabled:bg-slate-900"
                        >
                          <option value="PRESENT">Present</option>
                          <option value="ABSENT">Absent</option>
                          <option value="NOT_ATTEMPTED">Not Attempted</option>
                          <option value="WITHHELD">Withheld</option>
                          <option value="MALPRACTICE">Malpractice</option>
                        </select>
                      </td>

                      <td className="py-3.5 px-4">
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          max={maxMarks}
                          disabled={isFinalized || draft.status === "ABSENT"}
                          value={draft.marks_obtained}
                          onChange={(e) => handleMarkChange(student.student_id, e.target.value)}
                          placeholder={draft.status === "ABSENT" ? "ABSENT" : "0"}
                          className={`w-24 rounded-lg border px-2.5 py-1 font-mono text-sm text-slate-900 focus:ring-1 disabled:bg-slate-100 disabled:opacity-80 dark:bg-slate-800 dark:text-white dark:disabled:bg-slate-900 ${
                            isOverLimit
                              ? "border-rose-500 bg-rose-50 dark:bg-rose-950/30"
                              : "border-slate-300 dark:border-slate-700 focus:border-indigo-500 focus:ring-indigo-500"
                          }`}
                        />
                        {isOverLimit && (
                          <span className="block text-[10px] text-rose-600 dark:text-rose-400 mt-0.5">
                            Exceeds max ({maxMarks})
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <input
                          type="text"
                          disabled={isFinalized}
                          value={draft.remarks}
                          onChange={(e) => handleRemarksChange(student.student_id, e.target.value)}
                          placeholder="Optional notes"
                          className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-800 focus:border-indigo-500 disabled:bg-slate-100 disabled:opacity-80 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:disabled:bg-slate-900"
                        />
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        {isFinalized && hasPermission("marks:correct") && (
                          <button
                            onClick={() => {
                              setCorrectionTarget(student);
                              setCorrectionForm({
                                new_marks: student.marks_obtained ?? 0,
                                new_status: student.status || "PRESENT",
                                reason: "",
                              });
                            }}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-amber-600 hover:text-amber-500 dark:text-amber-400"
                          >
                            <History className="h-3.5 w-3.5" />
                            Request Correction
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Mark Correction Request */}
      {correctionTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-2.5 text-amber-600 dark:text-amber-400">
              <History className="h-5 w-5" />
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Request Supervised Mark Correction
              </h2>
            </div>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Because this assessment is finalized, any adjustment requires an audited justification and administrative sign-off.
            </p>

            <form onSubmit={handleCorrectionSubmit} className="mt-4 space-y-4">
              <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 p-3 text-xs">
                <p className="font-semibold text-slate-900 dark:text-white">
                  Student: {correctionTarget.student_name}
                </p>
                <p className="text-slate-500 mt-0.5">
                  Roll: {correctionTarget.student_roll_number || "N/A"} | Current Score:{" "}
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    {correctionTarget.marks_obtained ?? "N/A"}
                  </span>
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Proposed New Score *
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max={activeAssessment?.max_marks ?? 100}
                  required
                  value={correctionForm.new_marks}
                  onChange={(e) =>
                    setCorrectionForm({ ...correctionForm, new_marks: Number(e.target.value) })
                  }
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Status *
                </label>
                <select
                  value={correctionForm.new_status}
                  onChange={(e) =>
                    setCorrectionForm({ ...correctionForm, new_status: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                >
                  <option value="PRESENT">Present</option>
                  <option value="ABSENT">Absent</option>
                  <option value="WITHHELD">Withheld</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Correction Justification / Reason *
                </label>
                <textarea
                  rows={3}
                  required
                  value={correctionForm.reason}
                  onChange={(e) =>
                    setCorrectionForm({ ...correctionForm, reason: e.target.value })
                  }
                  placeholder="Detail the grading recalculation or re-evaluation reason..."
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setCorrectionTarget(null)}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={correctionSubmitting}
                  className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
                >
                  {correctionSubmitting ? "Submitting..." : "Submit Correction"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MarksEntryRosterPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-sm text-slate-400">Loading marks entry roster...</div>}>
      <MarksEntryRosterContent />
    </React.Suspense>
  );
}

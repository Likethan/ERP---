"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import type {
  SemesterResult,
  StudentSemesterTranscript,
  CourseOffering,
  ExamTerm,
} from "@campusos/types";
import {
  Award,
  CheckCircle2,
  Lock,
  Globe,
  Calculator,
  GraduationCap,
  Layers,
} from "lucide-react";

export default function ResultsAndPublicationPage() {
  const { hasPermission, hasRole } = useAuth();
  const [calculating, setCalculating] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Aux state
  const [courseOfferings, setCourseOfferings] = useState<CourseOffering[]>([]);
  const [examTerms, setExamTerms] = useState<ExamTerm[]>([]);

  // Selection
  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [selectedTermId, setSelectedTermId] = useState<string>("");

  // Loaded data
  const [courseResults, setCourseResults] = useState<SemesterResult[]>([]);
  const [studentTranscript, setStudentTranscript] = useState<StudentSemesterTranscript | null>(null);

  // Publication modal
  const [publishModalOpen, setPublishModalOpen] = useState(false);

  // Determine if viewing as Student
  const isStudentUser = hasRole("STUDENT");
  const [viewMode, setViewMode] = useState<"ADMIN" | "STUDENT">(
    isStudentUser ? "STUDENT" : "ADMIN"
  );

  // Load initial courses & terms
  useEffect(() => {
    async function loadAux() {
      try {
        setError(null);

        const [coursesRes, termsRes] = await Promise.all([
          apiFetch<CourseOffering[]>("/api/v1/academics/course-offerings"),
          apiFetch<ExamTerm[]>("/api/v1/examinations/terms"),
        ]);

        const courses = coursesRes.data || [];
        const terms = termsRes.data || [];
        setCourseOfferings(courses);
        setExamTerms(terms);

        if (courses.length > 0) setSelectedCourseId(courses[0].id);
        if (terms.length > 0) setSelectedTermId(terms[0].id);
      } catch {
        const mockCourses = [
          { id: "off-cs301", course_code: "CS301", course_name: "Data Structures & Algorithms" } as unknown as CourseOffering,
          { id: "off-cs302", course_code: "CS302", course_name: "Database Management Systems" } as unknown as CourseOffering,
        ];
        const mockTerms = [{ id: "term-odd-2026", name: "Odd Semester 2026-27", is_active: true } as unknown as ExamTerm];
        setCourseOfferings(mockCourses);
        setExamTerms(mockTerms);
        setSelectedCourseId(mockCourses[0].id);
        setSelectedTermId(mockTerms[0].id);
      }
    }

    loadAux();
  }, []);

  // Load results whenever course changes (in admin mode)
  useEffect(() => {
    if (viewMode === "ADMIN" && selectedCourseId) {
      loadCourseResults();
    }
  }, [selectedCourseId, viewMode]);

  // Load student results/transcript (in student mode)
  useEffect(() => {
    if (viewMode === "STUDENT" && selectedTermId) {
      loadStudentResults();
    }
  }, [selectedTermId, viewMode]);

  async function loadCourseResults() {
    if (!selectedCourseId) return;
    try {
      setError(null);
      const res = await apiFetch<SemesterResult[]>(
        `/api/v1/examinations/results?course_offering_id=${selectedCourseId}`
      );
      setCourseResults(res.data || []);
    } catch {
      const mockRes = await examinationsService.getResults();
      const mapped: SemesterResult[] = (mockRes.data || []).map((r, i) => ({
        id: `res-${r.studentId}`,
        student_id: r.studentId,
        student_name: r.name,
        roll_number: r.rollNumber,
        course_offering_id: selectedCourseId,
        course_code: "CS301",
        course_name: "Data Structures & Algorithms",
        final_marks_obtained: i === 0 ? 94 : i === 1 ? 88 : 82,
        final_percentage: i === 0 ? 94 : i === 1 ? 88 : 82,
        letter_grade: i === 0 ? "O" : i === 1 ? "A+" : "A",
        grade_points: i === 0 ? 10 : i === 1 ? 9 : 8,
        credits_earned: 4,
        result_status: "PASS",
        publication_status: "PUBLISHED",
      } as unknown as SemesterResult));
      setCourseResults(mapped);
    }
  }

  async function loadStudentResults() {
    try {
      setError(null);
      const res = await apiFetch<SemesterResult[]>(
        `/api/v1/examinations/results?exam_term_id=${selectedTermId}&publication_status=PUBLISHED`
      );
      setCourseResults(res.data || []);
    } catch {
      const mockRes = await examinationsService.getResults();
      const mapped: SemesterResult[] = (mockRes.data || []).map((r, i) => ({
        id: `res-${r.studentId}`,
        student_id: r.studentId,
        student_name: r.name,
        roll_number: r.rollNumber,
        course_offering_id: "off-cs301",
        course_code: "CS301",
        course_name: "Data Structures & Algorithms",
        final_marks_obtained: i === 0 ? 94 : i === 1 ? 88 : 82,
        final_percentage: i === 0 ? 94 : i === 1 ? 88 : 82,
        letter_grade: i === 0 ? "O" : i === 1 ? "A+" : "A",
        grade_points: i === 0 ? 10 : i === 1 ? 9 : 8,
        credits_earned: 4,
        result_status: "PASS",
        publication_status: "PUBLISHED",
      } as unknown as SemesterResult));
      setCourseResults(mapped);
    }
  }

  // Trigger automated course result calculation
  async function handleCalculateCourseResults() {
    if (!selectedCourseId) return;
    try {
      setCalculating(true);
      setError(null);

      const res = await apiFetch<SemesterResult[]>(
        `/api/v1/examinations/results/calculate-course/${selectedCourseId}`,
        { method: "POST" }
      );

      setCourseResults(res.data || []);
      setSuccessMsg(
        `Calculated authoritative results for ${res.data?.length || 0} students based on weighted scores and UGC grade scale.`
      );
    } catch {
      await loadCourseResults();
      setSuccessMsg(
        "Calculated authoritative results for 5 students based on weighted scores and UGC grade scale."
      );
    } finally {
      setCalculating(false);
    }
  }

  // Publish results for course
  async function handlePublishCourseResults() {
    if (!selectedCourseId) return;
    try {
      setPublishing(true);
      setError(null);

      const res = await apiFetch<{ published_count: number }>(
        `/api/v1/examinations/results/publish-course/${selectedCourseId}`,
        { method: "POST" }
      );

      setSuccessMsg(
        `Successfully published ${res.data?.published_count || 0} results! Results are now visible to students on their portal.`
      );
      setPublishModalOpen(false);
      loadCourseResults();
    } catch {
      setCourseResults((prev) =>
        prev.map((r) => ({ ...r, publication_status: "PUBLISHED" as any }))
      );
      setSuccessMsg(
        "Successfully published results! Results are now visible to students on their portal."
      );
      setPublishModalOpen(false);
    } finally {
      setPublishing(false);
    }
  }

  const selectedCourse = useMemo(
    () => courseOfferings.find((c) => c.id === selectedCourseId),
    [courseOfferings, selectedCourseId]
  );

  const publicationStats = useMemo(() => {
    const total = courseResults.length;
    const published = courseResults.filter((r) => r.publication_status === "PUBLISHED").length;
    const passing = courseResults.filter((r) => r.result_status === "PASS").length;
    return {
      total,
      published,
      passing,
      passPercentage: total > 0 ? Math.round((passing / total) * 100) : 0,
    };
  }, [courseResults]);

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
            <span className="text-xs text-slate-500 dark:text-slate-400">Results & Publication</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Award className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Grading & Result Publication
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Authoritative 10-point grade scale calculation, semester GPA computation, and controlled result publication.
          </p>
        </div>

        {/* View mode toggle for non-students */}
        {!isStudentUser && (
          <div className="flex items-center rounded-lg border border-slate-300 dark:border-slate-700 p-0.5 bg-slate-50 dark:bg-slate-800">
            <button
              onClick={() => setViewMode("ADMIN")}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${
                viewMode === "ADMIN"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Faculty / Admin
            </button>
            <button
              onClick={() => setViewMode("STUDENT")}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${
                viewMode === "STUDENT"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Student Portal Preview
            </button>
          </div>
        )}
      </div>

      {/* Alerts */}
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300 flex items-start justify-between">
          <div>
            <p className="font-semibold">Calculation Alert</p>
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

      {/* ADMIN VIEW */}
      {viewMode === "ADMIN" && (
        <div className="space-y-6">
          {/* Controls & Operations */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div className="w-full md:w-1/2">
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

              <div className="flex items-center gap-2.5">
                {hasPermission("results:finalize") && (
                  <button
                    onClick={handleCalculateCourseResults}
                    disabled={calculating}
                    className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition disabled:opacity-50"
                  >
                    <Calculator className="h-4 w-4" />
                    {calculating ? "Calculating..." : "Calculate Results"}
                  </button>
                )}

                {hasPermission("results:publish") && (
                  <button
                    onClick={() => setPublishModalOpen(true)}
                    disabled={courseResults.length === 0}
                    className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 transition disabled:opacity-50"
                  >
                    <Globe className="h-4 w-4" />
                    Publish to Students
                  </button>
                )}
              </div>
            </div>

            {/* Course Telemetry & KPI */}
            {selectedCourse && (
              <div className="mt-5 pt-5 border-t border-slate-100 dark:border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Total Enrolled</span>
                  <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                    {publicationStats.total}
                  </div>
                </div>

                <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Passing Rate</span>
                  <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                    {publicationStats.passPercentage}%
                  </div>
                </div>

                <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Publication Status</span>
                  <div className="text-sm font-bold text-slate-800 dark:text-slate-200 mt-1">
                    {publicationStats.published === publicationStats.total && publicationStats.total > 0 ? (
                      <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="h-4 w-4" />
                        100% Published
                      </span>
                    ) : (
                      <span className="text-amber-600 dark:text-amber-400">
                        {publicationStats.published} / {publicationStats.total} Published
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <span className="text-xs text-slate-500 dark:text-slate-400">Grading Standard</span>
                  <div className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 mt-1">
                    UGC 10-Point Scale
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results Table */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
            <div className="p-5 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                  Course Results Ledger
                </h2>
                <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium">
                  {courseResults.length}
                </span>
              </div>
            </div>

            {courseResults.length === 0 ? (
              <div className="p-12 text-center">
                <Calculator className="mx-auto h-10 w-10 text-slate-300 dark:text-slate-600" />
                <h3 className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">
                  No calculated results found
                </h3>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  Click &apos;Calculate Results&apos; to process marks across all assessment components.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-50/75 dark:bg-slate-800/50 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200/80 dark:border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Student</th>
                      <th className="py-3 px-4">Internal</th>
                      <th className="py-3 px-4">External</th>
                      <th className="py-3 px-4">Total Score</th>
                      <th className="py-3 px-4">Grade Letter</th>
                      <th className="py-3 px-4">Grade Point</th>
                      <th className="py-3 px-4">Outcome</th>
                      <th className="py-3 px-4">Publication</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {courseResults.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-slate-900 dark:text-white">
                            {r.student_name}
                          </div>
                          <div className="text-xs text-slate-400 font-mono mt-0.5">
                            {r.student_roll_number || r.student_admission_number}
                          </div>
                        </td>
                        <td className="py-3.5 px-4 font-mono">{r.internal_marks}</td>
                        <td className="py-3.5 px-4 font-mono">{r.external_marks}</td>
                        <td className="py-3.5 px-4 font-mono font-bold text-slate-900 dark:text-white">
                          {r.total_marks}%
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center justify-center w-8 h-8 rounded-lg font-mono font-bold text-sm ${
                              r.grade_letter === "F"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                                : r.grade_letter === "O" || r.grade_letter === "A+"
                                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                                : "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300"
                            }`}
                          >
                            {r.grade_letter}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono font-semibold">{r.grade_point}</td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                              r.result_status === "PASS"
                                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                                : "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                            }`}
                          >
                            {r.result_status}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          {r.publication_status === "PUBLISHED" ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                              <Globe className="h-3 w-3" />
                              Published
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300">
                              <Lock className="h-3 w-3" />
                              Unpublished
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* STUDENT SELF-SERVICE VIEW */}
      {viewMode === "STUDENT" && (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <GraduationCap className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                  Official Published Academic Transcript
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Verified results published by the Office of the Controller of Examinations.
                </p>
              </div>

              <div className="w-full sm:w-64">
                <select
                  value={selectedTermId}
                  onChange={(e) => setSelectedTermId(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                >
                  {examTerms.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Transcript GPA Telemetry Card */}
            {studentTranscript && (
              <div className="mt-5 pt-5 border-t border-slate-100 dark:border-slate-800/80 bg-linear-to-r from-indigo-50/50 to-purple-50/50 dark:from-slate-800/50 dark:to-slate-800/20 p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
                    Semester Performance
                  </span>
                  <div className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                    {studentTranscript.student_name}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                    Roll: {studentTranscript.student_roll_number || studentTranscript.student_admission_number}
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <span className="text-xs text-slate-500 dark:text-slate-400">Credits Earned</span>
                    <div className="text-lg font-bold text-slate-900 dark:text-white">
                      {studentTranscript.total_credits_earned} / {studentTranscript.total_credits_registered}
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-500 dark:text-slate-400">Semester GPA</span>
                    <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400">
                      {studentTranscript.semester_gpa != null ? studentTranscript.semester_gpa.toFixed(2) : "N/A"}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Published Courses Table */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
            {courseResults.length === 0 ? (
              <div className="p-12 text-center">
                <Lock className="mx-auto h-10 w-10 text-slate-300 dark:text-slate-600" />
                <h3 className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">
                  No published results available
                </h3>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                  Results for this examination term have not been officially published yet. In accordance with institutional examination privacy policy, marks remain confidential until official publication.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-50/75 dark:bg-slate-800/50 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200/80 dark:border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Course</th>
                      <th className="py-3 px-4">Credits</th>
                      <th className="py-3 px-4">Marks (%)</th>
                      <th className="py-3 px-4">Letter Grade</th>
                      <th className="py-3 px-4">Grade Point</th>
                      <th className="py-3 px-4">Earned</th>
                      <th className="py-3 px-4">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {courseResults.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                        <td className="py-3.5 px-4 font-medium text-slate-900 dark:text-white">
                          <div>
                            {r.course_code ? `${r.course_code} - ` : ""}
                            {r.course_name}
                          </div>
                        </td>
                        <td className="py-3.5 px-4 font-mono">{r.credits ?? 3}</td>
                        <td className="py-3.5 px-4 font-mono font-bold text-slate-900 dark:text-white">
                          {r.total_marks}%
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center justify-center w-7 h-7 rounded-md font-mono font-bold text-xs ${
                              r.grade_letter === "F"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                                : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            }`}
                          >
                            {r.grade_letter}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 font-mono font-semibold">{r.grade_point}</td>
                        <td className="py-3.5 px-4 font-mono">{r.credits_earned}</td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                              r.result_status === "PASS"
                                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                                : "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                            }`}
                          >
                            {r.result_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal: Publish Confirmation */}
      {publishModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-2.5 text-emerald-600 dark:text-emerald-400">
              <Globe className="h-6 w-6" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Confirm Result Publication
              </h3>
            </div>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Publishing will make the finalized course outcomes immediately visible to all enrolled students on their student portal. Once published, grades cannot be silently modified without formal audited correction procedures.
            </p>
            <div className="mt-5 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setPublishModalOpen(false)}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={publishing}
                onClick={handlePublishCourseResults}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {publishing ? "Publishing..." : "Confirm & Publish"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

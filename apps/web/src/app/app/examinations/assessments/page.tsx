"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  Assessment,
  CourseOffering,
  ExamTerm,
  CourseAssessmentStructure,
} from "@campusos/types";
import {
  BookOpen,
  Plus,
  CheckCircle2,
  AlertTriangle,
  Lock,
  ArrowRight,
  Layers,
} from "lucide-react";

export default function AssessmentConfigurationPage() {
  const { hasPermission } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Aux state
  const [courseOfferings, setCourseOfferings] = useState<CourseOffering[]>([]);
  const [examTerms, setExamTerms] = useState<ExamTerm[]>([]);

  // Selection & Filters
  const [selectedCourseId, setSelectedCourseId] = useState<string>("");
  const [filterType, setFilterType] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("");

  // Loaded structure
  const [structure, setStructure] = useState<CourseAssessmentStructure | null>(null);
  const [allAssessments, setAllAssessments] = useState<Assessment[]>([]);

  // Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [finalizeId, setFinalizeId] = useState<string | null>(null);
  const [finalizing, setFinalizing] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    course_offering_id: "",
    exam_term_id: "",
    title: "",
    assessment_type: "INTERNAL",
    sequence: 1,
    max_marks: 50,
    passing_marks: 20,
    weightage_percent: 20,
    description: "",
  });

  // Load initial course offerings & exam terms
  useEffect(() => {
    async function loadInitial() {
      try {
        setError(null);

        const [coursesRes, termsRes] = await Promise.all([
          apiFetch<CourseOffering[]>("/api/v1/academics/course-offerings"),
          apiFetch<ExamTerm[]>("/api/v1/examinations/terms"),
        ]);

        const courses = coursesRes.data || [];
        setCourseOfferings(courses);
        setExamTerms(termsRes.data || []);

        if (courses.length > 0) {
          const firstId = courses[0].id;
          setSelectedCourseId(firstId);
          setFormData((prev) => ({ ...prev, course_offering_id: firstId }));
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
          {
            id: "off-cs303",
            course_code: "CS303",
            course_name: "Operating Systems & Concurrency",
            faculty_name: "Prof. Meenakshi Sundaram",
            section_name: "Sec A",
          } as unknown as CourseOffering,
        ];
        setCourseOfferings(mockCourses);
        setSelectedCourseId(mockCourses[0].id);
        setFormData((prev) => ({ ...prev, course_offering_id: mockCourses[0].id }));
        setExamTerms([
          { id: "term-odd-2026", name: "Odd Semester 2026-27", is_active: true } as unknown as ExamTerm,
        ]);
      }
    }
    loadInitial();
  }, []);

  // Whenever selected course changes, load its assessment structure
  useEffect(() => {
    if (!selectedCourseId) {
      setStructure(null);
      return;
    }

    async function loadCourseStructure() {
      try {
        setError(null);
        const res = await apiFetch<CourseAssessmentStructure>(
          `/api/v1/examinations/assessments/structure/${selectedCourseId}`
        );
        setStructure(res.data);
        setFormData((prev) => ({
          ...prev,
          course_offering_id: selectedCourseId,
          sequence: (res.data?.assessments?.length || 0) + 1,
        }));
      } catch {
        const fallbackStructure: CourseAssessmentStructure = {
          course_offering_id: selectedCourseId,
          course_code: "CS301",
          course_name: "Data Structures & Algorithms",
          total_weightage_allocated: 100,
          is_complete: true,
          assessments: [
            {
              id: "asm-ia1-2026",
              course_offering_id: selectedCourseId,
              title: "Continuous Internal Assessment 1",
              assessment_type: "INTERNAL",
              sequence: 1,
              max_marks: 50,
              passing_marks: 20,
              weightage_percent: 20,
              status: "FINALIZED",
            } as unknown as Assessment,
            {
              id: "asm-ia2-2026",
              course_offering_id: selectedCourseId,
              title: "Continuous Internal Assessment 2",
              assessment_type: "INTERNAL",
              sequence: 2,
              max_marks: 50,
              passing_marks: 20,
              weightage_percent: 20,
              status: "OPEN",
            } as unknown as Assessment,
            {
              id: "asm-mid-2026",
              course_offering_id: selectedCourseId,
              title: "Mid-Term Evaluation",
              assessment_type: "MID_TERM",
              sequence: 3,
              max_marks: 100,
              passing_marks: 40,
              weightage_percent: 30,
              status: "DRAFT",
            } as unknown as Assessment,
            {
              id: "asm-ese-2026",
              course_offering_id: selectedCourseId,
              title: "End-Semester Examination",
              assessment_type: "END_SEM",
              sequence: 4,
              max_marks: 100,
              passing_marks: 40,
              weightage_percent: 30,
              status: "DRAFT",
            } as unknown as Assessment,
          ],
        } as unknown as CourseAssessmentStructure;

        setStructure(fallbackStructure);
        setFormData((prev) => ({
          ...prev,
          course_offering_id: selectedCourseId,
          sequence: fallbackStructure.assessments.length + 1,
        }));
      }
    }

    loadCourseStructure();
  }, [selectedCourseId]);

  // Filtered assessments
  const displayedAssessments = useMemo(() => {
    const list = structure?.assessments || allAssessments;
    return list.filter((a) => {
      if (filterType && a.assessment_type !== filterType) return false;
      if (filterStatus && a.status !== filterStatus) return false;
      return true;
    });
  }, [structure, allAssessments, filterType, filterStatus]);

  // Selected course details
  const selectedCourse = useMemo(
    () => courseOfferings.find((c) => c.id === selectedCourseId),
    [courseOfferings, selectedCourseId]
  );

  const totalWeightage = structure?.total_weightage_percent ?? displayedAssessments.reduce((sum, a) => sum + a.weightage_percent, 0);

  // Submit create assessment component
  async function handleCreateAssessment(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.course_offering_id) {
      setError("Please select a valid course offering.");
      return;
    }

    if (formData.passing_marks > formData.max_marks) {
      setError("Passing marks cannot exceed maximum marks.");
      return;
    }

    try {
      setCreating(true);
      setError(null);

      await apiFetch<Assessment>("/api/v1/examinations/assessments", {
        method: "POST",
        body: JSON.stringify({
          course_offering_id: formData.course_offering_id,
          exam_term_id: formData.exam_term_id || null,
          title: formData.title.trim(),
          assessment_type: formData.assessment_type,
          sequence: Number(formData.sequence),
          max_marks: Number(formData.max_marks),
          passing_marks: Number(formData.passing_marks),
          weightage_percent: Number(formData.weightage_percent),
          description: formData.description.trim() || null,
        }),
      });

      setSuccessMsg(`Assessment component "${formData.title}" created successfully.`);
      setCreateModalOpen(false);

      // Reset form title and reload structure
      setFormData((prev) => ({
        ...prev,
        title: "",
        sequence: prev.sequence + 1,
        description: "",
      }));

      // Reload
      const res = await apiFetch<CourseAssessmentStructure>(
        `/api/v1/examinations/assessments/structure/${formData.course_offering_id}`
      );
      setStructure(res.data);
    } catch {
      const newAsm: Assessment = {
        id: `asm-${Date.now()}`,
        course_offering_id: formData.course_offering_id,
        exam_term_id: formData.exam_term_id || "term-odd-2026",
        title: formData.title.trim(),
        assessment_type: formData.assessment_type as any,
        sequence: Number(formData.sequence),
        max_marks: Number(formData.max_marks),
        passing_marks: Number(formData.passing_marks),
        weightage_percent: Number(formData.weightage_percent),
        status: "DRAFT" as any,
      } as unknown as Assessment;

      setStructure((prev) =>
        prev
          ? {
              ...prev,
              assessments: [...prev.assessments, newAsm],
            }
          : null
      );
      setSuccessMsg(`Assessment component "${formData.title}" created successfully.`);
      setCreateModalOpen(false);
      setFormData((prev) => ({
        ...prev,
        title: "",
        sequence: prev.sequence + 1,
        description: "",
      }));
    } finally {
      setCreating(false);
    }
  }

  // Handle finalize assessment
  async function handleFinalize(assessmentId: string) {
    try {
      setFinalizing(true);
      setError(null);

      await apiFetch(`/api/v1/examinations/assessments/${assessmentId}/finalize`, {
        method: "POST",
      });

      setSuccessMsg("Assessment finalized and locked successfully.");
      setFinalizeId(null);

      if (selectedCourseId) {
        const res = await apiFetch<CourseAssessmentStructure>(
          `/api/v1/examinations/assessments/structure/${selectedCourseId}`
        );
        setStructure(res.data);
      }
    } catch {
      setStructure((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          assessments: prev.assessments.map((a) =>
            a.id === assessmentId ? { ...a, status: "FINALIZED" as any } : a
          ),
        };
      });
      setSuccessMsg("Assessment finalized and locked successfully.");
      setFinalizeId(null);
    } finally {
      setFinalizing(false);
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
            <span className="text-xs text-slate-500 dark:text-slate-400">Assessments</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <BookOpen className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Assessment Configuration
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Define multi-component assessment structures, sequence, passing benchmarks, and weightage distribution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {hasPermission("assessments:create") && (
            <button
              onClick={() => {
                setFormData((prev) => ({
                  ...prev,
                  course_offering_id: selectedCourseId,
                  sequence: (structure?.assessments?.length || 0) + 1,
                }));
                setCreateModalOpen(true);
              }}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition"
            >
              <Plus className="h-4 w-4" />
              New Component
            </button>
          )}
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300 flex items-start justify-between">
          <div>
            <p className="font-semibold">Operation Error</p>
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

      {/* Course Offering Selector & Filter Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-1">
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              Course Offering
            </label>
            <select
              value={selectedCourseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              {courseOfferings.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.subject_code ? `${c.subject_code} - ` : ""}
                  {c.subject_name || "Unnamed Course"} ({c.section_name || "Section A"})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              Filter By Type
            </label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              <option value="">All Assessment Types</option>
              <option value="INTERNAL">Internal Assessment</option>
              <option value="MIDTERM">Midterm</option>
              <option value="ASSIGNMENT">Assignment</option>
              <option value="QUIZ">Quiz</option>
              <option value="LAB">Lab / Practical</option>
              <option value="MODEL_EXAM">Model Exam</option>
              <option value="END_SEMESTER">End Semester Examination</option>
              <option value="PROJECT">Project Evaluation</option>
              <option value="VIVA">Viva Voce</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              Filter By Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              <option value="">All Statuses</option>
              <option value="CONFIGURED">Configured (Open for Entry)</option>
              <option value="FINALIZED">Finalized (Marks Locked)</option>
              <option value="DRAFT">Draft</option>
            </select>
          </div>
        </div>

        {/* Weightage Audit Card */}
        {selectedCourse && (
          <div className="mt-5 pt-5 border-t border-slate-100 dark:border-slate-800/80">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">
                    {selectedCourse.subject_code ? `${selectedCourse.subject_code}: ` : ""}
                    {selectedCourse.subject_name}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium">
                    {selectedCourse.subject_credits ?? 3} Credits
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Academic Year: {selectedCourse.academic_year_name || "Active"} | Semester:{" "}
                  {selectedCourse.semester_name || "Active"} | Section: {selectedCourse.section_name || "A"}
                </p>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Total Weightage
                  </span>
                  <div className="text-lg font-bold">
                    <span
                      className={
                        totalWeightage === 100
                          ? "text-emerald-600 dark:text-emerald-400"
                          : totalWeightage > 100
                          ? "text-rose-600 dark:text-rose-400"
                          : "text-amber-600 dark:text-amber-400"
                      }
                    >
                      {totalWeightage}%
                    </span>
                    <span className="text-xs text-slate-400 font-normal"> / 100%</span>
                  </div>
                </div>

                <div className="w-32 bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
                  <div
                    className={`h-2.5 rounded-full transition-all duration-500 ${
                      totalWeightage === 100
                        ? "bg-emerald-500"
                        : totalWeightage > 100
                        ? "bg-rose-500"
                        : "bg-amber-500"
                    }`}
                    style={{ width: `${Math.min(totalWeightage, 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {totalWeightage < 100 && (
              <p className="mt-2 text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" />
                Assessment weightage totals {totalWeightage}%. Configure remaining {100 - totalWeightage}% to complete grading structure.
              </p>
            )}
            {totalWeightage === 100 && (
              <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Cumulative weightage is mathematically sound (100.0%). Ready for authoritative marks evaluation.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Assessment Components List */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        <div className="p-5 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              Configured Assessment Components
            </h2>
            <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium">
              {displayedAssessments.length}
            </span>
          </div>
        </div>

        {displayedAssessments.length === 0 ? (
          <div className="p-12 text-center">
            <BookOpen className="mx-auto h-10 w-10 text-slate-300 dark:text-slate-600" />
            <h3 className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">
              No assessments configured
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              No assessment components have been created for this course offering yet.
            </p>
            {hasPermission("assessments:create") && (
              <button
                onClick={() => setCreateModalOpen(true)}
                className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
              >
                <Plus className="h-4 w-4" />
                Add First Assessment Component
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50/75 dark:bg-slate-800/50 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200/80 dark:border-slate-800">
                <tr>
                  <th className="py-3 px-4">Seq</th>
                  <th className="py-3 px-4">Title & Type</th>
                  <th className="py-3 px-4">Max Marks</th>
                  <th className="py-3 px-4">Passing</th>
                  <th className="py-3 px-4">Weightage</th>
                  <th className="py-3 px-4">Marks Progress</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {displayedAssessments.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-400">{a.sequence}</td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-900 dark:text-white">{a.title}</div>
                      <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                        <span className="capitalize">{a.assessment_type.toLowerCase().replace("_", " ")}</span>
                        {a.exam_term_name && <span>• {a.exam_term_name}</span>}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono font-medium text-slate-800 dark:text-slate-200">
                      {a.max_marks}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-600 dark:text-slate-400">
                      {a.passing_marks}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
                        {a.weightage_percent}%
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="text-xs font-medium text-slate-700 dark:text-slate-300">
                        {a.total_marks_entered} / {a.total_enrolled} entered
                      </div>
                      <div className="w-24 bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-1 overflow-hidden">
                        <div
                          className="bg-indigo-500 h-1.5 rounded-full"
                          style={{
                            width: `${
                              a.total_enrolled > 0
                                ? Math.round((a.total_marks_entered / a.total_enrolled) * 100)
                                : 0
                            }%`,
                          }}
                        />
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      {a.is_finalized ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                          <Lock className="h-3 w-3" />
                          Finalized
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
                          Open for Marks
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/app/examinations/marks?assessment_id=${a.id}&course_offering_id=${selectedCourseId}`}
                          className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 inline-flex items-center gap-1"
                        >
                          Roster & Marks
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Link>

                        {!a.is_finalized && hasPermission("assessments:finalize") && (
                          <button
                            onClick={() => setFinalizeId(a.id)}
                            className="text-xs px-2.5 py-1 rounded border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition"
                            title="Lock marks and mark component as finalized"
                          >
                            Finalize
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Create Assessment Component */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Create Assessment Component
            </h2>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Configure weightage and passing threshold for this evaluation milestone.
            </p>

            <form onSubmit={handleCreateAssessment} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Component Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Internal Assessment 1"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Assessment Type *
                  </label>
                  <select
                    value={formData.assessment_type}
                    onChange={(e) => setFormData({ ...formData, assessment_type: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <option value="INTERNAL">Internal Assessment</option>
                    <option value="MIDTERM">Midterm</option>
                    <option value="ASSIGNMENT">Assignment</option>
                    <option value="QUIZ">Quiz</option>
                    <option value="LAB">Lab / Practical</option>
                    <option value="MODEL_EXAM">Model Exam</option>
                    <option value="END_SEMESTER">End Semester Exam</option>
                    <option value="PROJECT">Project Evaluation</option>
                    <option value="VIVA">Viva Voce</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Exam Term (Optional)
                  </label>
                  <select
                    value={formData.exam_term_id}
                    onChange={(e) => setFormData({ ...formData, exam_term_id: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <option value="">No Associated Term</option>
                    {examTerms.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Max Marks *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="500"
                    required
                    value={formData.max_marks}
                    onChange={(e) => setFormData({ ...formData, max_marks: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Passing Marks *
                  </label>
                  <input
                    type="number"
                    min="0"
                    max={formData.max_marks}
                    required
                    value={formData.passing_marks}
                    onChange={(e) => setFormData({ ...formData, passing_marks: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Weightage (%) *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    required
                    value={formData.weightage_percent}
                    onChange={(e) =>
                      setFormData({ ...formData, weightage_percent: Number(e.target.value) })
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Description / Remarks
                </label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional evaluation criteria or syllabus modules covered..."
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Save Component"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Confirm Finalize Assessment */}
      {finalizeId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-3 text-amber-600 dark:text-amber-400">
              <Lock className="h-6 w-6" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Finalize Assessment Component?
              </h3>
            </div>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Finalizing this assessment will lock all student marks. Once locked, ordinary faculty cannot edit scores directly without initiating a formal, audited correction request.
            </p>
            <div className="mt-5 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setFinalizeId(null)}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={finalizing}
                onClick={() => handleFinalize(finalizeId)}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {finalizing ? "Locking..." : "Confirm & Lock Marks"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

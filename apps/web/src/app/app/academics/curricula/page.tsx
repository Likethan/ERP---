"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  CurriculumScheme,
  CurriculumDetail,
  Program,
  Regulation,
  Subject,
} from "@campusos/types";

const SUBJECT_CATEGORIES = [
  "CORE",
  "ELECTIVE",
  "PROFESSIONAL_ELECTIVE",
  "OPEN_ELECTIVE",
  "LAB",
  "PROJECT",
  "INTERNSHIP",
  "FOUNDATION",
];

export default function CurriculaPage() {
  const { hasPermission } = useAuth();
  const [curricula, setCurricula] = useState<CurriculumScheme[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [regulations, setRegulations] = useState<Regulation[]>([]);
  const [subjectsCatalog, setSubjectsCatalog] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Selected Scheme
  const [selectedProgramId, setSelectedProgramId] = useState("");
  const [selectedCurriculumId, setSelectedCurriculumId] = useState("");
  const [activeCurriculumDetail, setActiveCurriculumDetail] = useState<CurriculumDetail | null>(null);
  const [selectedSemester, setSelectedSemester] = useState<number>(1);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddSubjectModal, setShowAddSubjectModal] = useState(false);
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Scheme Create Form
  const [newProgramId, setNewProgramId] = useState("");
  const [newRegId, setNewRegId] = useState("");
  const [newName, setNewName] = useState("");
  const [newVersion, setNewVersion] = useState(1);
  const [newCredits, setNewCredits] = useState(160);
  const [newDesc, setNewDesc] = useState("");

  // Add Subject Form
  const [chosenSubjectId, setChosenSubjectId] = useState("");
  const [category, setCategory] = useState("CORE");
  const [isMandatory, setIsMandatory] = useState(true);
  const [electiveGroup, setElectiveGroup] = useState("");
  const [subjCredits, setSubjCredits] = useState(3.0);
  const [subjLectureHours, setSubjLectureHours] = useState(3);
  const [subjTutorialHours, setSubjTutorialHours] = useState(0);
  const [subjPracticalHours, setSubjPracticalHours] = useState(0);

  const canManage = hasPermission("academics:curriculum:manage");
  const canPublish = hasPermission("academics:curriculum:publish");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [currRes, progRes, regRes, subjRes] = await Promise.all([
        apiFetch<CurriculumScheme[]>("/api/v1/academics/curricula"),
        apiFetch<Program[]>("/api/v1/programs"),
        apiFetch<Regulation[]>("/api/v1/regulations"),
        apiFetch<Subject[]>("/api/v1/academics/subjects"),
      ]);

      setCurricula(currRes.data || []);
      setPrograms(progRes.data || []);
      setRegulations(regRes.data || []);
      setSubjectsCatalog(subjRes.data || []);

      if (currRes.data && currRes.data.length > 0 && !selectedCurriculumId) {
        setSelectedCurriculumId(currRes.data[0].id);
      }
    } catch {
      // Mock Fallback
      const { MOCK_CURRICULA, MOCK_PROGRAMS, MOCK_SUBJECTS } = await import("@/mocks/academics.mock");
      const mappedCurricula = MOCK_CURRICULA.map((c) => ({
        id: c.id,
        program_id: "prog-cse-btech",
        regulation_id: "reg-2024",
        name: c.name,
        version: 1,
        total_credits: c.totalCredits,
        status: c.status,
        is_locked: c.status === "PUBLISHED",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })) as unknown as CurriculumScheme[];

      const mappedProgs = MOCK_PROGRAMS.map((p) => ({
        id: p.id,
        code: p.code,
        name: p.name,
        department_id: "dept-cse",
        is_active: true,
      })) as unknown as Program[];

      const mappedRegs = [
        { id: "reg-2024", code: "R-2024", name: "Autonomous Regulation 2024", is_active: true },
        { id: "reg-2026", code: "R-2026", name: "AI & Embedded Scheme 2026", is_active: true },
      ] as unknown as Regulation[];

      const mappedSubs = MOCK_SUBJECTS.map((s) => ({
        id: s.id,
        code: s.code,
        name: s.name,
        department_id: "dept-cse",
        credits: s.credits,
        lecture_hours: s.lectureHours,
        tutorial_hours: s.tutorialHours,
        practical_hours: s.practicalHours,
        subject_type: s.type,
      })) as unknown as Subject[];

      setCurricula(mappedCurricula);
      setPrograms(mappedProgs);
      setRegulations(mappedRegs);
      setSubjectsCatalog(mappedSubs);

      if (mappedCurricula.length > 0 && !selectedCurriculumId) {
        setSelectedCurriculumId(mappedCurricula[0].id);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Fetch detailed breakdown when selected curriculum changes
  useEffect(() => {
    if (!selectedCurriculumId) {
      setActiveCurriculumDetail(null);
      return;
    }

    async function loadDetail() {
      try {
        const res = await apiFetch<CurriculumDetail>(
          `/api/v1/academics/curricula/${selectedCurriculumId}`
        );
        setActiveCurriculumDetail(res.data);
      } catch {
        // Mock detailed curriculum structure
        const mockDetail: CurriculumDetail = {
          id: selectedCurriculumId,
          program_id: "prog-cse-btech",
          program: { id: "prog-cse-btech", code: "BTECH-CSE", name: "B.Tech Computer Science & Engineering", department_id: "dept-cse", is_active: true },
          regulation_id: "reg-2024",
          regulation: { id: "reg-2024", code: "R-2024", name: "Autonomous CBCS Scheme 2024", is_active: true },
          name: "Outcome-Based Curriculum Scheme 2024 (CBCS)",
          version: 1,
          total_credits: 160,
          status: "PUBLISHED",
          is_locked: true,
          semesters: [
            {
              semester_number: 1,
              subjects: [
                {
                  id: "cs101",
                  subject_id: "sub-1",
                  subject: { id: "sub-1", code: "MA101", name: "Linear Algebra & Calculus", subject_type: "THEORY", department_id: "dept-cse", credits: 4, lecture_hours: 3, tutorial_hours: 1, practical_hours: 0, is_active: true },
                  category: "BASIC_SCIENCES",
                  is_mandatory: true,
                  credits: 4,
                  lecture_hours: 3,
                  tutorial_hours: 1,
                  practical_hours: 0,
                },
              ],
            },
            {
              semester_number: 5,
              subjects: [
                {
                  id: "cs301-c",
                  subject_id: "sub-cs301",
                  subject: { id: "sub-cs301", code: "CS301", name: "Data Structures & Algorithms", subject_type: "THEORY", department_id: "dept-cse", credits: 4, lecture_hours: 3, tutorial_hours: 1, practical_hours: 0, is_active: true },
                  category: "CORE",
                  is_mandatory: true,
                  credits: 4,
                  lecture_hours: 3,
                  tutorial_hours: 1,
                  practical_hours: 0,
                },
                {
                  id: "cs302-c",
                  subject_id: "sub-cs302",
                  subject: { id: "sub-cs302", code: "CS302", name: "Database Management Systems", subject_type: "INTEGRATED", department_id: "dept-cse", credits: 4, lecture_hours: 3, tutorial_hours: 0, practical_hours: 2, is_active: true },
                  category: "CORE",
                  is_mandatory: true,
                  credits: 4,
                  lecture_hours: 3,
                  tutorial_hours: 0,
                  practical_hours: 2,
                },
              ],
            },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        } as unknown as CurriculumDetail;

        setActiveCurriculumDetail(mockDetail);
      }
    }

    loadDetail();
  }, [selectedCurriculumId]);

  const handleCreateScheme = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProgramId || !newRegId || !newName.trim()) {
      setFormError("Please select program, regulation, and enter a scheme name.");
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);

      const res = await apiFetch<CurriculumDetail>("/api/v1/academics/curricula", {
        method: "POST",
        body: JSON.stringify({
          program_id: newProgramId,
          regulation_id: newRegId,
          name: newName.trim(),
          version: Number(newVersion),
          total_credits: Number(newCredits),
          description: newDesc.trim() || null,
        }),
      });

      setShowCreateModal(false);
      await loadData();
      setSelectedCurriculumId(res.data.id);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create curriculum.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddSubjectToSemester = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCurriculumId || !chosenSubjectId) {
      setFormError("Please select a valid subject from the master catalog.");
      return;
    }

    try {
      setSubmitting(true);
      setFormError(null);

      const res = await apiFetch<CurriculumDetail>(
        `/api/v1/academics/curricula/${selectedCurriculumId}/subjects`,
        {
          method: "POST",
          body: JSON.stringify({
            subject_id: chosenSubjectId,
            semester_number: selectedSemester,
            category,
            is_mandatory: isMandatory,
            elective_group: electiveGroup.trim() || null,
            credits: Number(subjCredits),
            lecture_hours: Number(subjLectureHours),
            tutorial_hours: Number(subjTutorialHours),
            practical_hours: Number(subjPracticalHours),
          }),
        }
      );

      setActiveCurriculumDetail(res.data);
      setShowAddSubjectModal(false);
      setChosenSubjectId("");
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to add subject to curriculum.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemoveSubject = async (subjectId: string) => {
    if (!selectedCurriculumId) return;
    if (!confirm("Are you sure you want to remove this subject from the draft curriculum?")) return;

    try {
      const res = await apiFetch<CurriculumDetail>(
        `/api/v1/academics/curricula/${selectedCurriculumId}/subjects/${subjectId}`,
        { method: "DELETE" }
      );
      setActiveCurriculumDetail(res.data);
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to remove subject.");
    }
  };

  const handlePublishCurriculum = async () => {
    if (!selectedCurriculumId) return;
    try {
      setSubmitting(true);
      const res = await apiFetch<CurriculumDetail>(
        `/api/v1/academics/curricula/${selectedCurriculumId}/publish`,
        { method: "POST" }
      );
      setActiveCurriculumDetail(res.data);
      setShowPublishModal(false);
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to publish curriculum scheme.");
    } finally {
      setSubmitting(false);
    }
  };

  // Sync selected subject credits when picking from catalog
  const onPickSubject = (subjId: string) => {
    setChosenSubjectId(subjId);
    const found = subjectsCatalog.find((s) => s.id === subjId);
    if (found) {
      setSubjCredits(found.credits);
      setSubjLectureHours(found.lecture_hours);
      setSubjTutorialHours(found.tutorial_hours);
      setSubjPracticalHours(found.practical_hours);
    }
  };

  // Filter schemes by program
  const filteredSchemes = curricula.filter(
    (c) => !selectedProgramId || c.program_id === selectedProgramId
  );

  // Group current scheme subjects by semester
  const semesterSubjects = (activeCurriculumDetail?.subjects || []).filter(
    (s) => s.semester_number === selectedSemester
  );
  const totalSemesterCredits = semesterSubjects.reduce(
    (acc, s) => acc + Number(s.credits || 0),
    0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <Link href="/app/academics" className="hover:underline">
            Academics
          </Link>
          <span>/</span>
          <span>Curricula & Versioning</span>
        </div>
        <div className="mt-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Curriculum Schemes & Versioning
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Statutory degree regulations, multi-semester roadmaps, and locked version history.
            </p>
          </div>
          {canManage && (
            <button
              onClick={() => {
                setFormError(null);
                if (programs.length > 0) setNewProgramId(programs[0].id);
                if (regulations.length > 0) setNewRegId(regulations[0].id);
                setShowCreateModal(true);
              }}
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition"
            >
              + Create Scheme Version
            </button>
          )}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-6 text-sm text-slate-500">
          <div className="w-5 h-5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mr-2" />
          Loading curricula schemes...
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      )}

      {/* Program Selector & Schemes Selector Bar */}
      <div className="flex flex-col sm:flex-row gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex-1">
          <label className="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 mb-1">
            Filter by Program
          </label>
          <select
            value={selectedProgramId}
            onChange={(e) => setSelectedProgramId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:text-white"
          >
            <option value="">All Programs</option>
            {programs.map((p) => (
              <option key={p.id} value={p.id}>
                {p.code} - {p.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 mb-1">
            Select Scheme & Version
          </label>
          <select
            value={selectedCurriculumId}
            onChange={(e) => setSelectedCurriculumId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 font-medium focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:text-white"
          >
            {filteredSchemes.length === 0 ? (
              <option value="">No curriculum schemes found</option>
            ) : (
              filteredSchemes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} (v{c.version}) - {c.status} {c.is_locked ? "🔒" : "📝"}
                </option>
              ))
            )}
          </select>
        </div>
      </div>

      {/* Main Curriculum Canvas */}
      {!activeCurriculumDetail ? (
        <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
          <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300">
            No Curriculum Scheme Selected
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            Select a curriculum version or create a new scheme version for your degree program.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Scheme Banner */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                    {activeCurriculumDetail.name}
                  </h2>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
                    v{activeCurriculumDetail.version}
                  </span>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      activeCurriculumDetail.status === "PUBLISHED"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                        : "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                    }`}
                  >
                    {activeCurriculumDetail.status}
                  </span>
                  {activeCurriculumDetail.is_locked && (
                    <span className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                      🔒 Immutable
                    </span>
                  )}
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                  <span>Program: <strong>{activeCurriculumDetail.program_name || activeCurriculumDetail.program_code}</strong></span>
                  <span>Regulation: <strong>{activeCurriculumDetail.regulation_code}</strong></span>
                  <span>Target Degree Credits: <strong>{activeCurriculumDetail.total_credits}</strong></span>
                  <span>Mapped Subjects: <strong>{activeCurriculumDetail.subjects.length}</strong></span>
                </div>
              </div>

              {/* Publish Action */}
              <div className="flex items-center gap-3">
                {!activeCurriculumDetail.is_locked && canPublish && (
                  <button
                    onClick={() => setShowPublishModal(true)}
                    className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 transition"
                  >
                    Publish & Lock Scheme
                  </button>
                )}
                {activeCurriculumDetail.is_locked && (
                  <div className="text-right">
                    <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                      ✓ Published & Active for Student Cohorts
                    </span>
                    <p className="text-[11px] text-slate-400">
                      Modifications require incrementing to a new scheme version.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Semester Navigator Tabs */}
          <div className="flex overflow-x-auto gap-2 border-b border-slate-200 pb-2 dark:border-slate-800">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((semNum) => {
              const count = (activeCurriculumDetail.subjects || []).filter(
                (s) => s.semester_number === semNum
              ).length;
              return (
                <button
                  key={semNum}
                  onClick={() => setSelectedSemester(semNum)}
                  className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2 text-xs font-semibold transition ${
                    selectedSemester === semNum
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                  }`}
                >
                  Semester {semNum}
                  <span
                    className={`ml-1 rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                      selectedSemester === semNum
                        ? "bg-indigo-700 text-white"
                        : "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                    }`}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Semester Subjects Grid */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between p-4 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Semester {selectedSemester} Subjects
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Total Term Credits: <strong>{totalSemesterCredits.toFixed(1)}</strong>
                </p>
              </div>

              {!activeCurriculumDetail.is_locked && canManage && (
                <button
                  onClick={() => {
                    setFormError(null);
                    setShowAddSubjectModal(true);
                  }}
                  className="inline-flex items-center justify-center rounded-lg bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-600 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:text-indigo-400 dark:hover:bg-indigo-900"
                >
                  + Add Subject to Semester {selectedSemester}
                </button>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm dark:divide-slate-800">
                <thead className="bg-slate-50 dark:bg-slate-800/50 text-xs uppercase font-semibold text-slate-500 dark:text-slate-400">
                  <tr>
                    <th className="py-3 px-4">Subject</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Mandatory</th>
                    <th className="py-3 px-4 text-center">Contact Hours (L-T-P)</th>
                    <th className="py-3 px-4 text-center">Credits</th>
                    {!activeCurriculumDetail.is_locked && <th className="py-3 px-4 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {semesterSubjects.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-10 text-center text-sm text-slate-500">
                        No subjects mapped to Semester {selectedSemester} yet.
                        {!activeCurriculumDetail.is_locked && " Click '+ Add Subject' above to assign."}
                      </td>
                    </tr>
                  ) : (
                    semesterSubjects.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="py-3 px-4">
                          <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                            {s.subject_code}
                          </span>{" "}
                          <span className="font-medium text-slate-900 dark:text-white">
                            {s.subject_name}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center rounded bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                            {s.category}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                              s.is_mandatory
                                ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400"
                                : "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400"
                            }`}
                          >
                            {s.is_mandatory ? "Compulsory" : `Elective (${s.elective_group || "Group"})`}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center font-mono text-xs text-slate-600 dark:text-slate-400">
                          {s.lecture_hours} - {s.tutorial_hours} - {s.practical_hours}
                        </td>
                        <td className="py-3 px-4 text-center font-mono font-bold text-slate-900 dark:text-white">
                          {Number(s.credits).toFixed(1)}
                        </td>
                        {!activeCurriculumDetail.is_locked && (
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => handleRemoveSubject(s.subject_id)}
                              className="text-xs font-semibold text-rose-600 hover:text-rose-800 dark:text-rose-400"
                            >
                              Remove
                            </button>
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Create Curriculum Scheme */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Create Curriculum Scheme Version
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateScheme} className="mt-4 space-y-4">
              {formError && (
                <div className="rounded-lg bg-rose-50 p-3 text-xs font-semibold text-rose-800 dark:bg-rose-950/50 dark:text-rose-300">
                  {formError}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Degree Program *
                  </label>
                  <select
                    value={newProgramId}
                    onChange={(e) => setNewProgramId(e.target.value)}
                    required
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  >
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.code} - {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Statutory Regulation *
                  </label>
                  <select
                    value={newRegId}
                    onChange={(e) => setNewRegId(e.target.value)}
                    required
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  >
                    {regulations.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.code} ({r.effective_year})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                  Scheme Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. B.Tech Computer Science 2024 Curriculum"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Scheme Version Number *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="99"
                    required
                    value={newVersion}
                    onChange={(e) => setNewVersion(parseInt(e.target.value, 10))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                  <p className="mt-1 text-[11px] text-slate-400">Version 1, 2, etc.</p>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Total Required Credits
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    value={newCredits}
                    onChange={(e) => setNewCredits(parseFloat(e.target.value))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                  Description / Board of Studies Notes
                </label>
                <textarea
                  rows={2}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {submitting ? "Creating..." : "Save Scheme"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Subject to Semester */}
      {showAddSubjectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Add Subject to Semester {selectedSemester}
              </h3>
              <button onClick={() => setShowAddSubjectModal(false)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>

            <form onSubmit={handleAddSubjectToSemester} className="mt-4 space-y-4">
              {formError && (
                <div className="rounded-lg bg-rose-50 p-3 text-xs font-semibold text-rose-800 dark:bg-rose-950/50 dark:text-rose-300">
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                  Subject from Catalog *
                </label>
                <select
                  value={chosenSubjectId}
                  onChange={(e) => onPickSubject(e.target.value)}
                  required
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                >
                  <option value="">-- Choose Subject --</option>
                  {subjectsCatalog.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.code} - {s.name} ({s.credits} Credits)
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Category *
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  >
                    {SUBJECT_CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Course Type
                  </label>
                  <div className="mt-3 flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="isMandatoryCheck"
                      checked={isMandatory}
                      onChange={(e) => setIsMandatory(e.target.checked)}
                      className="rounded text-indigo-600"
                    />
                    <label htmlFor="isMandatoryCheck" className="text-xs text-slate-700 dark:text-slate-300">
                      Mandatory / Compulsory
                    </label>
                  </div>
                </div>
              </div>

              {!isMandatory && (
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Elective Group Code
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. PE-I (Professional Elective 1)"
                    value={electiveGroup}
                    onChange={(e) => setElectiveGroup(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
              )}

              <div className="grid grid-cols-4 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Credits
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={subjCredits}
                    onChange={(e) => setSubjCredits(parseFloat(e.target.value))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                    L Hours
                  </label>
                  <input
                    type="number"
                    value={subjLectureHours}
                    onChange={(e) => setSubjLectureHours(parseInt(e.target.value, 10))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                    T Hours
                  </label>
                  <input
                    type="number"
                    value={subjTutorialHours}
                    onChange={(e) => setSubjTutorialHours(parseInt(e.target.value, 10))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                    P Hours
                  </label>
                  <input
                    type="number"
                    value={subjPracticalHours}
                    onChange={(e) => setSubjPracticalHours(parseInt(e.target.value, 10))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddSubjectModal(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {submitting ? "Adding..." : "Add to Semester"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Publish Confirmation */}
      {showPublishModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Confirm Curriculum Publishing
            </h3>
            <p className="mt-2 text-sm text-slate-600 leading-relaxed dark:text-slate-300">
              Publishing will <strong>permanently lock</strong> version {activeCurriculumDetail?.version} of{" "}
              <strong>{activeCurriculumDetail?.name}</strong>.
            </p>
            <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
              ⚠️ Once published, subjects cannot be added or deleted. Any future academic revisions must be released as a new version (v{(activeCurriculumDetail?.version ?? 1) + 1}).
            </p>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowPublishModal(false)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handlePublishCurriculum}
                disabled={submitting}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {submitting ? "Publishing..." : "Yes, Publish Scheme"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

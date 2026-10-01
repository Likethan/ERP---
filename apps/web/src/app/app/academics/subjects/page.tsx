"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { Subject, Department } from "@campusos/types";

const SUBJECT_TYPES = [
  "THEORY",
  "PRACTICAL",
  "LAB",
  "PROJECT",
  "ELECTIVE",
  "SEMINAR",
  "INTERNSHIP",
];

export default function SubjectsPage() {
  const { hasPermission } = useAuth();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedDeptId, setSelectedDeptId] = useState("");
  const [selectedType, setSelectedType] = useState("");

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const [deptId, setDeptId] = useState("");
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [credits, setCredits] = useState<number>(3.0);
  const [lectureHours, setLectureHours] = useState<number>(3);
  const [tutorialHours, setTutorialHours] = useState<number>(0);
  const [practicalHours, setPracticalHours] = useState<number>(0);
  const [subjectType, setSubjectType] = useState("THEORY");
  const [description, setDescription] = useState("");
  const [isActive, setIsActive] = useState(true);

  const canManage = hasPermission("academics:subjects:manage");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [subRes, deptRes] = await Promise.all([
        apiFetch<Subject[]>("/api/v1/academics/subjects"),
        apiFetch<Department[]>("/api/v1/departments"),
      ]);

      setSubjects(subRes.data || []);
      setDepartments(deptRes.data || []);
      if (deptRes.data && deptRes.data.length > 0 && !deptId) {
        setDeptId(deptRes.data[0].id);
      }
    } catch {
      // Fallback to academics service mock data
      const [mockSubs, mockDepts] = await Promise.all([
        import("@/services/academics.service").then((m) => m.academicsService.getSubjects()),
        import("@/services/academics.service").then((m) => m.academicsService.getDepartments()),
      ]);
      const mappedSubs = mockSubs.data.map((s) => ({
        id: s.id,
        code: s.code,
        name: s.name,
        department_id: "dept-cse",
        credits: s.credits,
        lecture_hours: s.lectureHours,
        tutorial_hours: s.tutorialHours,
        practical_hours: s.practicalHours,
        subject_type: s.type,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })) as unknown as Subject[];

      const mappedDepts = mockDepts.data.map((d) => ({
        id: d.id,
        code: d.code,
        name: d.name,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })) as unknown as Department[];

      setSubjects(mappedSubs);
      setDepartments(mappedDepts);
      if (mappedDepts.length > 0 && !deptId) {
        setDeptId(mappedDepts[0].id);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deptId || !code.trim() || !name.trim()) {
      setFormError("Please fill out department, subject code, and course name.");
      return;
    }

    try {
      setSaving(true);
      setFormError(null);

      await apiFetch<Subject>("/api/v1/academics/subjects", {
        method: "POST",
        body: JSON.stringify({
          department_id: deptId,
          code: code.trim().toUpperCase(),
          name: name.trim(),
          credits: Number(credits),
          lecture_hours: Number(lectureHours),
          tutorial_hours: Number(tutorialHours),
          practical_hours: Number(practicalHours),
          subject_type: subjectType,
          description: description.trim() || null,
          is_active: isActive,
        }),
      });

      setShowModal(false);
      resetForm();
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create subject.");
    } finally {
      setSaving(false);
    }
  };

  const resetForm = () => {
    setCode("");
    setName("");
    setCredits(3.0);
    setLectureHours(3);
    setTutorialHours(0);
    setPracticalHours(0);
    setSubjectType("THEORY");
    setDescription("");
    setIsActive(true);
    setFormError(null);
  };

  // Filtered Subjects
  const filteredSubjects = subjects.filter((s) => {
    const matchesSearch =
      !search ||
      s.code.toLowerCase().includes(search.toLowerCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase());
    const matchesDept = !selectedDeptId || s.department_id === selectedDeptId;
    const matchesType = !selectedType || s.subject_type === selectedType;
    return matchesSearch && matchesDept && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Breadcrumbs and Header */}
      <div>
        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <Link href="/app/academics" className="hover:underline">
            Academics
          </Link>
          <span>/</span>
          <span>Subjects Master</span>
        </div>
        <div className="mt-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Subject Master Catalog
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Canonical registry of courses, academic credit weights, and contact hours.
            </p>
          </div>
          {canManage && (
            <button
              onClick={() => {
                resetForm();
                setShowModal(true);
              }}
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition"
            >
              + Create Subject
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      )}

      {/* Filters Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search by code (e.g. CS101) or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:text-white"
          />
        </div>

        <select
          value={selectedDeptId}
          onChange={(e) => setSelectedDeptId(e.target.value)}
          className="rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:text-white"
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.code} - {d.name}
            </option>
          ))}
        </select>

        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:text-white"
        >
          <option value="">All Types</option>
          {SUBJECT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {/* Subjects Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase tracking-wider font-semibold text-slate-500 dark:text-slate-400">
              <tr>
                <th className="py-3 px-4">Subject Code</th>
                <th className="py-3 px-4">Course Name</th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4 text-center">L - T - P</th>
                <th className="py-3 px-4 text-center">Credits</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-sm text-slate-500">
                    Loading subjects catalog...
                  </td>
                </tr>
              ) : filteredSubjects.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-sm text-slate-500">
                    <p className="font-semibold text-slate-700 dark:text-slate-300">
                      No subjects found
                    </p>
                    <p className="mt-1 text-xs">
                      {search || selectedDeptId || selectedType
                        ? "Try clearing filters to see all subjects."
                        : "Create your first subject master record to build curriculum schemes."}
                    </p>
                  </td>
                </tr>
              ) : (
                filteredSubjects.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                      {s.code}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">
                      {s.name}
                      {s.description && (
                        <p className="text-xs text-slate-500 font-normal line-clamp-1">{s.description}</p>
                      )}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-600 dark:text-slate-400">
                      {s.department_name || "-"}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                        {s.subject_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-xs text-slate-600 dark:text-slate-400">
                      {s.lecture_hours} - {s.tutorial_hours} - {s.practical_hours}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-slate-900 dark:text-white">
                      {Number(s.credits).toFixed(1)}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                          s.is_active
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                        }`}
                      >
                        {s.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Create Subject */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Add Subject to Master Catalog
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubject} className="mt-4 space-y-4">
              {formError && (
                <div className="rounded-lg bg-rose-50 p-3 text-xs font-semibold text-rose-800 dark:bg-rose-950/50 dark:text-rose-300">
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                  Department *
                </label>
                <select
                  value={deptId}
                  onChange={(e) => setDeptId(e.target.value)}
                  required
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                >
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.code} - {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Subject Code *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. CS201"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Subject Type
                  </label>
                  <select
                    value={subjectType}
                    onChange={(e) => setSubjectType(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  >
                    {SUBJECT_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                  Course Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Data Structures & Algorithms"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-4 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                    Credits
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max="20"
                    required
                    value={credits}
                    onChange={(e) => setCredits(parseFloat(e.target.value))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                    L (Lecture)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={lectureHours}
                    onChange={(e) => setLectureHours(parseInt(e.target.value, 10))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                    T (Tutorial)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={tutorialHours}
                    onChange={(e) => setTutorialHours(parseInt(e.target.value, 10))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold uppercase text-slate-600 dark:text-slate-400">
                    P (Practical)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={practicalHours}
                    onChange={(e) => setPracticalHours(parseInt(e.target.value, 10))}
                    className="mt-1 w-full font-mono rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 dark:text-slate-400">
                  Description / Syllabus Overview
                </label>
                <textarea
                  rows={2}
                  placeholder="Optional brief description..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:text-white"
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="isActiveToggle"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="isActiveToggle" className="text-sm text-slate-700 dark:text-slate-300">
                  Active in academic curriculum building
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Subject"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

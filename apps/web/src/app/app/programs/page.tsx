"use client";

import React, { useEffect, useState } from "react";
import type { Department, Program } from "@campusos/types";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";

export default function ProgramsPage() {
  const { hasPermission } = useAuth();
  const [programs, setPrograms] = useState<Program[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDeptId, setSelectedDeptId] = useState<string>("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [showCreate, setShowCreate] = useState(false);
  const [deptId, setDeptId] = useState("");
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [degreeLevel, setDegreeLevel] = useState("UG");
  const [durationYears, setDurationYears] = useState("4.0");
  const [totalSemesters, setTotalSemesters] = useState(8);
  const [requiredCredits, setRequiredCredits] = useState(160);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const canManage = hasPermission("core:programs:manage");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (selectedDeptId) params.append("department_id", selectedDeptId);
      if (search) params.append("search", search);

      const qs = params.toString() ? `?${params.toString()}` : "";
      const [progRes, deptRes] = await Promise.all([
        apiFetch<Program[]>(`/api/v1/programs${qs}`),
        apiFetch<Department[]>("/api/v1/departments"),
      ]);
      setPrograms(progRes.data);
      setDepartments(deptRes.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load degree programs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadData();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, selectedDeptId]);

  const handleCreateProgram = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await apiFetch<Program>("/api/v1/programs", {
        method: "POST",
        body: JSON.stringify({
          department_id: deptId,
          code: code.trim().toUpperCase(),
          name: name.trim(),
          degree_level: degreeLevel,
          duration_years: parseFloat(durationYears),
          total_semesters: Number(totalSemesters),
          required_credits: Number(requiredCredits),
        }),
      });
      setShowCreate(false);
      setCode("");
      setName("");
      setDeptId("");
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create program");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Degree Programs</h1>
          <p className="mt-1 text-sm text-slate-400">
            Formal undergraduate, postgraduate, and doctoral degree curricula.
          </p>
        </div>
        {canManage && (
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-medium text-white hover:bg-indigo-500 transition-colors shadow-sm self-start sm:self-auto"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Create Program
          </button>
        )}
      </div>

      {/* Filter / Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full sm:max-w-md">
          <input
            type="text"
            placeholder="Search programs by name or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3.5 py-2 pl-9 text-xs text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
          />
          <svg
            className="absolute left-3 top-2.5 h-4 w-4 text-slate-500"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="2"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
        </div>

        <select
          value={selectedDeptId}
          onChange={(e) => setSelectedDeptId(e.target.value)}
          className="w-full sm:w-auto rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} ({d.code})
            </option>
          ))}
        </select>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-rose-800 bg-rose-950/40 p-4 text-sm text-rose-300">
          {error}
        </div>
      )}

      {/* Programs Table */}
      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="text-xs text-slate-400">Loading degree programs...</div>
        </div>
      ) : programs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center">
          <svg className="mx-auto h-10 w-10 text-slate-600 mb-2" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342" />
          </svg>
          <p className="text-sm font-medium text-slate-300">No programs found.</p>
          <p className="mt-1 text-xs text-slate-500">
            {search || selectedDeptId ? "Try clearing your filters." : "Create your first degree program under a department."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50 shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-slate-900 text-slate-400 uppercase">
              <tr>
                <th className="px-5 py-3 font-semibold">Program Code</th>
                <th className="px-5 py-3 font-semibold">Program Name</th>
                <th className="px-5 py-3 font-semibold">Department</th>
                <th className="px-5 py-3 font-semibold">Level</th>
                <th className="px-5 py-3 font-semibold">Duration</th>
                <th className="px-5 py-3 font-semibold">Credits</th>
                <th className="px-5 py-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {programs.map((p) => (
                <tr key={p.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-indigo-400 font-medium">{p.code}</td>
                  <td className="px-5 py-3.5 font-medium text-white">{p.name}</td>
                  <td className="px-5 py-3.5 text-slate-400">{p.department_name || "Department"}</td>
                  <td className="px-5 py-3.5">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-300">
                      {p.degree_level}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-slate-300">{p.duration_years} Years ({p.total_semesters} Sem)</td>
                  <td className="px-5 py-3.5 text-slate-300">{p.required_credits}</td>
                  <td className="px-5 py-3.5">
                    <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-400">
                      Active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Program Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-semibold text-white">Create Degree Program</h3>
              <button onClick={() => setShowCreate(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            {formError && (
              <div className="rounded-lg border border-rose-800 bg-rose-950/40 p-3 text-xs text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateProgram} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Department</label>
                <select
                  required
                  value={deptId}
                  onChange={(e) => setDeptId(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">Select Offering Department...</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Program Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. BE-CSE, BTECH-AIDS"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Degree Level</label>
                  <select
                    value={degreeLevel}
                    onChange={(e) => setDegreeLevel(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="UG">Undergraduate (UG)</option>
                    <option value="PG">Postgraduate (PG)</option>
                    <option value="DOCTORAL">Doctoral (Ph.D)</option>
                    <option value="DIPLOMA">Diploma</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Program Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Bachelor of Engineering in Computer Science and Engineering"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Duration (Years)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    max="6"
                    required
                    value={durationYears}
                    onChange={(e) => setDurationYears(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Total Semesters</label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    required
                    value={totalSemesters}
                    onChange={(e) => setTotalSemesters(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Required Credits</label>
                  <input
                    type="number"
                    min="20"
                    max="300"
                    required
                    value={requiredCredits}
                    onChange={(e) => setRequiredCredits(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-500 transition-colors disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Create Program"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

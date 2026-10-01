"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { AttendancePolicy } from "@campusos/types";

export default function AttendancePoliciesPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [policies, setPolicies] = useState<AttendancePolicy[]>([]);
  const [modalOpen, setModalOpen] = useState(false);

  const [policyForm, setPolicyForm] = useState({
    name: "Institutional Baseline Attendance Policy",
    minimum_percentage: 75.0,
    warning_threshold_percentage: 80.0,
    critical_threshold_percentage: 65.0,
    condonation_percentage: 65.0,
    late_grace_minutes: 10,
    late_weight: 0.5,
    excused_counts_as_present: true,
    on_leave_counts_as_present: true,
    exclude_excused_from_total: false,
    effective_from: new Date().toISOString().split("T")[0],
    effective_to: "",
  });

  async function loadPolicies() {
    try {
      setLoading(true);
      setError(null);

      const res = await apiFetch<AttendancePolicy[]>("/api/v1/attendance/policies");
      setPolicies(res.data || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load attendance policies.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPolicies();
  }, []);

  async function handleSavePolicy(e: React.FormEvent) {
    e.preventDefault();
    try {
      setError(null);
      setSuccessMsg(null);

      await apiFetch("/api/v1/attendance/policies", {
        method: "POST",
        body: JSON.stringify({
          ...policyForm,
          effective_to: policyForm.effective_to || undefined,
        }),
      });

      setSuccessMsg("Attendance policy configured and versioned successfully.");
      setModalOpen(false);
      await loadPolicies();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save attendance policy.");
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
            Institutional Attendance Policies
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Define eligibility thresholds, condonation boundaries, late weighting, and leave treatment rules.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {hasPermission("attendance_policy:create") && (
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
            >
              + Define Policy
            </button>
          )}
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

      {/* Policy Concept Info Banner */}
      <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4 text-xs text-blue-900 dark:border-blue-900/40 dark:bg-blue-950/20 dark:text-blue-300">
        <span className="font-bold">Hierarchical Resolution Engine: </span>
        Policies resolve via Course Offering &rarr; Semester &rarr; Program &rarr; Department &rarr; Institution Baseline.
        Attendance percentages are dynamically calculated without permanently modifying historical session data.
      </div>

      {/* Policies Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading attendance policies...</div>
        ) : policies.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No attendance policies configured.
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Create an institutional baseline policy defining the 75% minimum threshold.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 border-b border-slate-100 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Policy Name</th>
                  <th className="px-4 py-3">Min %</th>
                  <th className="px-4 py-3">Warning %</th>
                  <th className="px-4 py-3">Critical %</th>
                  <th className="px-4 py-3">Late Penalty</th>
                  <th className="px-4 py-3">Leave Treatment</th>
                  <th className="px-4 py-3">Effective Range</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {policies.map((pol) => (
                  <tr key={pol.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {pol.name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {pol.course_offering_id
                          ? "Course Offering Scope"
                          : pol.program_id
                          ? "Program Scope"
                          : "Institutional Baseline"}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap font-bold text-slate-900 dark:text-white">
                      {pol.minimum_percentage}%
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-amber-500 font-semibold">
                      {pol.warning_threshold_percentage}%
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-rose-600 dark:text-rose-400 font-semibold">
                      {pol.critical_threshold_percentage}%
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                      {pol.late_weight * 100}% credit ({pol.late_grace_minutes}m grace)
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                      {pol.on_leave_counts_as_present ? "Counts as Present" : "Excluded from Denominator"}
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                      {pol.effective_from || "Always"} &rarr; {pol.effective_to || "Present"}
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                          pol.is_active
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                      >
                        {pol.is_active ? "Active" : "Archived"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Define Policy */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Configure Attendance Policy
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Rules versioning ensures historical calculation reproducibility without retroactive distortion.
            </p>

            <form onSubmit={handleSavePolicy} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Policy Name *
                </label>
                <input
                  type="text"
                  required
                  value={policyForm.name}
                  onChange={(e) => setPolicyForm({ ...policyForm, name: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Min % *
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    max="100"
                    required
                    value={policyForm.minimum_percentage}
                    onChange={(e) =>
                      setPolicyForm({
                        ...policyForm,
                        minimum_percentage: parseFloat(e.target.value) || 75.0,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Warning % *
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    max="100"
                    required
                    value={policyForm.warning_threshold_percentage}
                    onChange={(e) =>
                      setPolicyForm({
                        ...policyForm,
                        warning_threshold_percentage: parseFloat(e.target.value) || 80.0,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Critical % *
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    max="100"
                    required
                    value={policyForm.critical_threshold_percentage}
                    onChange={(e) =>
                      setPolicyForm({
                        ...policyForm,
                        critical_threshold_percentage: parseFloat(e.target.value) || 65.0,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Late Grace (Mins)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="60"
                    value={policyForm.late_grace_minutes}
                    onChange={(e) =>
                      setPolicyForm({
                        ...policyForm,
                        late_grace_minutes: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Late Session Weight (0 - 1.0)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1.0"
                    value={policyForm.late_weight}
                    onChange={(e) =>
                      setPolicyForm({
                        ...policyForm,
                        late_weight: parseFloat(e.target.value) || 0.5,
                      })
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policyForm.on_leave_counts_as_present}
                    onChange={(e) =>
                      setPolicyForm({
                        ...policyForm,
                        on_leave_counts_as_present: e.target.checked,
                      })
                    }
                    className="rounded text-indigo-600"
                  />
                  <span>Approved Leave counts as Present session in calculation</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policyForm.excused_counts_as_present}
                    onChange={(e) =>
                      setPolicyForm({
                        ...policyForm,
                        excused_counts_as_present: e.target.checked,
                      })
                    }
                    className="rounded text-indigo-600"
                  />
                  <span>Excused Absence counts as Present session in calculation</span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
                >
                  Save Policy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useCallback, useEffect, useState } from "react";
import type { Campus, Department } from "@campusos/types";
import { organizationService } from "@/services/organization.service";
import { useAuth } from "@/lib/auth-context";

export default function DepartmentsPage() {
  const { hasPermission } = useAuth();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [campuses, setCampuses] = useState<Campus[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create Modal
  const [showCreate, setShowCreate] = useState(false);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [deptType, setDeptType] = useState("ACADEMIC");
  const [campusId, setCampusId] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null);

  const canManage = hasPermission("core:departments:manage");

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [deptRes, campRes] = await Promise.all([
        organizationService.listDepartments(undefined, search),
        organizationService.listCampuses(),
      ]);
      setDepartments(deptRes.data);
      setCampuses(campRes.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load departments");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadData();
    }, 250);
    return () => clearTimeout(timer);
  }, [loadData]);

  const handleCreateDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await organizationService.createDepartment({
        code: code.trim().toUpperCase(),
        name: name.trim(),
        department_type: deptType,
        campus_id: campusId || undefined,
      });
      setShowCreate(false);
      setCode("");
      setName("");
      setCampusId("");
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create department");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateDepartment = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingDepartment) return;
    setSubmitting(true);
    setFormError(null);
    try {
      await organizationService.updateDepartment(editingDepartment.id, {
        name: name.trim(),
        department_type: deptType,
        campus_id: campusId || null,
        is_active: editingDepartment.is_active,
      });
      setEditingDepartment(null);
      setShowCreate(false);
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to update department");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Academic Departments</h1>
          <p className="mt-1 text-sm text-slate-400">
            Authoritative faculty and program organizational units.
          </p>
        </div>
        {canManage && (
          <button
            onClick={() => { setEditingDepartment(null); setFormError(null); setCode(""); setName(""); setCampusId(""); setShowCreate(true); }}
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-medium text-white hover:bg-indigo-500 transition-colors shadow-sm self-start sm:self-auto"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Create Department
          </button>
        )}
      </div>

      {/* Filter / Search Bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search by department name or code..."
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
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-rose-800 bg-rose-950/40 p-4 text-sm text-rose-300">
          {error}
        </div>
      )}

      {/* Departments Table */}
      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="text-xs text-slate-400">Loading departments...</div>
        </div>
      ) : departments.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center">
          <svg className="mx-auto h-10 w-10 text-slate-600 mb-2" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" />
          </svg>
          <p className="text-sm font-medium text-slate-300">No departments found.</p>
          <p className="mt-1 text-xs text-slate-500">
            {search ? "Try adjusting your search criteria." : "Create your first department to begin building the academic structure."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50 shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-slate-900 text-slate-400 uppercase">
              <tr>
                <th className="px-5 py-3 font-semibold">Code</th>
                <th className="px-5 py-3 font-semibold">Department Name</th>
                <th className="px-5 py-3 font-semibold">Classification</th>
                <th className="px-5 py-3 font-semibold">Head of Department (HOD)</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                {canManage && <th className="px-5 py-3 font-semibold text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {departments.map((d) => (
                <tr key={d.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-indigo-400 font-medium">{d.code}</td>
                  <td className="px-5 py-3.5 font-medium text-white">{d.name}</td>
                  <td className="px-5 py-3.5">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] text-slate-300">
                      {d.department_type}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    {d.hod_name ? (
                      <span className="text-slate-200 font-medium">{d.hod_name}</span>
                    ) : (
                      <span className="text-slate-500 italic">Not Assigned</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${d.is_active ? "bg-emerald-500/10 text-emerald-400" : "bg-slate-800 text-slate-400"}`}>
                      {d.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  {canManage && <td className="px-5 py-3.5 text-right"><button onClick={() => { setFormError(null); setEditingDepartment(d); setCode(d.code); setName(d.name); setDeptType(d.department_type); setCampusId(d.campus_id || ""); setShowCreate(true); }} className="rounded-md border border-slate-700 px-2.5 py-1.5 text-[11px] font-medium text-slate-200 hover:bg-slate-800">Edit</button></td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Department Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-semibold text-white">{editingDepartment ? "Edit Academic Department" : "Create Academic Department"}</h3>
              <button onClick={() => { setShowCreate(false); setEditingDepartment(null); }} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            {formError && (
              <div className="rounded-lg border border-rose-800 bg-rose-950/40 p-3 text-xs text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={editingDepartment ? handleUpdateDepartment : handleCreateDepartment} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Department Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CSE, ECE, MECH, AIDS"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  disabled={Boolean(editingDepartment)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Department Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Computer Science & Engineering"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Department Classification</label>
                <select
                  value={deptType}
                  onChange={(e) => setDeptType(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="ACADEMIC">ACADEMIC (Teaching & Research)</option>
                  <option value="ADMINISTRATIVE">ADMINISTRATIVE (Operations & Office)</option>
                  <option value="SUPPORT">SUPPORT (Infrastructure & Facilities)</option>
                </select>
              </div>

              {campuses.length > 0 && (
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Campus Branch (Optional)</label>
                  <select
                    value={campusId}
                    onChange={(e) => setCampusId(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="">Institution-Wide (All Campuses)</option>
                    {campuses.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.code})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {editingDepartment && <label className="flex items-center gap-2 text-slate-300"><input type="checkbox" checked={editingDepartment.is_active} onChange={(e) => setEditingDepartment({ ...editingDepartment, is_active: e.target.checked })} className="rounded border-slate-700 bg-slate-950 text-indigo-500 focus:ring-indigo-500" /> Department is active</label>}

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => { setShowCreate(false); setEditingDepartment(null); }}
                  className="rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-500 transition-colors disabled:opacity-50"
                >
                  {submitting ? "Saving..." : editingDepartment ? "Save changes" : "Create Department"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import type { Campus, Institution } from "@campusos/types";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";

export default function InstitutionPage() {
  const { hasPermission } = useAuth();
  const [institution, setInstitution] = useState<Institution | null>(null);
  const [campuses, setCampuses] = useState<Campus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Campus modal state
  const [showAddCampus, setShowAddCampus] = useState(false);
  const [campusCode, setCampusCode] = useState("");
  const [campusName, setCampusName] = useState("");
  const [campusCity, setCampusCity] = useState("");
  const [campusAddress, setCampusAddress] = useState("");
  const [submittingCampus, setSubmittingCampus] = useState(false);
  const [campusError, setCampusError] = useState<string | null>(null);

  const canManage = hasPermission("core:institutions:manage") || hasPermission("core:campuses:manage");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [instRes, campRes] = await Promise.all([
        apiFetch<Institution>("/api/v1/institutions"),
        apiFetch<Campus[]>("/api/v1/campuses"),
      ]);
      setInstitution(instRes.data);
      setCampuses(campRes.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load institution data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateCampus = async (e: React.FormEvent) => {
    e.preventDefault();
    setCampusError(null);
    setSubmittingCampus(true);
    try {
      await apiFetch<Campus>("/api/v1/campuses", {
        method: "POST",
        body: JSON.stringify({
          code: campusCode.trim().toUpperCase(),
          name: campusName.trim(),
          city: campusCity.trim(),
          address: campusAddress.trim(),
        }),
      });
      setShowAddCampus(false);
      setCampusCode("");
      setCampusName("");
      setCampusCity("");
      setCampusAddress("");
      await loadData();
    } catch (err: unknown) {
      setCampusError(err instanceof Error ? err.message : "Failed to create campus branch");
    } finally {
      setSubmittingCampus(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm text-slate-400">Loading institution details...</div>
      </div>
    );
  }

  if (error || !institution) {
    return (
      <div className="rounded-lg border border-rose-800 bg-rose-950/40 p-4 text-rose-300">
        {error || "Institution record not found"}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-white">{institution.legal_name}</h1>
          <span className="rounded-md bg-indigo-500/10 px-2.5 py-1 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
            {institution.code}
          </span>
          <span className="rounded-md bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
            Active Tenant
          </span>
        </div>
        <p className="mt-1 text-sm text-slate-400">
          Canonical operational record for this institution and associated campus sites.
        </p>
      </div>

      {/* Institution Metadata Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Organization</h3>
          <div className="space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Short Name:</span>
              <span className="font-medium text-slate-200">{institution.short_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Website:</span>
              <span className="font-medium text-indigo-400">{institution.website || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Timezone:</span>
              <span className="font-medium text-slate-200">{institution.default_timezone}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Base Currency:</span>
              <span className="font-medium text-slate-200">{institution.currency_code}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Contact Details</h3>
          <div className="space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Email:</span>
              <span className="font-medium text-slate-200">{institution.contact_email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Phone:</span>
              <span className="font-medium text-slate-200">{institution.contact_phone}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Registered Address</h3>
          <div className="text-sm text-slate-300 space-y-0.5">
            <div>{institution.address_line1}</div>
            <div>
              {institution.city}, {institution.state} {institution.postal_code}
            </div>
            <div className="text-slate-400">{institution.country}</div>
          </div>
        </div>
      </div>

      {/* Campuses Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Campus Branches</h2>
            <p className="text-xs text-slate-400">Physical campuses belonging to this institution</p>
          </div>
          {canManage && (
            <button
              onClick={() => setShowAddCampus(true)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-medium text-white hover:bg-indigo-500 transition-colors shadow-sm"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add Campus Site
            </button>
          )}
        </div>

        {campuses.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-8 text-center">
            <p className="text-sm font-medium text-slate-300">No campus sites provisioned yet.</p>
            <p className="mt-1 text-xs text-slate-400">
              Add your main campus branch to begin organizing academic departments.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-800 bg-slate-900 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-5 py-3.5 font-medium">Campus Code</th>
                  <th className="px-5 py-3.5 font-medium">Name</th>
                  <th className="px-5 py-3.5 font-medium">City</th>
                  <th className="px-5 py-3.5 font-medium">Address</th>
                  <th className="px-5 py-3.5 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {campuses.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-3.5 font-mono text-xs text-indigo-400">{c.code}</td>
                    <td className="px-5 py-3.5 font-medium text-white">{c.name}</td>
                    <td className="px-5 py-3.5">{c.city}</td>
                    <td className="px-5 py-3.5 text-slate-400 max-w-xs truncate">{c.address}</td>
                    <td className="px-5 py-3.5">
                      <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-400">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Campus Modal */}
      {showAddCampus && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-semibold text-white">Add Campus Site</h3>
              <button
                onClick={() => setShowAddCampus(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {campusError && (
              <div className="rounded-lg border border-rose-800 bg-rose-950/40 p-3 text-xs text-rose-300">
                {campusError}
              </div>
            )}

            <form onSubmit={handleCreateCampus} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Campus Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. MAIN, CITY, NORTH"
                  value={campusCode}
                  onChange={(e) => setCampusCode(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Campus Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Central Technology Campus"
                  value={campusName}
                  onChange={(e) => setCampusName(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">City</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Coimbatore"
                  value={campusCity}
                  onChange={(e) => setCampusCity(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Full Physical Address</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Physical site location details..."
                  value={campusAddress}
                  onChange={(e) => setCampusAddress(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none resize-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddCampus(false)}
                  className="rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCampus}
                  className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-500 transition-colors disabled:opacity-50"
                >
                  {submittingCampus ? "Provisioning..." : "Create Campus"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

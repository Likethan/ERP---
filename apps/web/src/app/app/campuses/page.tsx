"use client";

import React, { useCallback, useEffect, useState } from "react";
import type { Campus, Institution } from "@campusos/types";
import { organizationService } from "@/services/organization.service";
import { useAuth } from "@/lib/auth-context";

export default function CampusesPage() {
  const { hasPermission } = useAuth();
  const [campuses, setCampuses] = useState<Campus[]>([]);
  const [institution, setInstitution] = useState<Institution | null>(null);
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
  const [editingCampus, setEditingCampus] = useState<Campus | null>(null);

  const canManage = hasPermission("core:campuses:manage");

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [instRes, campRes] = await Promise.all([
        organizationService.getInstitution(),
        organizationService.listCampuses(),
      ]);
      setInstitution(instRes.data);
      setCampuses(campRes.data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load campus locations",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleCreateCampus = async (e: React.FormEvent) => {
    e.preventDefault();
    setCampusError(null);
    setSubmittingCampus(true);
    try {
      if (editingCampus) {
        await organizationService.updateCampus(editingCampus.id, {
          name: campusName.trim(),
          city: campusCity.trim(),
          address: campusAddress.trim(),
          is_active: editingCampus.is_active,
        });
      } else {
        await organizationService.createCampus({
          code: campusCode.trim().toUpperCase(),
          name: campusName.trim(),
          city: campusCity.trim(),
          address: campusAddress.trim(),
        });
      }
      setShowAddCampus(false);
      setEditingCampus(null);
      setCampusCode("");
      setCampusName("");
      setCampusCity("");
      setCampusAddress("");
      await loadData();
    } catch (err: unknown) {
      setCampusError(
        err instanceof Error ? err.message : "Failed to create campus branch",
      );
    } finally {
      setSubmittingCampus(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Campus Locations
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Physical campus locations and institutional branches for{" "}
            {institution?.legal_name || "the institution"}.
          </p>
        </div>
        {canManage && (
          <button
            onClick={() => {
              setEditingCampus(null);
              setCampusCode("");
              setCampusName("");
              setCampusCity("");
              setCampusAddress("");
              setCampusError(null);
              setShowAddCampus(true);
            }}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-colors self-start sm:self-auto"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Add Campus Branch
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadData} className="underline hover:text-red-200">
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-500 text-sm">
          <svg
            className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
          Loading campus locations...
        </div>
      ) : campuses.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-16 text-center text-slate-500 space-y-2">
          <p className="text-base font-semibold text-slate-300">
            No campuses configured
          </p>
          <p className="text-sm text-slate-400">
            Add your primary campus to associate departments, classrooms, and
            facilities.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campuses.map((c) => (
            <div
              key={c.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm hover:border-slate-700 transition-colors flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-xs uppercase px-2 py-0.5 rounded bg-blue-950/80 border border-blue-800 text-blue-400">
                    {c.code}
                  </span>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                      c.is_active
                        ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800"
                        : "bg-slate-800 text-slate-400 border border-slate-700"
                    }`}
                  >
                    {c.is_active ? "Operational" : "Inactive"}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">{c.name}</h3>
                  <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                    <svg
                      className="w-3.5 h-3.5 text-slate-500"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                    {c.city || "Primary Branch"}
                  </p>
                </div>
                {c.address && (
                  <p className="text-xs text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                    {c.address}
                  </p>
                )}
              </div>

              <div className="pt-4 mt-4 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
                <span>Campus ID: {c.id.substring(0, 8)}...</span>
                {canManage && (
                  <button
                    onClick={() => {
                      setEditingCampus(c);
                      setCampusCode(c.code);
                      setCampusName(c.name);
                      setCampusCity(c.city);
                      setCampusAddress(c.address || "");
                      setCampusError(null);
                      setShowAddCampus(true);
                    }}
                    className="rounded-md border border-slate-700 px-2.5 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-800"
                  >
                    Edit
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CREATE CAMPUS MODAL */}
      {showAddCampus && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-white">
                {editingCampus ? "Edit Campus Location" : "Add Campus Location"}
              </h2>
              <button
                onClick={() => {
                  setShowAddCampus(false);
                  setEditingCampus(null);
                }}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {campusError && (
              <div className="p-3 bg-red-950/40 border border-red-800 text-red-300 text-xs rounded-lg">
                {campusError}
              </div>
            )}

            <form onSubmit={handleCreateCampus} className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Campus Code *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="MAIN"
                    value={campusCode}
                    onChange={(e) => setCampusCode(e.target.value)}
                    disabled={Boolean(editingCampus)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono uppercase focus:outline-none focus:border-blue-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    City / Region *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Bangalore"
                    value={campusCity}
                    onChange={(e) => setCampusCity(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Campus Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Main Technology Campus"
                  value={campusName}
                  onChange={(e) => setCampusName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Physical Address
                </label>
                <textarea
                  rows={2}
                  placeholder="Street address, postal code, landmarks..."
                  value={campusAddress}
                  onChange={(e) => setCampusAddress(e.target.value)}
                  required
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 text-sm"
                />
              </div>

              {editingCampus && (
                <label className="flex items-center gap-2 text-xs text-slate-300">
                  <input
                    type="checkbox"
                    checked={editingCampus.is_active}
                    onChange={(e) =>
                      setEditingCampus({
                        ...editingCampus,
                        is_active: e.target.checked,
                      })
                    }
                    className="rounded border-slate-700 bg-slate-950 text-indigo-500 focus:ring-indigo-500"
                  />{" "}
                  Campus is operational
                </label>
              )}

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddCampus(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCampus}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg disabled:opacity-50"
                >
                  {submittingCampus
                    ? "Saving..."
                    : editingCampus
                      ? "Save changes"
                      : "Create Campus"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

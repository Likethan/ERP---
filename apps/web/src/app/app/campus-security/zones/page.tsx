"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Building,
  Users,
  AlertTriangle,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  Lock,
  Compass,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import { ClearanceLevel, SecurityZone } from "@/types/campus-security";

export default function SecurityZonesPage() {
  const [zones, setZones] = useState<SecurityZone[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState<string>("ALL");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Form state
  const [form, setForm] = useState({
    code: "",
    name: "",
    clearance_level: "CAMPUS_GENERAL" as ClearanceLevel,
    building_name: "",
    floor_number: 1,
    requires_escort: false,
    max_occupancy: 50,
    emergency_assembly_point: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await CampusSecurityService.listZones();
      setZones(data);
    } catch (err) {
      console.error("Failed to load security zones:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateZone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.code || !form.name) return;

    try {
      setSubmitting(true);
      await CampusSecurityService.createZone({
        code: form.code,
        name: form.name,
        clearance_level: form.clearance_level,
        building_name: form.building_name,
        floor_number: Number(form.floor_number),
        requires_escort: form.requires_escort,
        max_occupancy: Number(form.max_occupancy),
        emergency_assembly_point: form.emergency_assembly_point,
      });

      setNotification({
        type: "success",
        message: `Security zone ${form.code} (${form.name}) successfully registered.`,
      });
      setIsModalOpen(false);
      setForm({
        code: "",
        name: "",
        clearance_level: "CAMPUS_GENERAL",
        building_name: "",
        floor_number: 1,
        requires_escort: false,
        max_occupancy: 50,
        emergency_assembly_point: "",
      });
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to create security zone. Please verify your inputs.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const filteredZones = zones.filter((z) => {
    const matchesSearch =
      z.name.toLowerCase().includes(search.toLowerCase()) ||
      z.code.toLowerCase().includes(search.toLowerCase()) ||
      (z.building_name && z.building_name.toLowerCase().includes(search.toLowerCase()));

    const matchesFilter = levelFilter === "ALL" || z.clearance_level === levelFilter;
    return matchesSearch && matchesFilter;
  });

  const highSecurityCount = zones.filter((z) => z.clearance_level === "HIGH_SECURITY").length;
  const restrictedCount = zones.filter((z) => z.clearance_level === "RESTRICTED").length;
  const escortRequiredCount = zones.filter((z) => z.requires_escort).length;

  const getClearanceBadge = (level: ClearanceLevel) => {
    switch (level) {
      case "HIGH_SECURITY":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border border-red-200 dark:border-red-800">
            <Lock className="w-3 h-3" /> HIGH SECURITY
          </span>
        );
      case "RESTRICTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            <AlertTriangle className="w-3 h-3" /> RESTRICTED
          </span>
        );
      case "FACULTY_STAFF_ONLY":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            <ShieldCheck className="w-3 h-3" /> STAFF & FACULTY
          </span>
        );
      case "CAMPUS_GENERAL":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle2 className="w-3 h-3" /> CAMPUS GENERAL
          </span>
        );
      case "PUBLIC":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            PUBLIC ACCESS
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Campus Security Clearance Zones
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
              Perimeter Demarcation
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Configure physical clearance tiers, access rules, escort mandates, and evacuation assembly hubs across institutional facilities.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Register Security Zone
        </button>
      </div>

      {/* Navigation tabs */}
      <SecurityNav />

      {/* Notification */}
      {notification && (
        <div
          className={`p-4 rounded-lg flex items-center justify-between text-sm ${
            notification.type === "success"
              ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800"
              : "bg-red-50 text-red-800 dark:bg-red-950/50 dark:text-red-200 border border-red-200 dark:border-red-800"
          }`}
        >
          <span>{notification.message}</span>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs font-bold"
          >
            DISMISS
          </button>
        </div>
      )}

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Zones</span>
            <Building className="w-5 h-5 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white mt-2">{zones.length}</div>
          <div className="text-xs text-slate-500 mt-1">Institutional sectors mapped</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">High Security</span>
            <ShieldAlert className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-2">{highSecurityCount}</div>
          <div className="text-xs text-slate-500 mt-1">Data centers & server vaults</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Restricted Areas</span>
            <AlertTriangle className="w-5 h-5 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-2">{restrictedCount}</div>
          <div className="text-xs text-slate-500 mt-1">Research labs & chemical storage</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Escort Required</span>
            <Users className="w-5 h-5 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 mt-2">{escortRequiredCount}</div>
          <div className="text-xs text-slate-500 mt-1">Visitors require authorized escort</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search code, name, or building..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-2 sm:pb-0">
          <Filter className="w-4 h-4 text-slate-400 mr-1 shrink-0" />
          {["ALL", "HIGH_SECURITY", "RESTRICTED", "FACULTY_STAFF_ONLY", "CAMPUS_GENERAL", "PUBLIC"].map(
            (lvl) => (
              <button
                key={lvl}
                onClick={() => setLevelFilter(lvl)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  levelFilter === lvl
                    ? "bg-indigo-600 text-white"
                    : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                {lvl.replace(/_/g, " ")}
              </button>
            )
          )}
        </div>
      </div>

      {/* Zones Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-6 py-4">Zone Code & Name</th>
                <th className="px-6 py-4">Clearance Level</th>
                <th className="px-6 py-4">Building & Floor</th>
                <th className="px-6 py-4">Escort Policy</th>
                <th className="px-6 py-4">Max Occupancy</th>
                <th className="px-6 py-4">Assembly Point</th>
                <th className="px-6 py-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    Loading security clearance zones...
                  </td>
                </tr>
              ) : filteredZones.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    No security zones matching the current criteria.
                  </td>
                </tr>
              ) : (
                filteredZones.map((zone) => (
                  <tr key={zone.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900 dark:text-white">{zone.name}</div>
                      <div className="font-mono text-xs text-indigo-600 dark:text-indigo-400 mt-0.5">
                        {zone.code}
                      </div>
                    </td>
                    <td className="px-6 py-4">{getClearanceBadge(zone.clearance_level)}</td>
                    <td className="px-6 py-4">
                      <div className="text-slate-900 dark:text-slate-200">{zone.building_name || "Campus Main"}</div>
                      <div className="text-xs text-slate-500">Floor {zone.floor_number ?? 1}</div>
                    </td>
                    <td className="px-6 py-4">
                      {zone.requires_escort ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 dark:text-amber-400">
                          <Users className="w-3.5 h-3.5" /> Escort Required
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> Self-Access
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-mono text-xs">{zone.max_occupancy ? `${zone.max_occupancy} persons` : "Uncapped"}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1 text-xs text-slate-600 dark:text-slate-400">
                        <Compass className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                        <span>{zone.emergency_assembly_point || "Assembly Point A (Campus Quad)"}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {zone.is_active ? (
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                          ACTIVE
                        </span>
                      ) : (
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                          DECOMMISSIONED
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Zone Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Lock className="w-5 h-5 text-indigo-600" />
                Register New Security Zone
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateZone} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Zone Code *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. ZONE-LAB-B"
                    value={form.code}
                    onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Zone Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Advanced Robotics Lab"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Clearance Level
                </label>
                <select
                  value={form.clearance_level}
                  onChange={(e) => setForm({ ...form, clearance_level: e.target.value as ClearanceLevel })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                >
                  <option value="PUBLIC">PUBLIC</option>
                  <option value="CAMPUS_GENERAL">CAMPUS GENERAL</option>
                  <option value="FACULTY_STAFF_ONLY">FACULTY & STAFF ONLY</option>
                  <option value="RESTRICTED">RESTRICTED</option>
                  <option value="HIGH_SECURITY">HIGH SECURITY</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Building Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Tech Block A"
                    value={form.building_name}
                    onChange={(e) => setForm({ ...form, building_name: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Floor Number
                  </label>
                  <input
                    type="number"
                    value={form.floor_number}
                    onChange={(e) => setForm({ ...form, floor_number: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Max Occupancy
                  </label>
                  <input
                    type="number"
                    value={form.max_occupancy}
                    onChange={(e) => setForm({ ...form, max_occupancy: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Assembly Point
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Quad Evac Area 2"
                    value={form.emergency_assembly_point}
                    onChange={(e) => setForm({ ...form, emergency_assembly_point: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="requires_escort"
                  checked={form.requires_escort}
                  onChange={(e) => setForm({ ...form, requires_escort: e.target.checked })}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                />
                <label htmlFor="requires_escort" className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Mandatory Security Escort for Non-Cleared Personnel
                </label>
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {submitting ? "Registering..." : "Create Zone"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


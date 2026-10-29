"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  Building,
  Radio,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Phone,
  DoorOpen,
  Car,
  Users,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import { CheckpointType, SecurityCheckpoint } from "@/types/campus-security";

export default function CheckpointsPage() {
  const [checkpoints, setCheckpoints] = useState<SecurityCheckpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [mannedFilter, setMannedFilter] = useState<string>("ALL");

  // Create Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Form state
  const [form, setForm] = useState({
    code: "",
    name: "",
    checkpoint_type: "MAIN_GATE" as CheckpointType,
    location_description: "",
    is_manned: true,
    operating_hours: "24x7",
    guard_post_phone: "+91-44-2200-GATE",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await CampusSecurityService.listCheckpoints();
      setCheckpoints(data);
    } catch (err) {
      console.error("Failed to load checkpoints:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateCheckpoint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.code || !form.name || !form.location_description) return;

    try {
      setSubmitting(true);
      await CampusSecurityService.createCheckpoint({
        code: form.code,
        name: form.name,
        checkpoint_type: form.checkpoint_type,
        location_description: form.location_description,
        is_manned: form.is_manned,
        operating_hours: form.operating_hours,
        guard_post_phone: form.guard_post_phone,
      });

      setNotification({
        type: "success",
        message: `Gate checkpoint ${form.code} (${form.name}) created successfully.`,
      });
      setIsModalOpen(false);
      setForm({
        code: "",
        name: "",
        checkpoint_type: "MAIN_GATE",
        location_description: "",
        is_manned: true,
        operating_hours: "24x7",
        guard_post_phone: "+91-44-2200-GATE",
      });
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to create checkpoint. Please check inputs.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const filteredCheckpoints = checkpoints.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.code.toLowerCase().includes(search.toLowerCase()) ||
      c.location_description.toLowerCase().includes(search.toLowerCase());

    const matchesType = typeFilter === "ALL" || c.checkpoint_type === typeFilter;
    const matchesManned =
      mannedFilter === "ALL" ||
      (mannedFilter === "MANNED" && c.is_manned) ||
      (mannedFilter === "UNMANNED" && !c.is_manned);

    return matchesSearch && matchesType && matchesManned;
  });

  const mannedCount = checkpoints.filter((c) => c.is_manned).length;
  const unmannedCount = checkpoints.filter((c) => !c.is_manned).length;
  const continuousCount = checkpoints.filter((c) => c.operating_hours.includes("24x7")).length;

  const getTypeIcon = (type: CheckpointType) => {
    switch (type) {
      case "VEHICLE_BARRIER":
        return <Car className="w-4 h-4 text-amber-500" />;
      case "PEDESTRIAN_TURNSTILE":
        return <Users className="w-4 h-4 text-blue-500" />;
      case "EMERGENCY_EXIT":
        return <DoorOpen className="w-4 h-4 text-red-500" />;
      case "MAIN_GATE":
      case "SERVICE_GATE":
      default:
        return <Building className="w-4 h-4 text-indigo-500" />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Campus Gates & Access Checkpoints
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
              Entry Infrastructure
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Configure physical ingress portals, turnstiles, automated vehicle barriers, and guard posts across campus perimeters.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Register Checkpoint
        </button>
      </div>

      {/* Nav */}
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

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Checkpoints</span>
            <Building className="w-5 h-5 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white mt-2">{checkpoints.length}</div>
          <div className="text-xs text-slate-500 mt-1">Authorized ingress portals</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Manned Guard Posts</span>
            <Users className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-2">{mannedCount}</div>
          <div className="text-xs text-slate-500 mt-1">Stationed security officers</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Automated Turnstiles</span>
            <Radio className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-2">{unmannedCount}</div>
          <div className="text-xs text-slate-500 mt-1">Badge and token-actuated</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Continuous 24x7 Gates</span>
            <Clock className="w-5 h-5 text-purple-500" />
          </div>
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-2">{continuousCount}</div>
          <div className="text-xs text-slate-500 mt-1">Always-open access points</div>
        </div>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search code, name, location..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto overflow-x-auto pb-2 sm:pb-0">
          <div className="flex items-center gap-1.5">
            <Filter className="w-4 h-4 text-slate-400 mr-1 shrink-0" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              <option value="ALL">All Types</option>
              <option value="MAIN_GATE">Main Gate</option>
              <option value="VEHICLE_BARRIER">Vehicle Barrier</option>
              <option value="PEDESTRIAN_TURNSTILE">Turnstile</option>
              <option value="SERVICE_GATE">Service Gate</option>
              <option value="EMERGENCY_EXIT">Emergency Exit</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <select
              value={mannedFilter}
              onChange={(e) => setMannedFilter(e.target.value)}
              className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              <option value="ALL">Manned & Automated</option>
              <option value="MANNED">Manned Guard Posts</option>
              <option value="UNMANNED">Automated / Unmanned</option>
            </select>
          </div>
        </div>
      </div>

      {/* Checkpoints Grid / Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full p-12 text-center text-slate-400 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
            Loading checkpoint infrastructure...
          </div>
        ) : filteredCheckpoints.length === 0 ? (
          <div className="col-span-full p-12 text-center text-slate-400 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
            No gate checkpoints matching criteria.
          </div>
        ) : (
          filteredCheckpoints.map((chk) => (
            <div
              key={chk.id}
              className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition-all space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getTypeIcon(chk.checkpoint_type)}
                  <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                    {chk.code}
                  </span>
                </div>
                {chk.is_manned ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                    <CheckCircle2 className="w-3 h-3" /> MANNED POST
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                    AUTOMATED
                  </span>
                )}
              </div>

              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-base">{chk.name}</h3>
                <p className="text-xs text-slate-500 mt-1">{chk.location_description}</p>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Type:</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {chk.checkpoint_type.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Hours:</span>
                  <span className="font-mono text-slate-800 dark:text-slate-200">{chk.operating_hours}</span>
                </div>
                {chk.guard_post_phone && (
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Guard Phone:</span>
                    <span className="font-mono text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
                      <Phone className="w-3 h-3" /> {chk.guard_post_phone}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Building className="w-5 h-5 text-indigo-600" />
                Register Physical Gate Checkpoint
              </h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateCheckpoint} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Checkpoint Code *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. GATE-WEST-01"
                    value={form.code}
                    onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Gate / Post Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. West Campus Vehicle Entrance"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Checkpoint Type *
                </label>
                <select
                  value={form.checkpoint_type}
                  onChange={(e) => setForm({ ...form, checkpoint_type: e.target.value as any })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                >
                  <option value="MAIN_GATE">Main Perimeter Gate</option>
                  <option value="VEHICLE_BARRIER">Automated Vehicle Boom Barrier</option>
                  <option value="PEDESTRIAN_TURNSTILE">Pedestrian Turnstile Bank</option>
                  <option value="SERVICE_GATE">Logistics / Service Gate</option>
                  <option value="EMERGENCY_EXIT">Emergency Egress Exit</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Location Description *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Western Perimeter, adjacent to Sports Complex"
                  value={form.location_description}
                  onChange={(e) => setForm({ ...form, location_description: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Operating Hours
                  </label>
                  <input
                    type="text"
                    value={form.operating_hours}
                    onChange={(e) => setForm({ ...form, operating_hours: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Guard Post Phone
                  </label>
                  <input
                    type="text"
                    value={form.guard_post_phone}
                    onChange={(e) => setForm({ ...form, guard_post_phone: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="is_manned"
                  checked={form.is_manned}
                  onChange={(e) => setForm({ ...form, is_manned: e.target.checked })}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                />
                <label htmlFor="is_manned" className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Stationed Security Personnel (Manned Guard Post)
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
                  {submitting ? "Registering..." : "Save Checkpoint"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


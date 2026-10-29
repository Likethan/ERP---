"use client";

import React, { useEffect, useState } from "react";
import {
  Footprints,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Plus,
  QrCode,
  ShieldCheck,
  UserCheck,
  Search,
  Filter,
  FileText,
  BadgeCheck,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import {
  PatrolCheckpointRecord,
  PatrolRecordStatus,
  PatrolShift,
  SecurityCheckpoint,
  SecurityPatrolPlan,
} from "@/types/campus-security";

export default function SecurityPatrolsPage() {
  const [plans, setPlans] = useState<SecurityPatrolPlan[]>([]);
  const [records, setRecords] = useState<PatrolCheckpointRecord[]>([]);
  const [checkpoints, setCheckpoints] = useState<SecurityCheckpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Create Plan Modal
  const [isPlanModalOpen, setIsPlanModalOpen] = useState(false);
  const [planSubmitting, setPlanSubmitting] = useState(false);

  // Record Scan Modal
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [scanSubmitting, setScanSubmitting] = useState(false);

  // Supervisor Review Modal
  const [reviewingRecord, setReviewingRecord] = useState<PatrolCheckpointRecord | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // New Plan Form
  const [planForm, setPlanForm] = useState({
    title: "",
    shift_name: "MORNING_SHIFT" as PatrolShift,
    frequency_hours: 2,
    assigned_team_name: "Patrol Alpha",
    checkpoints_sequence: [] as string[],
  });

  // New Scan Form
  const [scanForm, setScanForm] = useState({
    plan_id: "",
    checkpoint_id: "",
    officer_name: "Officer J. Vance",
    scheduled_round_time: new Date().toISOString().slice(0, 16),
    status: "COMPLETED" as PatrolRecordStatus,
    verification_token: `NFC-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
    observations: "Perimeter secure, doors locked, lighting operational.",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [plansData, recordsData, checkpointsData] = await Promise.all([
        CampusSecurityService.listPatrolPlans(),
        CampusSecurityService.listPatrolRecords(),
        CampusSecurityService.listCheckpoints(),
      ]);
      setPlans(plansData);
      setRecords(recordsData);
      setCheckpoints(checkpointsData);

      if (plansData.length > 0 && !scanForm.plan_id) {
        setScanForm((prev) => ({ ...prev, plan_id: plansData[0].id }));
      }
      if (checkpointsData.length > 0 && !scanForm.checkpoint_id) {
        setScanForm((prev) => ({ ...prev, checkpoint_id: checkpointsData[0].id }));
      }
    } catch (err) {
      console.error("Failed to load patrol operations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!planForm.title || !planForm.assigned_team_name) return;

    try {
      setPlanSubmitting(true);
      const sequence = planForm.checkpoints_sequence.length > 0
        ? planForm.checkpoints_sequence
        : checkpoints.map((c) => c.id);

      await CampusSecurityService.createPatrolPlan({
        title: planForm.title,
        shift_name: planForm.shift_name,
        frequency_hours: Number(planForm.frequency_hours),
        assigned_team_name: planForm.assigned_team_name,
        checkpoints_sequence: sequence,
      });

      setNotification({
        type: "success",
        message: `Patrol plan "${planForm.title}" registered successfully.`,
      });
      setIsPlanModalOpen(false);
      setPlanForm({
        title: "",
        shift_name: "MORNING_SHIFT",
        frequency_hours: 2,
        assigned_team_name: "Patrol Alpha",
        checkpoints_sequence: [],
      });
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to create patrol plan.",
      });
    } finally {
      setPlanSubmitting(false);
    }
  };

  const handleRecordScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scanForm.plan_id || !scanForm.checkpoint_id) return;

    try {
      setScanSubmitting(true);
      await CampusSecurityService.scanPatrolCheckpoint({
        plan_id: scanForm.plan_id,
        checkpoint_id: scanForm.checkpoint_id,
        officer_name: scanForm.officer_name,
        scheduled_round_time: new Date(scanForm.scheduled_round_time).toISOString(),
        status: scanForm.status,
        verification_token: scanForm.verification_token,
        observations: scanForm.observations,
      });

      setNotification({
        type: "success",
        message: "Patrol checkpoint scan verified and logged to audit trail.",
      });
      setIsScanModalOpen(false);
      setScanForm((prev) => ({
        ...prev,
        verification_token: `NFC-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
      }));
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to log checkpoint scan.",
      });
    } finally {
      setScanSubmitting(false);
    }
  };

  const handleReviewRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewingRecord) return;

    try {
      setReviewSubmitting(true);
      await CampusSecurityService.reviewPatrolRecord(reviewingRecord.id, reviewNotes);
      setNotification({
        type: "success",
        message: "Patrol round scan reviewed and approved by supervisor.",
      });
      setReviewingRecord(null);
      setReviewNotes("");
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to submit supervisor review.",
      });
    } finally {
      setReviewSubmitting(false);
    }
  };

  const filteredRecords = records.filter((r) => {
    const matchesSearch =
      r.officer_name.toLowerCase().includes(search.toLowerCase()) ||
      (r.observations && r.observations.toLowerCase().includes(search.toLowerCase())) ||
      (r.verification_token && r.verification_token.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const completedCount = records.filter((r) => r.status === "COMPLETED").length;
  const exceptionCount = records.filter((r) => r.status === "EXCEPTION_NOTED" || r.status === "MISSED").length;
  const reviewedCount = records.filter((r) => r.supervisor_reviewed).length;
  const completionRate = records.length > 0 ? Math.round((completedCount / records.length) * 100) : 100;

  const getCheckpointName = (id: string) => {
    const cp = checkpoints.find((c) => c.id === id);
    return cp ? `${cp.name} (${cp.code})` : id;
  };

  const getPlanTitle = (id: string) => {
    const p = plans.find((pl) => pl.id === id);
    return p ? p.title : id;
  };

  const getStatusBadge = (status: PatrolRecordStatus) => {
    switch (status) {
      case "COMPLETED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> COMPLETED
          </span>
        );
      case "DELAYED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
            <Clock className="w-3 h-3 text-amber-600" /> DELAYED
          </span>
        );
      case "EXCEPTION_NOTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300">
            <AlertTriangle className="w-3 h-3 text-purple-600" /> EXCEPTION
          </span>
        );
      case "MISSED":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300">
            MISSED
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
              Guard Patrol & Tour Verification
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
              NFC & Geofenced
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Schedule recurring security patrol routes, record cryptographic NFC checkpoint scans, and audit supervisor reviews.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsPlanModalOpen(true)}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Patrol Route
          </button>
          <button
            onClick={() => setIsScanModalOpen(true)}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow-sm transition-colors"
          >
            <QrCode className="w-4 h-4" />
            Record Checkpoint Scan
          </button>
        </div>
      </div>

      {/* Nav */}
      <SecurityNav />

      {/* Notification banner */}
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
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Patrol Plans</span>
            <Footprints className="w-5 h-5 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white mt-2">{plans.length}</div>
          <div className="text-xs text-slate-500 mt-1">Scheduled campus routes</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Completion Rate</span>
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-2">{completionRate}%</div>
          <div className="text-xs text-slate-500 mt-1">{completedCount} of {records.length} scans on time</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Exceptions / Missed</span>
            <AlertTriangle className="w-5 h-5 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-2">{exceptionCount}</div>
          <div className="text-xs text-slate-500 mt-1">Discrepancies flagged by guards</div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Supervisor Reviews</span>
            <BadgeCheck className="w-5 h-5 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-white mt-2">{reviewedCount}</div>
          <div className="text-xs text-slate-500 mt-1">Formally signed off tours</div>
        </div>
      </div>

      {/* Patrol Plans Strip */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
          <Footprints className="w-4 h-4 text-indigo-500" />
          Active Guard Tour Routines
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {plans.map((p) => (
            <div
              key={p.id}
              className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">{p.plan_code}</span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-300">
                  {p.shift_name.replace(/_/g, " ")}
                </span>
              </div>
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">{p.title}</h3>
              <div className="text-xs text-slate-500">
                Team: <strong className="text-slate-700 dark:text-slate-300">{p.assigned_team_name}</strong> | Every{" "}
                <strong className="text-slate-700 dark:text-slate-300">{p.frequency_hours} hrs</strong>
              </div>
              <div className="text-xs text-slate-400">
                Sequence: {p.checkpoints_sequence?.length || 0} Checkpoints configured
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Checkpoint Scan Log Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search officer, token, notes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400 shrink-0" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300"
            >
              <option value="ALL">All Scan Statuses</option>
              <option value="COMPLETED">Completed</option>
              <option value="DELAYED">Delayed</option>
              <option value="EXCEPTION_NOTED">Exception Noted</option>
              <option value="MISSED">Missed</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-6 py-4">Timestamp & NFC</th>
                <th className="px-6 py-4">Patrol Plan</th>
                <th className="px-6 py-4">Scanned Checkpoint</th>
                <th className="px-6 py-4">Patrol Officer</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Observations</th>
                <th className="px-6 py-4 text-right">Review</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    Loading patrol scans...
                  </td>
                </tr>
              ) : filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    No checkpoint scans recorded matching criteria.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {rec.scanned_at ? new Date(rec.scanned_at).toLocaleTimeString() : "Pending"}
                      </div>
                      <div className="font-mono text-[11px] text-indigo-600 dark:text-indigo-400 mt-0.5">
                        {rec.verification_token || "NFC-UNVERIFIED"}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-slate-900 dark:text-slate-200 text-xs font-medium">
                        {getPlanTitle(rec.plan_id)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900 dark:text-slate-100 text-xs">
                        {getCheckpointName(rec.checkpoint_id)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-xs text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                        <UserCheck className="w-3.5 h-3.5 text-slate-400" />
                        {rec.officer_name}
                      </div>
                    </td>
                    <td className="px-6 py-4">{getStatusBadge(rec.status)}</td>
                    <td className="px-6 py-4 max-w-xs truncate" title={rec.observations}>
                      <span className="text-xs text-slate-600 dark:text-slate-400">{rec.observations || "—"}</span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {rec.supervisor_reviewed ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Reviewed
                        </span>
                      ) : (
                        <button
                          onClick={() => setReviewingRecord(rec)}
                          className="px-2.5 py-1 text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 rounded border border-indigo-200 dark:border-indigo-900"
                        >
                          Sign Off
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* New Patrol Plan Modal */}
      {isPlanModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Footprints className="w-5 h-5 text-indigo-600" />
                Configure New Patrol Route
              </h2>
              <button
                onClick={() => setIsPlanModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreatePlan} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Patrol Route Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. North Perimeter & Research Wing Sweep"
                  value={planForm.title}
                  onChange={(e) => setPlanForm({ ...planForm, title: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Shift *
                  </label>
                  <select
                    value={planForm.shift_name}
                    onChange={(e) => setPlanForm({ ...planForm, shift_name: e.target.value as any })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  >
                    <option value="MORNING_SHIFT">Morning Shift (06:00 - 14:00)</option>
                    <option value="AFTERNOON_SHIFT">Afternoon Shift (14:00 - 22:00)</option>
                    <option value="NIGHT_SHIFT">Night Shift (22:00 - 06:00)</option>
                    <option value="WEEKEND_SHIFT">Weekend Shift</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Round Frequency (Hours) *
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={24}
                    value={planForm.frequency_hours}
                    onChange={(e) => setPlanForm({ ...planForm, frequency_hours: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Assigned Guard Team *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Patrol Squad Beta"
                  value={planForm.assigned_team_name}
                  onChange={(e) => setPlanForm({ ...planForm, assigned_team_name: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsPlanModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={planSubmitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {planSubmitting ? "Creating..." : "Save Patrol Route"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Record Scan Modal */}
      {isScanModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <QrCode className="w-5 h-5 text-indigo-600" />
                Record Checkpoint Tour Scan
              </h2>
              <button
                onClick={() => setIsScanModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleRecordScan} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Patrol Plan *
                </label>
                <select
                  value={scanForm.plan_id}
                  onChange={(e) => setScanForm({ ...scanForm, plan_id: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                >
                  {plans.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.title} ({p.shift_name})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Target Checkpoint *
                </label>
                <select
                  value={scanForm.checkpoint_id}
                  onChange={(e) => setScanForm({ ...scanForm, checkpoint_id: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                >
                  {checkpoints.map((cp) => (
                    <option key={cp.id} value={cp.id}>
                      {cp.name} ({cp.code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Officer Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={scanForm.officer_name}
                    onChange={(e) => setScanForm({ ...scanForm, officer_name: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Scan Status *
                  </label>
                  <select
                    value={scanForm.status}
                    onChange={(e) => setScanForm({ ...scanForm, status: e.target.value as any })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  >
                    <option value="COMPLETED">COMPLETED (Normal)</option>
                    <option value="DELAYED">DELAYED</option>
                    <option value="EXCEPTION_NOTED">EXCEPTION NOTED</option>
                    <option value="MISSED">MISSED</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  NFC Tag / Verification Token
                </label>
                <input
                  type="text"
                  value={scanForm.verification_token}
                  onChange={(e) => setScanForm({ ...scanForm, verification_token: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Field Observations
                </label>
                <textarea
                  rows={3}
                  value={scanForm.observations}
                  onChange={(e) => setScanForm({ ...scanForm, observations: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsScanModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={scanSubmitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {scanSubmitting ? "Logging..." : "Confirm Scan"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Review Modal */}
      {reviewingRecord && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-md shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <BadgeCheck className="w-5 h-5 text-indigo-600" />
                Supervisor Sign-Off Review
              </h2>
              <button
                onClick={() => setReviewingRecord(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleReviewRecord} className="p-6 space-y-4">
              <p className="text-sm text-slate-600 dark:text-slate-300">
                You are reviewing patrol record for officer{" "}
                <strong className="text-slate-900 dark:text-white">{reviewingRecord.officer_name}</strong> at{" "}
                <strong className="text-slate-900 dark:text-white">{getCheckpointName(reviewingRecord.checkpoint_id)}</strong>.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Supervisor Notes / Sign-Off Comments
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Verified camera footage; round timing and perimeter check confirmed satisfactory."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setReviewingRecord(null)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reviewSubmitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {reviewSubmitting ? "Signing..." : "Sign Off & Approve"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


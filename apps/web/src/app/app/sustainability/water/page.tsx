"use client";

import { useEffect, useState } from "react";
import {
  Droplets,
  AlertTriangle,
  CheckCircle2,
  Plus,
  Activity,
  Waves,
  Wrench,
  TrendingDown,
  CloudRain,
} from "lucide-react";
import { SustainabilityNav } from "../../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../../services/sustainability.service";
import { WaterIncidentRecord } from "../../../../types/sustainability";

export default function SustainabilityWaterPage() {
  const [incidents, setIncidents] = useState<WaterIncidentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showReportModal, setShowReportModal] = useState(false);

  // Form State
  const [location, setLocation] = useState("");
  const [incidentType, setIncidentType] = useState("LEAK_PIPE");
  const [estimatedLoss, setEstimatedLoss] = useState(2500);
  const [severity, setSeverity] = useState<"LOW" | "MEDIUM" | "HIGH" | "CRITICAL">("MEDIUM");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await sustainabilityService.getWaterIncidents();
        setIncidents(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleReport(e: React.FormEvent) {
    e.preventDefault();
    try {
      const code = `INC-WTR-${Date.now().toString().slice(-4)}`;
      const created = await sustainabilityService.reportWaterIncident({
        campus_id: "c0000000-0000-0000-0000-000000000001",
        incident_code: code,
        incident_type: incidentType,
        location,
        estimated_loss_litres: Number(estimatedLoss),
        severity,
        remediation_notes: notes,
      });
      setIncidents((prev) => [created, ...prev]);
      setShowReportModal(false);
      setLocation("");
      setNotes("");
    } catch (err) {
      console.error("Failed to report water incident", err);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="Campus Water Resources Balance & Leak Remediation"
        subtitle="Tracking municipal extraction, ground borewell levels, STP tertiary recycling, and plumbing incident corrective actions."
      />

      {/* Campus Water Balance Ledger */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Municipal Supply</span>
            <span className="p-2 rounded-lg bg-blue-950 text-blue-400 border border-blue-800">
              <Droplets className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">
            45,000 <span className="text-xs font-normal text-slate-400">kL / month</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Metrowater Bulk Intake Pipeline</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Borewell Recharge</span>
            <span className="p-2 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Waves className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-cyan-400">
            22,500 <span className="text-xs font-normal text-slate-400">kL / month</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Permitted under CGWA NOC #8821</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">STP Recycled Water</span>
            <span className="p-2 rounded-lg bg-emerald-950 text-emerald-400 border border-emerald-800">
              <Droplets className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">
            43,500 <span className="text-xs font-normal text-slate-400">kL (64.5%)</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Tertiary treated for cooling towers & turf</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Rainwater Harvested</span>
            <span className="p-2 rounded-lg bg-indigo-950 text-indigo-400 border border-indigo-800">
              <CloudRain className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-indigo-400">
            18,200 <span className="text-xs font-normal text-slate-400">kL Storage</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">12 interconnected recharge percolation pits</p>
        </div>
      </div>

      {/* Incident List Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Active & Resolved Water Leak Incidents
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Automatic linkage with Facilities asset maintenance work orders.
          </p>
        </div>
        <button
          onClick={() => setShowReportModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" /> Report Water Leak
        </button>
      </div>

      {/* Incidents Table */}
      {loading ? (
        <div className="flex items-center justify-center p-20 text-slate-400">
          <Activity className="w-6 h-6 animate-spin mr-2 text-emerald-500" />
          Loading water incident registry...
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-semibold">
                <th className="py-3 px-4">Incident Code</th>
                <th className="py-3 px-4">Location</th>
                <th className="py-3 px-4">Classification</th>
                <th className="py-3 px-4">Estimated Loss</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Remediation Status</th>
                <th className="py-3 px-4">Reported At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {incidents.map((inc) => (
                <tr key={inc.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3.5 px-4 font-mono font-bold text-slate-200">
                    {inc.incident_code}
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-slate-100">{inc.location}</div>
                    {inc.remediation_notes && (
                      <div className="text-[11px] text-slate-400 mt-0.5">{inc.remediation_notes}</div>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300">
                      {inc.incident_type.replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-bold text-cyan-400">
                    {inc.estimated_loss_litres.toLocaleString()} L
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        inc.severity === "CRITICAL" || inc.severity === "HIGH"
                          ? "bg-red-950 text-red-400 border border-red-800"
                          : "bg-amber-950 text-amber-400 border border-amber-800"
                      }`}
                    >
                      {inc.severity}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-semibold ${
                        inc.status === "REPAIRED" || inc.status === "CLOSED"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-blue-950 text-blue-400 border border-blue-800"
                      }`}
                    >
                      {inc.status === "REPAIRED" || inc.status === "CLOSED" ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : (
                        <Wrench className="w-3 h-3" />
                      )}
                      {inc.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                    {new Date(inc.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Report Modal */}
      {showReportModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-xl">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Droplets className="w-5 h-5 text-blue-400" />
              Report Water Leakage / Loss Incident
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Dispatches prompt alert to estate plumbing response team.
            </p>

            <form onSubmit={handleReport} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Location</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Science Block Riser A"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Incident Type</label>
                <select
                  value={incidentType}
                  onChange={(e) => setIncidentType(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                >
                  <option value="LEAK_PIPE">Pipe Burst / Joint Leak</option>
                  <option value="OVERFLOW_TANK">Overhead Tank Overflow</option>
                  <option value="BOREWELL_FAULT">Borewell Submersible Pump Fault</option>
                  <option value="VALVE_FAILURE">Pressure Valve Failure</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Estimated Loss (Litres)</label>
                  <input
                    type="number"
                    value={estimatedLoss}
                    onChange={(e) => setEstimatedLoss(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Severity</label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value as any)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Remediation / Inspection Notes</label>
                <textarea
                  rows={2}
                  placeholder="Details of damage or immediate valve shut-off..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowReportModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white"
                >
                  Submit Incident
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


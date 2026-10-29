"use client";

import { useEffect, useState } from "react";
import {
  Zap,
  Sun,
  Flame,
  AlertTriangle,
  Plus,
  Activity,
  CheckCircle2,
  Clock,
  Filter,
} from "lucide-react";
import { SustainabilityNav } from "../../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../../services/sustainability.service";
import { ResourceMeasurement, ResourceType } from "../../../../types/sustainability";

export default function SustainabilityEnergyPage() {
  const [measurements, setMeasurements] = useState<ResourceMeasurement[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [showLogModal, setShowLogModal] = useState(false);

  // Form State
  const [building, setBuilding] = useState("Main Academic Complex");
  const [meterCode, setMeterCode] = useState("MTR-ELEC-MAC-01");
  const [resourceType, setResourceType] = useState<ResourceType>("ELECTRICITY_GRID");
  const [readingVal, setReadingVal] = useState(4500);
  const [expectedBaseline, setExpectedBaseline] = useState(4200);

  useEffect(() => {
    async function load() {
      try {
        const data = await sustainabilityService.getMeasurements();
        setMeasurements(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleLog(e: React.FormEvent) {
    e.preventDefault();
    try {
      const now = new Date();
      const past = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      const created = await sustainabilityService.recordMeasurement({
        campus_id: "c0000000-0000-0000-0000-000000000001",
        building_name: building,
        meter_code: meterCode,
        resource_type: resourceType,
        period_start: past.toISOString(),
        period_end: now.toISOString(),
        reading_value: Number(readingVal),
        unit: "kWh",
        source_type: "IOT_SENSOR",
        baseline_expected_value: Number(expectedBaseline),
      });
      setMeasurements((prev) => [created, ...prev]);
      setShowLogModal(false);
    } catch (err) {
      console.error("Failed to record measurement", err);
    }
  }

  const filtered = measurements.filter((m) => {
    if (filterType === "ANOMALIES") return m.is_anomaly;
    if (filterType !== "ALL") return m.resource_type === filterType;
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="Multi-Source Campus Energy Monitoring & Peak Anomaly Engine"
        subtitle="Live telemetry capturing grid power import, rooftop solar PV generation, and stationary diesel gensets."
      />

      {/* Real-Time Energy Balances */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">TANGEDCO Grid Import</span>
            <span className="p-2 rounded-lg bg-amber-950 text-amber-400 border border-amber-800">
              <Zap className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">
            682,500 <span className="text-xs font-normal text-slate-400">kWh YTD</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">High Tension (HT) 11 kV Substation Feeder</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Rooftop Solar Generated</span>
            <span className="p-2 rounded-lg bg-emerald-950 text-emerald-400 border border-emerald-800">
              <Sun className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">
            254,800 <span className="text-xs font-normal text-slate-400">kWh YTD</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">500 kWp Phase-1 Bifacial Plant Capacity</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase">Genset Fuel Consumption</span>
            <span className="p-2 rounded-lg bg-red-950 text-red-400 border border-red-800">
              <Flame className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 text-2xl font-bold text-red-400">
            12,500 <span className="text-xs font-normal text-slate-400">Litres Diesel</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Emergency backup during grid maintenance outages</p>
        </div>
      </div>

      {/* Control Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <div className="flex gap-1.5 bg-slate-900 p-1 rounded-lg border border-slate-800">
            {["ALL", "ELECTRICITY_GRID", "SOLAR_GENERATION", "ANOMALIES"].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterType(tab)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                  filterType === tab
                    ? "bg-emerald-600 text-white font-semibold"
                    : "text-slate-300 hover:text-white"
                }`}
              >
                {tab === "ELECTRICITY_GRID"
                  ? "Grid Power"
                  : tab === "SOLAR_GENERATION"
                  ? "Solar Generation"
                  : tab === "ANOMALIES"
                  ? "Anomalies Only"
                  : "All Records"}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={() => setShowLogModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" /> Log Energy Reading
        </button>
      </div>

      {/* Telemetry Table */}
      {loading ? (
        <div className="flex items-center justify-center p-20 text-slate-400">
          <Activity className="w-6 h-6 animate-spin mr-2 text-emerald-500" />
          Loading energy telemetry...
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-semibold">
                <th className="py-3 px-4">Building & Meter</th>
                <th className="py-3 px-4">Resource Type</th>
                <th className="py-3 px-4">Reading</th>
                <th className="py-3 px-4">Expected Baseline</th>
                <th className="py-3 px-4">Variance</th>
                <th className="py-3 px-4">Status & Anomaly</th>
                <th className="py-3 px-4">Period</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((m) => (
                <tr key={m.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-slate-200">{m.building_name}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{m.meter_code}</div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300">
                      {m.resource_type.replace("_", " ")}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-bold text-slate-100">
                    {m.reading_value.toLocaleString()} {m.unit}
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">
                    {m.baseline_expected_value ? `${m.baseline_expected_value.toLocaleString()} ${m.unit}` : "—"}
                  </td>
                  <td className="py-3.5 px-4">
                    {m.variance_pct ? (
                      <span
                        className={`font-semibold ${
                          m.variance_pct > 30 ? "text-amber-400" : "text-slate-300"
                        }`}
                      >
                        {m.variance_pct > 0 ? `+${m.variance_pct}%` : `${m.variance_pct}%`}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    {m.is_anomaly ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-red-950 text-red-400 border border-red-800">
                        <AlertTriangle className="w-3 h-3" />
                        {m.anomaly_severity || "ANOMALY"}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                        <CheckCircle2 className="w-3 h-3" /> NORMAL
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                    {new Date(m.period_end).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Manual Measurement Log Modal */}
      {showLogModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-xl">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              Log Energy Telemetry Point
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Records are evaluated against baseline standard deviation for immediate anomaly triggering.
            </p>

            <form onSubmit={handleLog} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Building / Zone</label>
                <input
                  type="text"
                  required
                  value={building}
                  onChange={(e) => setBuilding(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Meter Code</label>
                <input
                  type="text"
                  required
                  value={meterCode}
                  onChange={(e) => setMeterCode(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Resource Classification</label>
                <select
                  value={resourceType}
                  onChange={(e) => setResourceType(e.target.value as ResourceType)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                >
                  <option value="ELECTRICITY_GRID">Electricity (Grid)</option>
                  <option value="SOLAR_GENERATION">Rooftop Solar PV</option>
                  <option value="DIESEL_GENSET">Diesel Generator Backup</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Reading (kWh)</label>
                  <input
                    type="number"
                    required
                    value={readingVal}
                    onChange={(e) => setReadingVal(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Expected Baseline</label>
                  <input
                    type="number"
                    value={expectedBaseline}
                    onChange={(e) => setExpectedBaseline(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowLogModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white"
                >
                  Log Reading
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


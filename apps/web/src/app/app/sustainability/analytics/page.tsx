"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  TrendingDown,
  Building,
  Zap,
  Activity,
  Layers,
  Calendar,
  Flame,
} from "lucide-react";
import { SustainabilityNav } from "../../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../../services/sustainability.service";
import { SustainabilityDashboardOverview } from "../../../../types/sustainability";

interface BuildingEnergyStats {
  name: string;
  sqm: number;
  annualKwh: number;
  intensityKwhSqm: number;
  solarSharePct: number;
  status: "EFFICIENT" | "MODERATE" | "HIGH_LOAD";
}

const MOCK_BUILDING_STATS: BuildingEnergyStats[] = [
  {
    name: "Main Academic Complex",
    sqm: 18500,
    annualKwh: 1240000,
    intensityKwhSqm: 67.0,
    solarSharePct: 45.0,
    status: "EFFICIENT",
  },
  {
    name: "Technology Research Tower",
    sqm: 12000,
    annualKwh: 1180000,
    intensityKwhSqm: 98.3,
    solarSharePct: 35.0,
    status: "HIGH_LOAD",
  },
  {
    name: "Central Library & Knowledge Hub",
    sqm: 8500,
    annualKwh: 480000,
    intensityKwhSqm: 56.5,
    solarSharePct: 52.0,
    status: "EFFICIENT",
  },
  {
    name: "Hostel Cluster A & B",
    sqm: 24000,
    annualKwh: 1850000,
    intensityKwhSqm: 77.1,
    solarSharePct: 28.0,
    status: "MODERATE",
  },
  {
    name: "Dining Complex & Mess",
    sqm: 6000,
    annualKwh: 540000,
    intensityKwhSqm: 90.0,
    solarSharePct: 20.0,
    status: "MODERATE",
  },
];

export default function SustainabilityAnalyticsPage() {
  const [overview, setOverview] = useState<SustainabilityDashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const ov = await sustainabilityService.getDashboardOverview();
        setOverview(ov);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="Comparative Building Energy Intensity & Decarbonization Trajectory"
        subtitle="Energy Use Intensity (EUI in kWh/m²), benchmark compliance against BEE / IGBC standards, and net-zero glidepath."
      />

      {/* Trajectory Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-emerald-400" />
              Net-Zero Carbon Glidepath (2020 — 2040)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Target trajectory: 5% annual emissions reduction through on-site renewables and circular heat recovery.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-semibold">
            <span className="flex items-center gap-1.5 text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-600" /> Baseline: 1,420 MT (2020)
            </span>
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Current: 475 MT (2024)
            </span>
            <span className="flex items-center gap-1.5 text-cyan-400">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> Goal: 0 MT (2040)
            </span>
          </div>
        </div>

        {/* Visual Progress Trajectory Bar */}
        <div className="mt-5 space-y-2">
          <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden flex">
            <div className="bg-emerald-500 h-3" style={{ width: "66.5%" }} />
            <div className="bg-slate-700 h-3" style={{ width: "33.5%" }} />
          </div>
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>2020 Baseline</span>
            <span className="text-emerald-400 font-bold">66.5% of Net-Zero Journey Completed</span>
            <span>2040 Net-Zero Goal</span>
          </div>
        </div>
      </div>

      {/* Building-by-Building EUI Heatmap Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Building className="w-4 h-4 text-emerald-400" />
            Campus Building Energy Intensity (EUI) Heatmap
          </h3>
          <span className="text-xs text-slate-400">
            Average Campus EUI: {overview?.energy_intensity_kwh_sqm || "78.5"} kWh / m² / year
          </span>
        </div>

        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-semibold">
              <th className="py-3 px-4">Building Name</th>
              <th className="py-3 px-4">Built-Up Area</th>
              <th className="py-3 px-4">Annual Energy</th>
              <th className="py-3 px-4">EUI (kWh / m²)</th>
              <th className="py-3 px-4">Solar Share</th>
              <th className="py-3 px-4">Energy Performance Rating</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {MOCK_BUILDING_STATS.map((b) => (
              <tr key={b.name} className="hover:bg-slate-800/30 transition">
                <td className="py-3.5 px-4 font-bold text-slate-100">{b.name}</td>
                <td className="py-3.5 px-4 text-slate-300">{b.sqm.toLocaleString()} m²</td>
                <td className="py-3.5 px-4 text-slate-300 font-mono">
                  {b.annualKwh.toLocaleString()} kWh
                </td>
                <td className="py-3.5 px-4 font-bold text-slate-100 font-mono">
                  {b.intensityKwhSqm} <span className="text-[11px] font-normal text-slate-400">kWh/m²</span>
                </td>
                <td className="py-3.5 px-4 text-emerald-400 font-semibold">{b.solarSharePct}%</td>
                <td className="py-3.5 px-4">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      b.status === "EFFICIENT"
                        ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                        : b.status === "MODERATE"
                        ? "bg-amber-950 text-amber-400 border border-amber-800"
                        : "bg-red-950 text-red-400 border border-red-800"
                    }`}
                  >
                    {b.status === "EFFICIENT"
                      ? "IGBC PLATINUM"
                      : b.status === "MODERATE"
                      ? "BEE 3-STAR"
                      : "RETROFIT RECOMMENDED"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


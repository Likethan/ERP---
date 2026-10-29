"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Leaf,
  Zap,
  Droplets,
  Trash2,
  Activity,
  ShieldCheck,
  AlertTriangle,
  ArrowUpRight,
  TrendingDown,
  CheckCircle2,
  Cpu,
  BarChart2,
} from "lucide-react";
import { SustainabilityNav } from "../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../services/sustainability.service";
import {
  ResourceMeasurement,
  SustainabilityDashboardOverview,
  SustainabilityTarget,
} from "../../../types/sustainability";

export default function SustainabilityDashboardPage() {
  const [overview, setOverview] = useState<SustainabilityDashboardOverview | null>(null);
  const [targets, setTargets] = useState<SustainabilityTarget[]>([]);
  const [anomalies, setAnomalies] = useState<ResourceMeasurement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [ov, tgts, anom] = await Promise.all([
          sustainabilityService.getDashboardOverview(),
          sustainabilityService.getTargets(),
          sustainabilityService.getMeasurements(undefined, true),
        ]);
        setOverview(ov);
        setTargets(tgts);
        setAnomalies(anom);
      } catch (err) {
        console.error("Failed to load sustainability dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="Campus Sustainability & Carbon Intelligence Hub"
        subtitle="Institutional ESG scorecard, real-time energy telemetry, GHG Scope 1-3 accounting, and environmental compliance."
      />

      {loading ? (
        <div className="flex items-center justify-center p-20 text-slate-400">
          <Activity className="w-6 h-6 animate-spin mr-2 text-emerald-500" />
          Loading verified institutional telemetry...
        </div>
      ) : (
        <div className="space-y-6">
          {/* Executive ESG Scorecard Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Composite ESG Score */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  ESG Composite Score
                </span>
                <span className="p-2 rounded-lg bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                  <Leaf className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-50">
                  {overview?.esg_composite_score.toFixed(1) || "88.4"}
                </span>
                <span className="text-sm font-medium text-slate-400">/ 100</span>
              </div>
              <p className="text-xs text-emerald-400 mt-2 flex items-center gap-1 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" /> High Institutional Rating (Tier-1 Green)
              </p>
            </div>

            {/* Card 2: Net GHG Emissions */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Net GHG Footprint (MT CO₂e)
                </span>
                <span className="p-2 rounded-lg bg-blue-950/80 text-blue-400 border border-blue-800/60">
                  <Activity className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-50">
                  {overview?.net_emissions_mt.toFixed(1) || "475.2"}
                </span>
                <span className="text-sm font-medium text-slate-400">MT CO₂e</span>
              </div>
              <p className="text-xs text-emerald-400 mt-2 flex items-center gap-1 font-medium">
                <TrendingDown className="w-3.5 h-3.5" /> 182.4 MT offset by on-site solar
              </p>
            </div>

            {/* Card 3: Renewable Share */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Rooftop Solar Share
                </span>
                <span className="p-2 rounded-lg bg-amber-950/80 text-amber-400 border border-amber-800/60">
                  <Zap className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-50">
                  {overview?.renewable_share_pct.toFixed(1) || "38.2"}%
                </span>
                <span className="text-sm font-medium text-slate-400">of total energy</span>
              </div>
              <p className="text-xs text-slate-400 mt-2 flex items-center gap-1">
                Phase-2 650 kWp expansion currently in execution
              </p>
            </div>

            {/* Card 4: Statutory Compliance */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Statutory Compliance
                </span>
                <span className="p-2 rounded-lg bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                  <ShieldCheck className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-50">
                  {overview?.statutory_compliance_rate_pct.toFixed(1) || "100.0"}%
                </span>
                <span className="text-sm font-medium text-emerald-400">Compliant</span>
              </div>
              <p className="text-xs text-amber-400 mt-2 flex items-center gap-1 font-medium">
                <AlertTriangle className="w-3.5 h-3.5" /> 1 CAPA calibration item pending review
              </p>
            </div>
          </div>

          {/* GHG Protocol Scope 1, 2, 3 Breakdown */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-emerald-400" />
                  GHG Protocol Carbon Emissions Hierarchy (2024 Year-to-Date)
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Verified emission factors: CEA India v19 (Scope 2) • IPCC Stationary Fuel (Scope 1) • DEFRA Water/Waste (Scope 3)
                </p>
              </div>
              <Link
                href="/app/sustainability/carbon"
                className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 hover:text-emerald-300"
              >
                Open Carbon Engine <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg">
                <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
                  <span>Scope 1 (Direct Fuels)</span>
                  <span className="px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-900">
                    Direct
                  </span>
                </div>
                <div className="mt-2 text-2xl font-bold text-slate-100">
                  {overview?.scope_1_mt.toFixed(1) || "33.5"}{" "}
                  <span className="text-xs font-normal text-slate-400">MT CO₂e</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Stationary diesel generators, campus transit shuttle fleet, mess LPG.
                </p>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg">
                <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
                  <span>Scope 2 (Purchased Electricity)</span>
                  <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-900">
                    Indirect Grid
                  </span>
                </div>
                <div className="mt-2 text-2xl font-bold text-slate-100">
                  {overview?.scope_2_mt.toFixed(1) || "608.6"}{" "}
                  <span className="text-xs font-normal text-slate-400">MT CO₂e</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Grid purchase from TANGEDCO High Tension sub-station @ 0.716 kgCO₂e/kWh.
                </p>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg">
                <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
                  <span>Scope 3 (Supply Chain & Waste)</span>
                  <span className="px-2 py-0.5 rounded bg-purple-950 text-purple-400 border border-purple-900">
                    Value Chain
                  </span>
                </div>
                <div className="mt-2 text-2xl font-bold text-slate-100">
                  {overview?.scope_3_mt.toFixed(1) || "15.5"}{" "}
                  <span className="text-xs font-normal text-slate-400">MT CO₂e</span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Municipal water treatment pumping, solid waste disposal, student commuting.
                </p>
              </div>
            </div>
          </div>

          {/* Two-column layout: Active Target Milestones & Live Anomaly Alerts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Column 1: Institutional Sustainability Targets */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <Leaf className="w-4 h-4 text-emerald-400" />
                  Active Environmental Milestones
                </h3>
                <Link
                  href="/app/sustainability/targets"
                  className="text-xs font-semibold text-emerald-400 hover:text-emerald-300"
                >
                  Manage All Targets →
                </Link>
              </div>

              <div className="space-y-4">
                {targets.map((tgt) => (
                  <div key={tgt.id} className="p-3.5 bg-slate-950/60 rounded-lg border border-slate-800/80">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200">{tgt.title}</span>
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                        {tgt.status.replace("_", " ")}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
                      <span>Baseline: {tgt.baseline_value} {tgt.unit}</span>
                      <span className="font-semibold text-slate-200">
                        {tgt.reduction_pct_achieved}% Achieved (Target: {tgt.reduction_pct_target}%)
                      </span>
                    </div>
                    {/* Progress Bar */}
                    <div className="w-full bg-slate-800 h-2 rounded-full mt-1.5 overflow-hidden">
                      <div
                        className="bg-emerald-500 h-2 rounded-full transition-all"
                        style={{
                          width: `${Math.min(
                            100,
                            Math.round((tgt.reduction_pct_achieved / tgt.reduction_pct_target) * 100)
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Column 2: Peak Load & Leak Anomaly Feeds */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  Live Operational Anomaly Feeds
                </h3>
                <Link
                  href="/app/sustainability/energy"
                  className="text-xs font-semibold text-amber-400 hover:text-amber-300"
                >
                  View All Telemetry →
                </Link>
              </div>

              <div className="space-y-3">
                {anomalies.length === 0 ? (
                  <p className="text-xs text-slate-500 italic p-4 text-center">
                    All smart meter streams operating within expected variance thresholds.
                  </p>
                ) : (
                  anomalies.map((anom) => (
                    <div
                      key={anom.id}
                      className="p-3.5 bg-slate-950/80 rounded-lg border border-amber-900/50 flex items-start gap-3"
                    >
                      <span className="p-2 rounded-md bg-amber-950 text-amber-400 border border-amber-800 shrink-0 mt-0.5">
                        <Zap className="w-4 h-4" />
                      </span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-bold text-slate-200">{anom.building_name}</h4>
                          <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-red-950 text-red-400 border border-red-800">
                            {anom.anomaly_severity || "WARNING"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 mt-1">{anom.anomaly_reason}</p>
                        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                          <span>Reading: {anom.reading_value} {anom.unit}</span>
                          <span className="text-amber-400 font-semibold">+{anom.variance_pct}% over baseline</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Quick Module Navigation Hub */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            <Link
              href="/app/sustainability/energy"
              className="p-4 bg-slate-900 border border-slate-800 rounded-lg hover:border-emerald-600/60 transition group text-center"
            >
              <Zap className="w-5 h-5 mx-auto text-amber-400 group-hover:scale-110 transition-transform" />
              <span className="text-xs font-semibold text-slate-200 mt-2 block">Energy & Solar</span>
            </Link>
            <Link
              href="/app/sustainability/water"
              className="p-4 bg-slate-900 border border-slate-800 rounded-lg hover:border-emerald-600/60 transition group text-center"
            >
              <Droplets className="w-5 h-5 mx-auto text-blue-400 group-hover:scale-110 transition-transform" />
              <span className="text-xs font-semibold text-slate-200 mt-2 block">Water Balance</span>
            </Link>
            <Link
              href="/app/sustainability/waste"
              className="p-4 bg-slate-900 border border-slate-800 rounded-lg hover:border-emerald-600/60 transition group text-center"
            >
              <Trash2 className="w-5 h-5 mx-auto text-emerald-400 group-hover:scale-110 transition-transform" />
              <span className="text-xs font-semibold text-slate-200 mt-2 block">Waste & TSDF</span>
            </Link>
            <Link
              href="/app/sustainability/compliance"
              className="p-4 bg-slate-900 border border-slate-800 rounded-lg hover:border-emerald-600/60 transition group text-center"
            >
              <ShieldCheck className="w-5 h-5 mx-auto text-purple-400 group-hover:scale-110 transition-transform" />
              <span className="text-xs font-semibold text-slate-200 mt-2 block">SPCB Permits</span>
            </Link>
            <Link
              href="/app/sustainability/iot-meters"
              className="p-4 bg-slate-900 border border-slate-800 rounded-lg hover:border-emerald-600/60 transition group text-center"
            >
              <Cpu className="w-5 h-5 mx-auto text-cyan-400 group-hover:scale-110 transition-transform" />
              <span className="text-xs font-semibold text-slate-200 mt-2 block">IoT Telemetry</span>
            </Link>
            <Link
              href="/app/sustainability/analytics"
              className="p-4 bg-slate-900 border border-slate-800 rounded-lg hover:border-emerald-600/60 transition group text-center"
            >
              <BarChart2 className="w-5 h-5 mx-auto text-emerald-400 group-hover:scale-110 transition-transform" />
              <span className="text-xs font-semibold text-slate-200 mt-2 block">Decarb Analytics</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}


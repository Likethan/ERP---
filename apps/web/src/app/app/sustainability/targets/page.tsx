"use client";

import { useEffect, useState } from "react";
import {
  Target,
  Plus,
  CheckCircle2,
  Clock,
  Calendar,
  Building2,
  TrendingDown,
  Activity,
} from "lucide-react";
import { SustainabilityNav } from "../../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../../services/sustainability.service";
import { SustainabilityTarget, TargetCategory } from "../../../../types/sustainability";

export default function SustainabilityTargetsPage() {
  const [targets, setTargets] = useState<SustainabilityTarget[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form State
  const [category, setCategory] = useState<TargetCategory>("ENERGY_REDUCTION");
  const [targetCode, setTargetCode] = useState("");
  const [title, setTitle] = useState("");
  const [baselineVal, setBaselineVal] = useState(100000);
  const [targetVal, setTargetVal] = useState(70000);
  const [unit, setUnit] = useState("kWh");
  const [targetYear, setTargetYear] = useState(2030);
  const [reductionPct, setReductionPct] = useState(30.0);
  const [team, setTeam] = useState("Estate & Energy Cell");

  useEffect(() => {
    async function load() {
      try {
        const data = await sustainabilityService.getTargets();
        setTargets(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await sustainabilityService.createTarget({
        category,
        target_code: targetCode || `TGT-${Date.now().toString().slice(-4)}`,
        title,
        baseline_year: 2022,
        baseline_value: Number(baselineVal),
        target_year: Number(targetYear),
        target_value: Number(targetVal),
        unit,
        reduction_pct_target: Number(reductionPct),
        responsible_team: team,
      });
      setTargets((prev) => [created, ...prev]);
      setShowCreateModal(false);
      setTitle("");
      setTargetCode("");
    } catch (err) {
      console.error("Failed to create target", err);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="Institutional Sustainability Targets & Carbon Baselines"
        subtitle="Establish quantitative reduction roadmaps, baseline references, and responsible departmental milestones."
      />

      {/* Action Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Target className="w-5 h-5 text-emerald-400" />
            Active Decarbonization & Resource Targets
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Measured against verified institutional baseline year 2022.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" /> Add Reduction Target
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-20 text-slate-400">
          <Activity className="w-6 h-6 animate-spin mr-2 text-emerald-500" />
          Loading sustainability targets...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {targets.map((tgt) => (
            <div
              key={tgt.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-bold text-emerald-400 tracking-wider uppercase">
                    {tgt.category.replace("_", " ")}
                  </span>
                  <h3 className="text-base font-bold text-slate-100 mt-0.5">{tgt.title}</h3>
                  <p className="text-xs text-slate-400 mt-1">{tgt.description || "Official institutional target."}</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-semibold rounded-md bg-emerald-950 text-emerald-300 border border-emerald-800">
                  {tgt.status.replace("_", " ")}
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-slate-800/80">
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">Baseline ({tgt.baseline_year})</span>
                  <div className="text-sm font-bold text-slate-200 mt-1">
                    {tgt.baseline_value} {tgt.unit}
                  </div>
                </div>
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">Current Progress</span>
                  <div className="text-sm font-bold text-emerald-400 mt-1">
                    {tgt.current_value} {tgt.unit}
                  </div>
                </div>
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">Target ({tgt.target_year})</span>
                  <div className="text-sm font-bold text-blue-400 mt-1">
                    {tgt.target_value} {tgt.unit}
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-4">
                <div className="flex items-center justify-between text-xs font-medium text-slate-300 mb-1">
                  <span>Reduction Progress</span>
                  <span className="text-emerald-400 font-bold">
                    {tgt.reduction_pct_achieved}% achieved of {tgt.reduction_pct_target}% goal
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-2.5 rounded-full transition-all"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.round((tgt.reduction_pct_achieved / tgt.reduction_pct_target) * 100)
                      )}%`,
                    }}
                  />
                </div>
              </div>

              {/* Footer Meta */}
              <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-slate-500" />
                  {tgt.responsible_team}
                </span>
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" />
                  Due: {tgt.deadline || `${tgt.target_year}-12-31`}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Target Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Target className="w-5 h-5 text-emerald-400" />
              Configure Sustainability Milestone Target
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Set quantitative reduction goals linked to institutional net-zero commitments.
            </p>

            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Target Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value as TargetCategory)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                >
                  <option value="ENERGY_REDUCTION">Energy Reduction</option>
                  <option value="RENEWABLE_SHARE">Renewable Energy Share</option>
                  <option value="WATER_CONSERVATION">Water Conservation</option>
                  <option value="WASTE_DIVERSION">Waste Diversion</option>
                  <option value="SCOPE_1_REDUCTION">Scope 1 Fuel Reduction</option>
                  <option value="SCOPE_2_REDUCTION">Scope 2 Grid Reduction</option>
                  <option value="NET_ZERO_GHG">Net-Zero GHG</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Target Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Cut Grid Energy Consumption by 30%"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Baseline Value (2022)</label>
                  <input
                    type="number"
                    value={baselineVal}
                    onChange={(e) => setBaselineVal(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Target Value</label>
                  <input
                    type="number"
                    value={targetVal}
                    onChange={(e) => setTargetVal(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Unit</label>
                  <input
                    type="text"
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Target Year</label>
                  <input
                    type="number"
                    value={targetYear}
                    onChange={(e) => setTargetYear(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Reduction %</label>
                  <input
                    type="number"
                    value={reductionPct}
                    onChange={(e) => setReductionPct(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Responsible Team</label>
                <input
                  type="text"
                  value={team}
                  onChange={(e) => setTeam(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white"
                >
                  Save Target
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


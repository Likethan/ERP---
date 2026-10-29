"use client";

import { useEffect, useState } from "react";
import {
  Sprout,
  Plus,
  Calendar,
  Building2,
  TrendingDown,
  Activity,
  CheckCircle2,
  Clock,
  IndianRupee,
  Leaf,
} from "lucide-react";
import { SustainabilityNav } from "../../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../../services/sustainability.service";
import { InitiativeCategory, InitiativeStatus, SustainabilityInitiative } from "../../../../types/sustainability";

export default function SustainabilityInitiativesPage() {
  const [initiatives, setInitiatives] = useState<SustainabilityInitiative[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form State
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<InitiativeCategory>("SOLAR_ROOFTOP");
  const [status, setStatus] = useState<InitiativeStatus>("PROPOSED");
  const [budgetAllocated, setBudgetAllocated] = useState(5000000);
  const [co2Savings, setCo2Savings] = useState(120);
  const [department, setDepartment] = useState("Estate & Facilities");

  useEffect(() => {
    async function load() {
      try {
        const data = await sustainabilityService.getInitiatives();
        setInitiatives(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const code = `INIT-${Date.now().toString().slice(-4)}`;
      const created = await sustainabilityService.createInitiative({
        campus_id: "c0000000-0000-0000-0000-000000000001",
        initiative_code: code,
        title,
        description,
        category,
        status,
        budget_allocated: Number(budgetAllocated),
        budget_spent: 0,
        annual_co2_savings_mt: Number(co2Savings),
        annual_energy_savings_kwh: Number(co2Savings * 1400),
        annual_water_savings_kl: 0,
        start_date: new Date().toISOString().split("T")[0],
        lead_department: department,
      });
      setInitiatives((prev) => [created, ...prev]);
      setShowCreateModal(false);
      setTitle("");
      setDescription("");
    } catch (err) {
      console.error("Failed to create initiative", err);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="Campus Green Initiatives & Decarbonization Portfolio"
        subtitle="Manage capital environmental programs, renewable energy expansions, and verified avoided carbon balances."
      />

      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Sprout className="w-5 h-5 text-emerald-400" />
            Active Decarbonization Capital Projects
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Total portfolio annual emissions avoided: ~738.5 MT CO₂e.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" /> Propose New Initiative
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-20 text-slate-400">
          <Activity className="w-6 h-6 animate-spin mr-2 text-emerald-500" />
          Loading project portfolio...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {initiatives.map((init) => (
            <div
              key={init.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between">
                  <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
                    {init.category.replace("_", " ")}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                      init.status === "OPERATIONAL" || init.status === "COMPLETED"
                        ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                        : "bg-blue-950 text-blue-300 border border-blue-800"
                    }`}
                  >
                    {init.status.replace("_", " ")}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-100 mt-2">{init.title}</h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-3">{init.description}</p>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Annual CO₂ Avoided:</span>
                  <span className="font-bold text-emerald-400">
                    {init.annual_co2_savings_mt} MT / year
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Capital Investment:</span>
                  <span className="font-semibold text-slate-200">
                    ₹{(init.budget_allocated / 100000).toFixed(1)} Lakhs
                  </span>
                </div>

                {/* Budget Utilization Bar */}
                <div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                    <span>Budget Spent</span>
                    <span>
                      {init.budget_allocated > 0
                        ? Math.round((init.budget_spent / init.budget_allocated) * 100)
                        : 0}
                      %
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-1.5 rounded-full"
                      style={{
                        width: `${
                          init.budget_allocated > 0
                            ? Math.min(
                                100,
                                Math.round((init.budget_spent / init.budget_allocated) * 100)
                              )
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                  <span>{init.lead_department}</span>
                  <span>Target: {init.completion_date || "Q4 2024"}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Propose Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Sprout className="w-5 h-5 text-emerald-400" />
              Propose New Green Initiative / Project
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Submit proposal for institutional capital allocation and carbon offset verification.
            </p>

            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Project Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 500 kWp Phase-2 Rooftop Solar PV"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Scope & Objectives</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Detailed description of technology and environmental outcome..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as InitiativeCategory)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  >
                    <option value="SOLAR_ROOFTOP">Solar PV Generation</option>
                    <option value="LED_RETROFIT">LED Energy Efficiency</option>
                    <option value="RAINWATER_HARVESTING">Rainwater Harvesting</option>
                    <option value="BIOGAS_PLANT">Biogas Plant</option>
                    <option value="EV_SHUTTLE">Electric Mobility Shuttle</option>
                    <option value="TREE_PLANTATION">Campus Afforestation</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Lifecycle Status</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value as InitiativeStatus)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  >
                    <option value="PROPOSED">Proposed</option>
                    <option value="APPROVED">Approved by Board</option>
                    <option value="IN_EXECUTION">In Execution</option>
                    <option value="OPERATIONAL">Fully Operational</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Budget Allocated (₹)</label>
                  <input
                    type="number"
                    value={budgetAllocated}
                    onChange={(e) => setBudgetAllocated(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Est. Annual CO₂ Saved (MT)</label>
                  <input
                    type="number"
                    value={co2Savings}
                    onChange={(e) => setCo2Savings(Number(e.target.value))}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Lead Department</label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
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
                  Submit Proposal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


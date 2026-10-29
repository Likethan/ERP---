"use client";

import { useEffect, useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  FileCheck2,
  Calendar,
  Building2,
  Plus,
  Activity,
  CheckCircle2,
  Clock,
  ExternalLink,
} from "lucide-react";
import { SustainabilityNav } from "../../../../components/sustainability/sustainability-nav";
import { sustainabilityService } from "../../../../services/sustainability.service";
import {
  ComplianceCategory,
  ComplianceStatus,
  EnvironmentalComplianceRequirement,
  EnvironmentalCorrectiveAction,
} from "../../../../types/sustainability";

export default function SustainabilityCompliancePage() {
  const [requirements, setRequirements] = useState<EnvironmentalComplianceRequirement[]>([]);
  const [actions, setActions] = useState<EnvironmentalCorrectiveAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPermitModal, setShowPermitModal] = useState(false);

  // Form State
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("Tamil Nadu Pollution Control Board (TNPCB)");
  const [cat, setCat] = useState<ComplianceCategory>("WATER_CONSENT");
  const [renewalDate, setRenewalDate] = useState("2025-06-30");
  const [permitNo, setPermitNo] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [reqs, acts] = await Promise.all([
          sustainabilityService.getComplianceRequirements(),
          sustainabilityService.getCorrectiveActions(),
        ]);
        setRequirements(reqs);
        setActions(acts);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const cCode = code || `COMP-${Date.now().toString().slice(-4)}`;
      const created = await sustainabilityService.createComplianceRequirement({
        campus_id: "c0000000-0000-0000-0000-000000000001",
        compliance_code: cCode,
        regulation_title: title,
        regulatory_body: body,
        compliance_category: cat,
        frequency: "ANNUAL",
        next_renewal_date: renewalDate,
        status: "COMPLIANT",
        permit_number: permitNo || undefined,
      });
      setRequirements((prev) => [created, ...prev]);
      setShowPermitModal(false);
      setTitle("");
      setPermitNo("");
    } catch (err) {
      console.error("Failed to add compliance requirement", err);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <SustainabilityNav
        title="Statutory Environmental Compliance & Corrective Actions"
        subtitle="SPCB Consent to Operate (CTO - Water & Air), hazardous TSDF manifests, CGWA groundwater extraction NOCs, and automated CAPA audits."
      />

      {/* Action Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Statutory Legal Permits & Statutory Clearances
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit evidence securely logged for NAAC Criteria 7 and NIRF Green Institutional Rankings.
          </p>
        </div>
        <button
          onClick={() => setShowPermitModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition"
        >
          <Plus className="w-4 h-4" /> Register Permit / Consent
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-20 text-slate-400">
          <Activity className="w-6 h-6 animate-spin mr-2 text-emerald-500" />
          Loading statutory permits...
        </div>
      ) : (
        <div className="space-y-6">
          {/* Permits Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {requirements.map((req) => (
              <div
                key={req.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <span className="text-[11px] font-bold text-slate-400 font-mono">
                      {req.compliance_code}
                    </span>
                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                        req.status === "COMPLIANT"
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : req.status === "RENEWAL_DUE"
                          ? "bg-amber-950 text-amber-400 border border-amber-800"
                          : "bg-red-950 text-red-400 border border-red-800"
                      }`}
                    >
                      {req.status.replace("_", " ")}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-100 mt-2 line-clamp-2">
                    {req.regulation_title}
                  </h3>
                  <p className="text-xs text-emerald-400 mt-1 font-medium">{req.regulatory_body}</p>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-2 text-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Permit / License #:</span>
                    <span className="font-mono text-slate-200">{req.permit_number || "—"}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Next Renewal Date:</span>
                    <span
                      className={`font-semibold ${
                        req.status === "RENEWAL_DUE" ? "text-amber-400 font-bold" : "text-slate-200"
                      }`}
                    >
                      {req.next_renewal_date}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/60">
                    <span>Audit Cycle: {req.frequency}</span>
                    <span className="text-emerald-400 flex items-center gap-1 cursor-pointer hover:underline">
                      View Certificate <ExternalLink className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Corrective Action Plans (CAPA) */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Environmental Corrective & Preventive Action Items (CAPA)
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Action items initiated during internal audits to ensure continuous regulatory compliance.
            </p>

            <div className="space-y-3">
              {actions.map((act) => (
                <div
                  key={act.id}
                  className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 flex items-start justify-between gap-4"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-200">{act.action_code}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-400 border border-amber-800">
                        {act.priority} PRIORITY
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-950 text-blue-400 border border-blue-800">
                        {act.status}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-slate-200 mt-2">{act.issue_description}</h4>
                    <p className="text-xs text-slate-400 mt-1">{act.action_plan}</p>
                  </div>
                  <div className="text-right shrink-0 text-xs">
                    <div className="text-slate-400">Due Date:</div>
                    <div className="font-semibold text-slate-200 mt-0.5">{act.due_date}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Register Permit Modal */}
      {showPermitModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Register Environmental Permit / Clearance
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Add statutory license reference, responsible regulatory board, and audit schedule.
            </p>

            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Regulation Title / Permit</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Consent to Operate (CTO) - Air & Water"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Regulatory Body</label>
                  <input
                    type="text"
                    required
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Permit Category</label>
                  <select
                    value={cat}
                    onChange={(e) => setCat(e.target.value as ComplianceCategory)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  >
                    <option value="WATER_CONSENT">Water Consent (SPCB)</option>
                    <option value="AIR_EMISSIONS">Air Emissions (SPCB)</option>
                    <option value="GROUNDWATER_EXTRACTION_NOC">CGWA Groundwater NOC</option>
                    <option value="HAZARDOUS_WASTE_AUTHORIZATION">Hazardous TSDF Authorization</option>
                    <option value="E_WASTE_EPR">E-Waste EPR Authorization</option>
                    <option value="GREEN_BUILDING_IGBC">IGBC Green Building Platinum</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Permit Number</label>
                  <input
                    type="text"
                    placeholder="e.g. TNPCB/CTO/2024-991"
                    value={permitNo}
                    onChange={(e) => setPermitNo(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300">Next Renewal Date</label>
                  <input
                    type="date"
                    required
                    value={renewalDate}
                    onChange={(e) => setRenewalDate(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowPermitModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white"
                >
                  Register Clearance
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


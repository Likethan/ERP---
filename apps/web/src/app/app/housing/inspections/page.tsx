"use client";

import { useEffect, useState } from "react";
import {
  ShieldCheck,
  Plus,
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Calendar,
  X,
  Flame,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  AccommodationProperty,
  HousingInspectionCreateInput,
  HousingPropertyInspection,
  InspectionOutcome,
  InspectionType,
} from "@/types/housing";

export default function InspectionsCompliancePage() {
  const [inspections, setInspections] = useState<HousingPropertyInspection[]>([]);
  const [properties, setProperties] = useState<AccommodationProperty[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const [formData, setFormData] = useState<HousingInspectionCreateInput>({
    property_id: "",
    inspection_date: new Date().toISOString().split("T")[0],
    inspection_type: "SAFETY_FIRE",
    overall_outcome: "PASSED",
    safety_score: 92,
    critical_issues_found: false,
    corrective_actions_required: "None required. Certified for statutory compliance.",
    reinspection_due_date: "2027-04-10",
  });

  const loadData = async () => {
    try {
      const [allInspections, allProps] = await Promise.all([
        HousingService.listInspections(),
        HousingService.listProperties(false),
      ]);
      setInspections(allInspections);
      setProperties(allProps);
      if (allProps.length > 0) {
        setFormData((prev) => ({ ...prev, property_id: allProps[0].id }));
      }
    } catch (err) {
      console.error("Failed to load inspections", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await HousingService.recordInspection(formData);
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      alert("Failed to record inspection: " + (err as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const getOutcomeBadge = (outcome: InspectionOutcome, critical: boolean) => {
    if (critical || outcome === "FAILED_CRITICAL") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
          <XCircle className="w-3.5 h-3.5" />
          Critical Failure (Suspended)
        </span>
      );
    }
    switch (outcome) {
      case "PASSED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle className="w-3.5 h-3.5" />
            Statutory Passed
          </span>
        );
      case "CONDITIONAL_PASS":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" />
            Conditional Pass
          </span>
        );
      case "REQUIRES_REINSPECTION":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            Reinspection Required
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <HousingNav />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <ShieldCheck className="w-7 h-7 text-indigo-400" />
              Safety, Fire, Hygiene & Compliance Inspections
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Statutory fire audits, food mess hygiene inspections, and automated facility suspension gates on critical safety failures.
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Record Safety Inspection
          </button>
        </div>

        {/* System Notice Banner */}
        <div className="bg-amber-950/20 border border-amber-800/40 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
          <div className="text-xs text-amber-200/90 leading-relaxed">
            <strong>Institutional Safety Mandate:</strong> Any inspection flagged with{" "}
            <code className="text-rose-400 font-mono">FAILED_CRITICAL</code> or{" "}
            <code className="text-rose-400 font-mono">critical_issues_found = true</code>{" "}
            will immediately transition the accommodation property to <strong>SUSPENDED</strong> status,
            preventing issuance of new student housing offers until a verified remediation inspection passes.
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading statutory compliance records...</div>
        ) : inspections.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
            <p className="text-slate-400">No safety or compliance inspections logged.</p>
          </div>
        ) : (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3">Property / Facility</th>
                    <th className="px-5 py-3">Inspection Category</th>
                    <th className="px-5 py-3">Inspector Agency</th>
                    <th className="px-5 py-3">Score & Outcome</th>
                    <th className="px-5 py-3">Corrective Actions</th>
                    <th className="px-5 py-3">Audit Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {inspections.map((insp) => (
                    <tr key={insp.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-4">
                        <div className="font-semibold text-white">
                          {insp.property_name || "Facility"}
                        </div>
                        <div className="text-xs font-mono text-indigo-400">
                          {insp.inspection_code}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="font-medium text-xs text-indigo-300">
                          {insp.inspection_type.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs text-slate-200">{insp.inspector_name || "Statutory Inspector"}</div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-white font-mono">
                            {insp.safety_score ? `${insp.safety_score}/100` : "N/A"}
                          </span>
                          {getOutcomeBadge(insp.overall_outcome, insp.critical_issues_found)}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs text-slate-300 max-w-sm truncate">
                          {insp.corrective_actions_required || "Compliant with national building norms."}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs font-mono text-slate-300">
                          {new Date(insp.inspection_date).toLocaleDateString()}
                        </div>
                        {insp.reinspection_due_date && (
                          <div className="text-[11px] text-slate-500">
                            Next: {insp.reinspection_due_date}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: Record Safety Inspection */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Flame className="w-5 h-5 text-indigo-400" />
                  Log Statutory Safety Inspection
                </h3>
                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Select Facility *
                  </label>
                  <select
                    required
                    value={formData.property_id}
                    onChange={(e) => setFormData({ ...formData, property_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  >
                    {properties.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.code})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Inspection Category *
                    </label>
                    <select
                      value={formData.inspection_type}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          inspection_type: e.target.value as InspectionType,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="SAFETY_FIRE">Fire & Life Safety</option>
                      <option value="HEALTH_HYGIENE">Mess / Food Hygiene</option>
                      <option value="ELECTRICAL">Electrical & Grid Safety</option>
                      <option value="STRUCTURAL">Structural & Civil</option>
                      <option value="ANNUAL_COMPLIANCE">Annual Compliance</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Compliance Score (0-100) *
                    </label>
                    <input
                      required
                      type="number"
                      min="0"
                      max="100"
                      value={formData.safety_score}
                      onChange={(e) =>
                        setFormData({ ...formData, safety_score: parseFloat(e.target.value) || 0 })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Inspection Date *
                    </label>
                    <input
                      required
                      type="date"
                      value={formData.inspection_date}
                      onChange={(e) =>
                        setFormData({ ...formData, inspection_date: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Next Reinspection Date
                    </label>
                    <input
                      type="date"
                      value={formData.reinspection_due_date || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, reinspection_due_date: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Inspection Outcome *
                  </label>
                  <select
                    value={formData.overall_outcome}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        overall_outcome: e.target.value as InspectionOutcome,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  >
                    <option value="PASSED">Statutory Passed</option>
                    <option value="CONDITIONAL_PASS">Passed with Conditions</option>
                    <option value="REQUIRES_REINSPECTION">Requires Reinspection</option>
                    <option value="FAILED_CRITICAL">Failed Critical (Auto-Suspension)</option>
                  </select>
                </div>

                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="crit_issues"
                    checked={formData.critical_issues_found}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        critical_issues_found: e.target.checked,
                      })
                    }
                    className="rounded bg-slate-900 border-slate-700 text-rose-600 focus:ring-rose-500"
                  />
                  <label htmlFor="crit_issues" className="text-xs font-medium text-rose-300 cursor-pointer">
                    Flag as Critical Safety Hazard (Automatically triggers immediate suspension of property availability)
                  </label>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Corrective Actions Required
                  </label>
                  <textarea
                    rows={2}
                    value={formData.corrective_actions_required || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, corrective_actions_required: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 text-xs"
                    placeholder="e.g. Recharge all expired ABC dry chemical extinguishers in Wing B within 48h."
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    File Inspection Record
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

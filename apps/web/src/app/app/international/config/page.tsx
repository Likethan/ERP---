"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle2,
  Lock,
  Save,
  Scale,
  Settings,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { InternationalPolicyConfig } from "@/types/international";

export default function InternationalPolicyConfigPage() {
  const [config, setConfig] = useState<InternationalPolicyConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const c = await internationalService.getPolicyConfig();
        setConfig(c);
      } catch (err) {
        console.error("Failed to load policy configuration", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!config) return;
    setSaving(true);
    try {
      const updated = await internationalService.updatePolicyConfig(config);
      setConfig(updated);
      setSuccessMessage(true);
      setTimeout(() => setSuccessMessage(false), 3000);
    } catch (err) {
      console.error(err);
      alert("Failed to update policy settings");
    } finally {
      setSaving(false);
    }
  }

  if (loading || !config) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <InternationalNav />
        <div className="p-12 text-center text-xs text-slate-500">Loading policy parameters...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Settings className="h-5 w-5 text-cyan-400" />
            Global Mobility & Treaty Governance Policies
          </h2>
          <p className="text-xs text-slate-400">
            Configure institutional compliance thresholds, approval hierarchies, and automated MoU renewal notice horizons
          </p>
        </div>

        {successMessage && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2.5 text-xs text-emerald-300">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>Policy configurations updated and published to active tenant profile successfully.</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6">
          {/* Agreement Notice Window */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-cyan-400" />
              Treaty Expiration & Renewal Parameters
            </h3>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1">
                MoU Expiration Warning Advance Notice (Days)
              </label>
              <input
                type="number"
                min={30}
                max={365}
                value={config.agreement_warning_days || config.agreementWarningDays || 90}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    agreement_warning_days: Number(e.target.value),
                    agreementWarningDays: Number(e.target.value),
                  })
                }
                className="w-full sm:w-64 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Institutional agreements with expiration dates within this window will trigger automated notification sweeps and flagged dashboard badges.
              </p>
            </div>
          </div>

          {/* Multi-Stage Approval Rules */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <UserCheck className="h-4 w-4 text-emerald-400" />
              Academic Review Hierarchies
            </h3>

            <div className="space-y-3">
              <label className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/60 border border-slate-850 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.require_department_approval_first ?? config.requireDepartmentApprovalFirst ?? true}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      require_department_approval_first: e.target.checked,
                      requireDepartmentApprovalFirst: e.target.checked,
                    })
                  }
                  className="rounded text-cyan-500 mt-0.5"
                />
                <div>
                  <span className="text-xs font-semibold text-white block">
                    Require Department Faculty Coordinator Endorsement Before International Office
                  </span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Ensures academic curriculum viability and prerequisite readiness before legal nomination to partner institutions.
                  </p>
                </div>
              </label>

              <label className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/60 border border-slate-850 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.require_vp_approval_for_faculty ?? config.requireVpApprovalForFaculty ?? true}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      require_vp_approval_for_faculty: e.target.checked,
                      requireVpApprovalForFaculty: e.target.checked,
                    })
                  }
                  className="rounded text-cyan-500 mt-0.5"
                />
                <div>
                  <span className="text-xs font-semibold text-white block">
                    Require Vice Principal Approval for All Faculty Mobility Proposals
                  </span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Faculty teaching exchanges and research fellowships must receive formal VP endorsement following HOD review.
                  </p>
                </div>
              </label>
            </div>
          </div>

          {/* Academic Governance & Inbound Orientation */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Scale className="h-4 w-4 text-purple-400" />
              Credit Recognition & Inbound Governance
            </h3>

            <div className="space-y-3">
              <label className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/60 border border-slate-850 cursor-pointer">
                <input
                  type="checkbox"
                  checked={
                    config.credit_transfer_requires_academic_council ??
                    config.creditTransferRequiresAcademicCouncil ??
                    true
                  }
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      credit_transfer_requires_academic_council: e.target.checked,
                      creditTransferRequiresAcademicCouncil: e.target.checked,
                    })
                  }
                  className="rounded text-cyan-500 mt-0.5"
                />
                <div>
                  <span className="text-xs font-semibold text-white block">
                    Credit Transfers Strictly Require Academic Council Resolution Reference
                  </span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Mandates that no academic credits can be automatically recognized without authorized committee review and council resolution tracking.
                  </p>
                </div>
              </label>

              <label className="flex items-start gap-3 p-3 rounded-lg bg-slate-950/60 border border-slate-850 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.inbound_orientation_mandatory ?? config.inboundOrientationMandatory ?? true}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      inbound_orientation_mandatory: e.target.checked,
                      inboundOrientationMandatory: e.target.checked,
                    })
                  }
                  className="rounded text-cyan-500 mt-0.5"
                />
                <div>
                  <span className="text-xs font-semibold text-white block">
                    Mandate Campus Orientation Check-In Before Inbound Course Enrollment
                  </span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Foreign exchange students must complete safety induction and in-person document verification to unlock course registration.
                  </p>
                </div>
              </label>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-lg shadow-cyan-900/40 flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {saving ? "Saving Changes..." : "Save Policy Configuration"}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

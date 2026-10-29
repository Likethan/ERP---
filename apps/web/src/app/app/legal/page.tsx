"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  FileCheck,
  FileSpreadsheet,
  FileText,
  Gavel,
  RefreshCw,
  Scale,
  Shield,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { LegalNav } from "@/components/legal/legal-nav";
import {
  calculateObligationHealth,
  calculateRiskMatrix,
  getContractStatusBadge,
} from "@/services/legal-calculator";
import { LegalService } from "@/services/legal.service";
import {
  InstitutionalContract,
  InstitutionalLegalMatter,
  InstitutionalRisk,
  LegalOperationsDashboard,
} from "@/types/legal";

export default function LegalOperationsDashboardPage() {
  const [dashboard, setDashboard] = useState<LegalOperationsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [sweeping, setSweeping] = useState(false);
  const [sweepResult, setSweepResult] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    setLoading(true);
    try {
      const data = await LegalService.getDashboard();
      setDashboard(data);
    } catch (err) {
      console.error("Failed to load legal operations dashboard", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleTriggerSweep() {
    setSweeping(true);
    setSweepResult(null);
    try {
      const result = await LegalService.triggerRenewalSweep();
      setSweepResult(
        `Sweep executed: ${result.contracts_flagged_expiring} expiring contract(s), ${result.obligations_flagged_overdue} overdue obligation(s), ${result.notifications_dispatched} reminder(s) queued.`
      );
      await loadDashboard();
    } catch (err) {
      setSweepResult("Error running automated renewal sweep.");
    } finally {
      setSweeping(false);
    }
  }

  if (loading || !dashboard) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
        <LegalNav />
        <div className="flex-1 flex items-center justify-center p-12">
          <div className="flex items-center gap-3 text-slate-500">
            <RefreshCw className="h-5 w-5 animate-spin text-indigo-600" />
            <span className="text-sm font-medium">Loading institutional legal operations telemetry...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      <LegalNav />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Banner with Sweep Action */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-xl border border-indigo-100 dark:border-indigo-900/60 bg-gradient-to-r from-indigo-50/70 via-white to-purple-50/50 dark:from-indigo-950/40 dark:via-slate-900 dark:to-purple-950/20 shadow-sm">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Scale className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              Unified Institutional Legal & Contract Operations
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 max-w-3xl">
              Centralized record of truth for contracts awaiting review, expiring agreements, compliance evidence,
              attorney-client privileged matters, and residual institutional risk scores.
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={handleTriggerSweep}
              disabled={sweeping}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm flex items-center gap-2 transition disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${sweeping ? "animate-spin" : ""}`} />
              <span>{sweeping ? "Processing Sweep..." : "Run Renewal & Expiry Sweep"}</span>
            </button>
          </div>
        </div>

        {sweepResult && (
          <div className="p-3.5 rounded-lg border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-800 dark:text-indigo-200 text-xs flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-indigo-600" />
            <span>{sweepResult}</span>
          </div>
        )}

        {/* 6 Key Operational Telemetry Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          <Link
            href="/app/legal/contracts"
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:shadow-md transition group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Contracts in Review</span>
              <span className="p-2 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">
                <FileText className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {dashboard.contracts_pending_review_count}
              </span>
              <span className="text-[10px] text-blue-600 font-medium">Pending Approvals</span>
            </div>
          </Link>

          <Link
            href="/app/legal/contracts?status=EXPIRING"
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:shadow-md transition group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Expiring Soon</span>
              <span className="p-2 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400">
                <Clock className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {dashboard.contracts_expiring_soon_count}
              </span>
              <span className="text-[10px] text-amber-600 font-medium">&lt; 60 Days Window</span>
            </div>
          </Link>

          <Link
            href="/app/legal/obligations"
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:shadow-md transition group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Overdue Obligations</span>
              <span className="p-2 rounded-lg bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400">
                <AlertTriangle className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {dashboard.obligations_overdue_count}
              </span>
              <span className="text-[10px] text-rose-600 font-medium">Action Required</span>
            </div>
          </Link>

          <Link
            href="/app/legal/matters"
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:shadow-md transition group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Legal Matters</span>
              <span className="p-2 rounded-lg bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400">
                <Gavel className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {dashboard.open_legal_matters_count}
              </span>
              <span className="text-[10px] text-purple-600 font-medium">Restricted Cases</span>
            </div>
          </Link>

          <Link
            href="/app/legal/compliance"
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:shadow-md transition group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Compliance Actions</span>
              <span className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
                <ShieldCheck className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {dashboard.compliance_actions_outstanding_count}
              </span>
              <span className="text-[10px] text-emerald-600 font-medium">Active Remediation</span>
            </div>
          </Link>

          <Link
            href="/app/legal/risks"
            className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:shadow-md transition group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">High Risks</span>
              <span className="p-2 rounded-lg bg-red-50 dark:bg-red-950/60 text-red-600 dark:text-red-400">
                <ShieldAlert className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                {dashboard.high_priority_risks_count}
              </span>
              <span className="text-[10px] text-red-600 font-medium">Score &gt;= 13</span>
            </div>
          </Link>
        </div>

        {/* Two-Column Grid: Contracts & Risk Matrix */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Contracts Section */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Active & In-Progress Contracts
                </h3>
              </div>
              <Link
                href="/app/legal/contracts"
                className="text-xs text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 font-medium flex items-center gap-1"
              >
                <span>View All</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="space-y-3">
              {dashboard.recent_contracts.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500">No recent contracts found.</div>
              ) : (
                dashboard.recent_contracts.map((contract) => {
                  const badge = getContractStatusBadge(contract.status);
                  return (
                    <Link
                      key={contract.id}
                      href={`/app/legal/contracts/${contract.id}`}
                      className="block p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 hover:border-indigo-200 dark:hover:border-indigo-800 bg-slate-50/50 dark:bg-slate-800/40 transition"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono font-semibold text-slate-500">
                              {contract.contract_number}
                            </span>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${badge.className}`}
                            >
                              {badge.label}
                            </span>
                          </div>
                          <h4 className="text-xs font-bold text-slate-900 dark:text-white mt-1">
                            {contract.title}
                          </h4>
                          <p className="text-[11px] text-slate-500 mt-0.5">
                            Counterparty: <span className="font-medium text-slate-700 dark:text-slate-300">{contract.counterparty_name}</span>
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          {contract.financial_value && (
                            <div className="text-xs font-bold text-slate-900 dark:text-white">
                              ${contract.financial_value.toLocaleString()}
                            </div>
                          )}
                          <div className="text-[10px] text-slate-400 mt-0.5">
                            Exp: {contract.expiration_date || "N/A"}
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })
              )}
            </div>
          </div>

          {/* 5x5 Enterprise Risk Register Snapshot */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-red-600 dark:text-red-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Institutional Risk Register (5x5 Matrix)
                </h3>
              </div>
              <Link
                href="/app/legal/risks"
                className="text-xs text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 font-medium flex items-center gap-1"
              >
                <span>Full Matrix</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="space-y-3">
              {dashboard.critical_risks.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500">No critical residual risks registered.</div>
              ) : (
                dashboard.critical_risks.map((risk) => {
                  const matrix = calculateRiskMatrix(risk.residual_likelihood, risk.residual_impact);
                  return (
                    <div
                      key={risk.id}
                      className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono font-semibold text-slate-500">
                              {risk.risk_code}
                            </span>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${matrix.badgeClass}`}
                            >
                              {matrix.label} (Score {risk.residual_score})
                            </span>
                          </div>
                          <h4 className="text-xs font-bold text-slate-900 dark:text-white mt-1">
                            {risk.title}
                          </h4>
                          <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">
                            Mitigation: {risk.mitigation_plan || "No active mitigation plan documented."}
                          </p>
                        </div>
                        <div className="text-right shrink-0 text-xs">
                          <span className="text-[10px] text-slate-400 block">Inherent vs Residual</span>
                          <span className="font-semibold text-slate-700 dark:text-slate-300">
                            {risk.inherent_score} &rarr; {risk.residual_score}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Bottom Section: Confidential Matters & Overdue Obligations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Restricted Legal Matters */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Gavel className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Restricted Institutional Matters
                </h3>
              </div>
              <Link
                href="/app/legal/matters"
                className="text-xs text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 font-medium flex items-center gap-1"
              >
                <span>View Matters</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="space-y-3">
              {dashboard.critical_matters.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500">No active legal matters on record.</div>
              ) : (
                dashboard.critical_matters.map((matter) => (
                  <div
                    key={matter.id}
                    className="p-3.5 rounded-lg border border-purple-100 dark:border-purple-950 bg-purple-50/20 dark:bg-purple-950/20"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-semibold text-purple-700 dark:text-purple-300">
                            {matter.matter_number}
                          </span>
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 border border-purple-200 dark:bg-purple-900/60 dark:text-purple-300">
                            {matter.restricted_classification.replace(/_/g, " ")}
                          </span>
                        </div>
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white mt-1">
                          {matter.title}
                        </h4>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Opposing Party: <span className="font-medium text-slate-700 dark:text-slate-300">{matter.counterparty_name || "N/A"}</span>
                        </p>
                      </div>
                      <div className="text-right shrink-0 text-xs">
                        {matter.financial_exposure_estimate && (
                          <span className="font-semibold text-rose-600 block">
                            Est: ${matter.financial_exposure_estimate.toLocaleString()}
                          </span>
                        )}
                        <span className="text-[10px] text-slate-400">Opened {matter.opened_date}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Overdue Obligations */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-600 dark:text-rose-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Contractual Commitments & Overdue Action
                </h3>
              </div>
              <Link
                href="/app/legal/obligations"
                className="text-xs text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 font-medium flex items-center gap-1"
              >
                <span>Obligations Register</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            <div className="space-y-3">
              {dashboard.overdue_obligations.length === 0 ? (
                <div className="p-8 text-center text-xs text-emerald-600 font-medium flex flex-col items-center gap-1">
                  <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                  <span>All contractual obligations and milestones are currently up to date.</span>
                </div>
              ) : (
                dashboard.overdue_obligations.map((obl) => (
                  <div
                    key={obl.id}
                    className="p-3.5 rounded-lg border border-rose-100 dark:border-rose-950 bg-rose-50/20 dark:bg-rose-950/20 flex items-center justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-semibold text-rose-700 dark:text-rose-300">
                          {obl.obligation_code}
                        </span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-200">
                          Due: {obl.due_date}
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white mt-1">
                        {obl.title}
                      </h4>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Type: {obl.obligation_type.replace(/_/g, " ")}
                      </p>
                    </div>
                    <Link
                      href="/app/legal/obligations"
                      className="px-3 py-1 text-xs font-semibold rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-indigo-400 transition shrink-0"
                    >
                      Resolve
                    </Link>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

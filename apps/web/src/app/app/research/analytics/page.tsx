"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Award,
  BarChart3,
  Calendar,
  CheckCircle2,
  DollarSign,
  Download,
  FileCheck2,
  FileText,
  Filter,
  Flame,
  FolderKanban,
  Lightbulb,
  PieChart,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import { ResearchAnalyticsSummary } from "@/types/research";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export default function ResearchAnalyticsPage() {
  const [summary, setSummary] = useState<ResearchAnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [sweeping, setSweeping] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  async function loadAnalytics() {
    try {
      setLoading(true);
      const res = await ResearchService.getAnalyticsSummary();
      setSummary(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load research analytics");
    } finally {
      setLoading(false);
    }
  }

  async function handleTriggerSweep() {
    try {
      setSweeping(true);
      setErrorMsg(null);
      const res = await fetch("http://localhost:8000/api/v1/research/analytics/sweep", {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Sweep failed");
      }
      const data = await res.json();
      const sweepRes = data.data || data;
      setSuccessMsg(
        `Compliance sweep completed: ${sweepRes.notifications_dispatched || 0} notifications dispatched, ${
          sweepRes.expired_ethics_locked || 0
        } expired ethics protocols evaluated.`
      );
      await loadAnalytics();
    } catch (err: any) {
      setErrorMsg(err.message || "Sweep execution failed.");
    } finally {
      setSweeping(false);
    }
  }

  function handleExportReport() {
    if (!summary) return;
    const reportData = {
      generated_at: new Date().toISOString(),
      institution_metrics: {
        total_projects: summary.total_active_projects,
        active_grants_awarded_amount: summary.total_grant_funding_awarded,
        total_budget_allocated: summary.total_budget_allocated,
        actual_expenditures: summary.total_actual_expenditure,
        proposals_in_pipeline: summary.grant_proposals_in_pipeline,
        published_outputs: summary.total_research_outputs_verified,
        pending_ethics: summary.pending_ethics_reviews,
      },
    };
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `CampusOS-Research-Executive-Report-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setSuccessMsg("Executive report exported successfully.");
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <ResearchNav />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Alerts */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
            <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-rose-200">✕</button>
          </div>
        )}
        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span>{successMsg}</span>
            </div>
            <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:text-emerald-200">✕</button>
          </div>
        )}

        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <BarChart3 className="h-6 w-6 text-emerald-400" />
              Institutional Research Analytics & Executive Portfolio Intelligence
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Verifiable funding pipeline conversion, expenditure burn rates, deliverable completion, and compliance sweeps.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={handleTriggerSweep}
              disabled={sweeping}
              variant="outline"
              className="border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800 text-xs gap-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${sweeping ? "animate-spin text-emerald-400" : ""}`} />
              Run Compliance Sweep
            </Button>
            <Button
              onClick={handleExportReport}
              className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 shadow-sm text-xs"
            >
              <Download className="h-3.5 w-3.5" />
              Export Portfolio Dossier
            </Button>
          </div>
        </div>

        {/* Top KPI Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-5 bg-slate-900/60 border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Projects</span>
              <span className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
                <FolderKanban className="h-4 w-4" />
              </span>
            </div>
            <div className="text-3xl font-bold text-white mt-2">
              {summary?.total_active_projects || 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Multi-departmental portfolio</p>
          </Card>

          <Card className="p-5 bg-slate-900/60 border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Grant Funding Awarded</span>
              <span className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
                <DollarSign className="h-4 w-4" />
              </span>
            </div>
            <div className="text-3xl font-bold text-emerald-400 mt-2">
              ${Number(summary?.total_grant_funding_awarded || 0).toLocaleString(undefined, { minimumFractionDigits: 0 })}
            </div>
            <p className="text-xs text-slate-500 mt-1">Verified external sponsor awards</p>
          </Card>

          <Card className="p-5 bg-slate-900/60 border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Proposals in Pipeline</span>
              <span className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
                <FileText className="h-4 w-4" />
              </span>
            </div>
            <div className="text-3xl font-bold text-indigo-400 mt-2">
              {summary?.grant_proposals_in_pipeline || 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Under review / external sponsor</p>
          </Card>

          <Card className="p-5 bg-slate-900/60 border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Verified Publications</span>
              <span className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
                <Lightbulb className="h-4 w-4" />
              </span>
            </div>
            <div className="text-3xl font-bold text-sky-400 mt-2">
              {summary?.total_research_outputs_verified || 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Peer-reviewed & DOI indexed</p>
          </Card>
        </div>

        {/* Detailed Financial & Operational Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Financial Utilization Ledger */}
          <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-emerald-400" />
                  Portfolio Financial Utilization & Burn
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Preserves existing finance module as authoritative ledger.
                </p>
              </div>
              <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs">
                Ledger Reconciled
              </Badge>
            </div>

            <div className="space-y-4 pt-2">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Total Approved Budget Allocation</span>
                  <span className="font-semibold text-white">
                    ${Number(summary?.total_budget_allocated || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full w-full" />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Reconciled Actual Expenditure</span>
                  <span className="font-semibold text-emerald-400">
                    ${Number(summary?.total_actual_expenditure || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div
                    className="bg-emerald-400 h-2 rounded-full"
                    style={{
                      width: `${Math.min(
                        100,
                        summary?.total_budget_allocated
                          ? ((summary.total_actual_expenditure || 0) / summary.total_budget_allocated) * 100
                          : 0
                      )}%`,
                    }}
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 block">Remaining Portfolio Balance</span>
                  <span className="text-lg font-bold text-white mt-0.5 block">
                    ${Math.max(
                      0,
                      Number(summary?.total_budget_allocated || 0) - Number(summary?.total_actual_expenditure || 0)
                    ).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Portfolio Burn</span>
                  <span className="text-lg font-bold text-amber-400 mt-0.5 block">
                    {summary?.total_budget_allocated && summary.total_budget_allocated > 0
                      ? (((summary.total_actual_expenditure || 0) / summary.total_budget_allocated) * 100).toFixed(1)
                      : "0.0"}
                    %
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* Institutional Compliance & Governance Health */}
          <Card className="p-6 bg-slate-900/60 border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  Institutional Compliance & Governance Health
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Ethics clearances, deliverable milestones, and safety gates.
                </p>
              </div>
              <Badge className="bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs">
                Audited Gates
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-xs text-slate-400 block">Pending Ethics Reviews</span>
                <span className="text-2xl font-bold text-amber-400 mt-1 block">
                  {summary?.pending_ethics_reviews || 0}
                </span>
                <p className="text-[11px] text-slate-500 mt-1">IRB/IACUC queues</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <span className="text-xs text-slate-400 block">Active Sponsored Grants</span>
                <span className="text-2xl font-bold text-emerald-400 mt-1 block">
                  {summary?.active_grants_count || 0}
                </span>
                <p className="text-[11px] text-slate-500 mt-1">External agreements</p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-xs text-slate-400 space-y-2">
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Operational Closure Blocking Active
              </div>
              <p>
                CampusOS Step 61 enforces strict multi-gate criteria before any project transitions to CLOSED: all mandatory deliverables verified by independent reviewers, ethics protocol renewals current, and financial ledger balances reconciled.
              </p>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}

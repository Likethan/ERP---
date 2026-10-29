"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCheck,
  FileText,
  Filter,
  History,
  Lock,
  Plus,
  RefreshCw,
  Scale,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  User,
  X,
  XCircle,
} from "lucide-react";
import { LegalNav } from "@/components/legal/legal-nav";
import { legalService } from "@/services/legal.service";
import {
  calculateRiskMatrix,
  formatLegalDate,
  getRiskLevelBadge,
} from "@/services/legal-calculator";
import {
  InstitutionalRisk,
  RiskAcceptInput,
  RiskCategory,
  RiskCreateInput,
  RiskLevel,
  RiskStatus,
} from "@/types/legal";

export default function RiskRegisterPage() {
  const [risks, setRisks] = useState<InstitutionalRisk[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedLevel, setSelectedLevel] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isAcceptOpen, setIsAcceptOpen] = useState(false);
  const [selectedRisk, setSelectedRisk] = useState<InstitutionalRisk | null>(null);

  // Create form
  const [newTitle, setNewTitle] = useState("");
  const [newCategory, setNewCategory] = useState<RiskCategory>("INFORMATION_SECURITY_PRIVACY");
  const [newDescription, setNewDescription] = useState("");
  const [newExistingControls, setNewExistingControls] = useState("");
  const [newMitigationPlan, setNewMitigationPlan] = useState("");
  const [newInherentLikelihood, setNewInherentLikelihood] = useState(4);
  const [newInherentImpact, setNewInherentImpact] = useState(4);
  const [newResidualLikelihood, setNewResidualLikelihood] = useState(2);
  const [newResidualImpact, setNewResidualImpact] = useState(3);
  const [newTargetDate, setNewTargetDate] = useState("");

  // Accept form
  const [acceptedBy, setAcceptedBy] = useState("President & Board Audit Committee");
  const [acceptRationale, setAcceptRationale] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadRisks();
  }, [selectedCategory, selectedLevel, selectedStatus]);

  async function loadRisks() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await legalService.getRisks({
        category: selectedCategory !== "ALL" ? selectedCategory : undefined,
        risk_level: selectedLevel !== "ALL" ? selectedLevel : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
      });
      setRisks(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load risk register");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: RiskCreateInput = {
        title: newTitle,
        category: newCategory,
        description: newDescription,
        existing_controls: newExistingControls || undefined,
        mitigation_plan: newMitigationPlan || undefined,
        inherent_likelihood: newInherentLikelihood,
        inherent_impact: newInherentImpact,
        residual_likelihood: newResidualLikelihood,
        residual_impact: newResidualImpact,
        target_resolution_date: newTargetDate || undefined,
      };
      await legalService.createRisk(input);
      setIsCreateOpen(false);
      resetCreateForm();
      await loadRisks();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create risk assessment");
    } finally {
      setIsSubmitting(false);
    }
  }

  function resetCreateForm() {
    setNewTitle("");
    setNewDescription("");
    setNewExistingControls("");
    setNewMitigationPlan("");
    setNewTargetDate("");
  }

  async function handleAcceptSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedRisk) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const input: RiskAcceptInput = {
        accepted_by: acceptedBy,
        rationale: acceptRationale,
      };
      await legalService.acceptRisk(selectedRisk.id, input);
      setIsAcceptOpen(false);
      setAcceptRationale("");
      await loadRisks();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to accept residual risk");
    } finally {
      setIsSubmitting(false);
    }
  }

  // Pre-calculated matrix preview for create modal
  const inherentCalc = calculateRiskMatrix(newInherentLikelihood, newInherentImpact);
  const residualCalc = calculateRiskMatrix(newResidualLikelihood, newResidualImpact);

  const filteredRisks = risks.filter((r) => {
    const identifier = r.risk_identifier || r.risk_code || "";
    if (
      searchTerm &&
      !r.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !identifier.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !r.category.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <LegalNav />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <ShieldAlert className="h-6 w-6 text-indigo-600" /> Enterprise Institutional Risk Register
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Quantitative 5×5 enterprise risk scoring, inherent vs residual risk mitigation, and executive residual risk acceptance.
            </p>
          </div>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
          >
            <Plus className="h-4 w-4" /> Assess New Institutional Risk
          </button>
        </div>

        {/* 5x5 Matrix Heatmap Card */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Scale className="h-5 w-5 text-indigo-600" /> Explainable 5×5 Enterprise Risk Matrix
              </h2>
              <p className="text-xs text-slate-500">
                Formula: Likelihood (1-5) × Impact (1-5) = Score (1-25). Hover cells to see risk concentration.
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs font-semibold">
              <span className="flex items-center gap-1.5 text-emerald-600">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Low (1-4)
              </span>
              <span className="flex items-center gap-1.5 text-yellow-600">
                <span className="h-2.5 w-2.5 rounded-full bg-yellow-500" /> Medium (5-9)
              </span>
              <span className="flex items-center gap-1.5 text-amber-600">
                <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> High (10-15)
              </span>
              <span className="flex items-center gap-1.5 text-rose-600">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-500" /> Critical (16-25)
              </span>
            </div>
          </div>

          {/* Matrix Grid Visualization */}
          <div className="overflow-x-auto pb-2">
            <div className="min-w-[600px] grid grid-cols-6 gap-2 text-center text-xs">
              {/* Header row */}
              <div className="text-[11px] font-bold text-slate-400 flex items-center justify-center">
                Likelihood ↓ / Impact →
              </div>
              <div className="font-semibold text-slate-600 dark:text-slate-400 py-1">1 - Negligible</div>
              <div className="font-semibold text-slate-600 dark:text-slate-400 py-1">2 - Minor</div>
              <div className="font-semibold text-slate-600 dark:text-slate-400 py-1">3 - Moderate</div>
              <div className="font-semibold text-slate-600 dark:text-slate-400 py-1">4 - Major</div>
              <div className="font-semibold text-slate-600 dark:text-slate-400 py-1">5 - Catastrophic</div>

              {/* Rows: Likelihood from 5 down to 1 */}
              {[5, 4, 3, 2, 1].map((likelihood) => (
                <div key={likelihood} className="contents">
                  <div className="font-semibold text-slate-600 dark:text-slate-400 flex items-center justify-center">
                    Level {likelihood}
                  </div>
                  {[1, 2, 3, 4, 5].map((impact) => {
                    const score = likelihood * impact;
                    const count = risks.filter(
                      (r) => r.residual_likelihood === likelihood && r.residual_impact === impact
                    ).length;

                    let bgClass = "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800";
                    if (score >= 16) {
                      bgClass = "bg-rose-50 dark:bg-rose-950/60 text-rose-800 dark:text-rose-200 border-rose-300 dark:border-rose-800";
                    } else if (score >= 10) {
                      bgClass = "bg-amber-50 dark:bg-amber-950/50 text-amber-800 dark:text-amber-200 border-amber-300 dark:border-amber-800";
                    } else if (score >= 5) {
                      bgClass = "bg-yellow-50 dark:bg-yellow-950/40 text-yellow-800 dark:text-yellow-200 border-yellow-200 dark:border-yellow-800";
                    }

                    return (
                      <div
                        key={`${likelihood}-${impact}`}
                        className={`p-3 rounded-xl border flex flex-col items-center justify-center transition-transform hover:scale-105 shadow-xs ${bgClass}`}
                      >
                        <span className="font-mono text-[10px] opacity-70">Score: {score}</span>
                        <div className="text-sm font-bold mt-0.5">
                          {count > 0 ? (
                            <span className="px-2 py-0.5 rounded-full bg-slate-900/10 dark:bg-white/20">
                              {count} {count === 1 ? "Risk" : "Risks"}
                            </span>
                          ) : (
                            <span className="text-slate-400 dark:text-slate-600 font-normal">—</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Filter and Search Bar */}
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="relative w-full md:w-96">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search risk identifier, title, or category..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm text-slate-900 dark:text-white"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Risk Domains</option>
                <option value="LEGAL_COMPLIANCE">Legal & Statutory Compliance</option>
                <option value="CONTRACTUAL">Contractual Breach & Counterparty</option>
                <option value="FINANCIAL">Financial Solvency & Liquidity</option>
                <option value="OPERATIONAL">Operational Disruption & Infrastructure</option>
                <option value="REPUTATIONAL">Reputational & Public Trust</option>
                <option value="INFORMATION_SECURITY">Cybersecurity & Data Privacy</option>
                <option value="RESEARCH_INTEGRITY">Research Integrity & IP</option>
                <option value="CAMPUS_SAFETY">Campus Safety & Emergency</option>
              </select>

              <select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical (Score 16-25)</option>
                <option value="HIGH">High (Score 10-15)</option>
                <option value="MEDIUM">Medium (Score 5-9)</option>
                <option value="LOW">Low (Score 1-4)</option>
              </select>

              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="ALL">All Statuses</option>
                <option value="IDENTIFIED">Identified</option>
                <option value="ASSESSED">Assessed</option>
                <option value="MITIGATION_ACTIVE">Mitigation Active</option>
                <option value="RESIDUAL_ACCEPTED">Residual Accepted</option>
                <option value="MONITORED">Monitored</option>
                <option value="CLOSED">Closed</option>
              </select>

              <button
                onClick={loadRisks}
                className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                title="Refresh risks"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Risks Register Table */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-600" />
              <p className="text-xs">Loading institutional risk register...</p>
            </div>
          ) : filteredRisks.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <ShieldCheck className="h-8 w-8 mx-auto text-slate-300" />
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No Risks Recorded</p>
              <p className="text-xs text-slate-500">No risk items match your query.</p>
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-6 py-3.5">Risk Item</th>
                  <th className="px-6 py-3.5">Category</th>
                  <th className="px-6 py-3.5">Inherent vs Residual</th>
                  <th className="px-6 py-3.5">Mitigation Plan</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {filteredRisks.map((risk) => (
                  <tr key={risk.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                          {risk.risk_identifier}
                        </span>
                        <strong className="text-slate-900 dark:text-white">{risk.title}</strong>
                      </div>
                      {risk.description && (
                        <p className="text-xs text-slate-500 line-clamp-1 mt-1">{risk.description}</p>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-600 dark:text-slate-300">
                      {risk.category.replace(/_/g, " ")}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-xs">
                        <div className="text-center">
                          <span className="text-[10px] text-slate-400 block">Inherent</span>
                          <span
                            className={`px-2 py-0.5 rounded font-mono font-bold ${getRiskLevelBadge(
                              risk.inherent_level || risk.risk_level
                            )}`}
                          >
                            {risk.inherent_score}
                          </span>
                        </div>
                        <TrendingDown className="h-4 w-4 text-emerald-500" />
                        <div className="text-center">
                          <span className="text-[10px] text-slate-400 block">Residual</span>
                          <span
                            className={`px-2 py-0.5 rounded font-mono font-bold ${getRiskLevelBadge(
                              risk.residual_level || risk.risk_level
                            )}`}
                          >
                            {risk.residual_score}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-600 dark:text-slate-400 max-w-xs">
                      {risk.mitigation_plan || (
                        <span className="italic text-slate-400">No active mitigation registered</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {risk.status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {(risk.status as string) !== "RESIDUAL_ACCEPTED" &&
                        (risk.status as string) !== "RESIDUAL_RISK_ACCEPTED" && (
                        <button
                          onClick={() => {
                            setSelectedRisk(risk);
                            setIsAcceptOpen(true);
                          }}
                          className="px-2.5 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 text-xs font-medium hover:bg-amber-100 transition-colors"
                        >
                          Accept Residual Risk
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* MODAL 1: Assess New Risk */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-xl w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-indigo-600" /> New Institutional Risk Assessment
              </h3>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Risk Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Critical Campus Fiber Cut / Core Data Center Single Point of Failure"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Risk Domain
                </label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value as RiskCategory)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                >
                  <option value="INFORMATION_SECURITY">INFORMATION_SECURITY</option>
                  <option value="LEGAL_COMPLIANCE">LEGAL_COMPLIANCE</option>
                  <option value="CONTRACTUAL">CONTRACTUAL</option>
                  <option value="FINANCIAL">FINANCIAL</option>
                  <option value="OPERATIONAL">OPERATIONAL</option>
                  <option value="CAMPUS_SAFETY">CAMPUS_SAFETY</option>
                  <option value="RESEARCH_INTEGRITY">RESEARCH_INTEGRITY</option>
                  <option value="REPUTATIONAL">REPUTATIONAL</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Risk Description & Vulnerability Analysis
                </label>
                <textarea
                  rows={2}
                  placeholder="Describe root cause, potential damages, and institutional impacts..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              {/* Inherent Risk Scoring */}
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                    Inherent Risk (Pre-Controls)
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded font-mono font-bold ${inherentCalc.badgeClass}`}>
                    Score: {inherentCalc.score} ({inherentCalc.level})
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-slate-500 mb-1">Likelihood (1-5): {newInherentLikelihood}</label>
                    <input
                      type="range"
                      min={1}
                      max={5}
                      value={newInherentLikelihood}
                      onChange={(e) => setNewInherentLikelihood(parseInt(e.target.value))}
                      className="w-full accent-indigo-600"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-500 mb-1">Impact (1-5): {newInherentImpact}</label>
                    <input
                      type="range"
                      min={1}
                      max={5}
                      value={newInherentImpact}
                      onChange={(e) => setNewInherentImpact(parseInt(e.target.value))}
                      className="w-full accent-indigo-600"
                    />
                  </div>
                </div>
              </div>

              {/* Residual Risk Scoring */}
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                    Residual Risk (Post-Mitigation)
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded font-mono font-bold ${residualCalc.badgeClass}`}>
                    Score: {residualCalc.score} ({residualCalc.level})
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-slate-500 mb-1">Residual Likelihood: {newResidualLikelihood}</label>
                    <input
                      type="range"
                      min={1}
                      max={5}
                      value={newResidualLikelihood}
                      onChange={(e) => setNewResidualLikelihood(parseInt(e.target.value))}
                      className="w-full accent-indigo-600"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-500 mb-1">Residual Impact: {newResidualImpact}</label>
                    <input
                      type="range"
                      min={1}
                      max={5}
                      value={newResidualImpact}
                      onChange={(e) => setNewResidualImpact(parseInt(e.target.value))}
                      className="w-full accent-indigo-600"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Mitigation Plan & Compensating Controls
                </label>
                <textarea
                  rows={2}
                  placeholder="Outline preventive controls, secondary routing, or contractual indemnification..."
                  value={newMitigationPlan}
                  onChange={(e) => setNewMitigationPlan(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              {errorMsg && (
                <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950 text-rose-700 text-xs">
                  {errorMsg}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  {isSubmitting ? "Creating..." : "Save Risk Assessment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Accept Residual Risk */}
      {isAcceptOpen && selectedRisk && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-amber-600" /> Executive Residual Risk Acceptance
              </h3>
              <button
                onClick={() => setIsAcceptOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                <strong>Institutional Governance Rule:</strong> Accepting residual risk indicates that further mitigation costs exceed risk tolerance. This creates a permanent Board Audit Committee audit entry.
              </span>
            </div>

            <form onSubmit={handleAcceptSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Authorizing Executive Body / Official
                </label>
                <input
                  type="text"
                  value={acceptedBy}
                  onChange={(e) => setAcceptedBy(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Executive Risk Tolerance Rationale
                </label>
                <textarea
                  rows={3}
                  placeholder="Document cost-benefit analysis, insurance coverage, or institutional rationale..."
                  value={acceptRationale}
                  onChange={(e) => setAcceptRationale(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAcceptOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-amber-600 text-white text-xs font-medium hover:bg-amber-700"
                >
                  {isSubmitting ? "Recording..." : "Formally Accept Risk"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

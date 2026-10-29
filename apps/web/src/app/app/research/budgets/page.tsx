"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowUpRight,
  BarChart2,
  CheckCircle2,
  DollarSign,
  FileEdit,
  FileSpreadsheet,
  History,
  Lock,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import {
  ResearchBudgetPlan,
  ResearchFinancialSummaryResponse,
  ResearchProject,
} from "@/types/research";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function ResearchBudgetsPage() {
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [budgetPlans, setBudgetPlans] = useState<ResearchBudgetPlan[]>([]);
  const [financialSummary, setFinancialSummary] = useState<ResearchFinancialSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showReviseModal, setShowReviseModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<ResearchBudgetPlan | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form states for new allocation
  const [newPlan, setNewPlan] = useState({
    plan_code: "",
    category: "RESEARCH_OPERATING",
    total_budget: 50000,
    personnel_costs: 25000,
    equipment_costs: 10000,
    consumables_materials_costs: 5000,
    travel_fieldwork_costs: 3000,
    external_services_costs: 2000,
    institutional_overheads: 3000,
    contingency_costs: 2000,
  });

  // Form states for revision
  const [revisionData, setRevisionData] = useState({
    revised_amount: 60000,
    revision_reason: "",
  });

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadProjectBudgets(selectedProjectId);
    } else {
      loadAllBudgets();
    }
  }, [selectedProjectId]);

  async function loadProjects() {
    try {
      setLoading(true);
      const res = await ResearchService.getProjects({ limit: 100 });
      const items = Array.isArray(res) ? res : [];
      setProjects(items);
      if (items.length > 0) {
        setSelectedProjectId(items[0].id);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }

  async function loadProjectBudgets(projectId: string) {
    try {
      setLoading(true);
      const [plans, summary] = await Promise.all([
        ResearchService.getBudgetPlans(projectId),
        ResearchService.getProjectFinancialSummary(projectId).catch(() => null),
      ]);
      setBudgetPlans(Array.isArray(plans) ? plans : []);
      setFinancialSummary(summary);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load budget plans");
    } finally {
      setLoading(false);
    }
  }

  async function loadAllBudgets() {
    try {
      setLoading(true);
      const plans = await ResearchService.getBudgetPlans();
      setBudgetPlans(Array.isArray(plans) ? plans : []);
      setFinancialSummary(null);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load budget plans");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateAllocation(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProjectId) {
      setErrorMsg("Please select a project for this budget allocation.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await ResearchService.createBudgetPlan({
        project_id: selectedProjectId,
        plan_code: newPlan.plan_code || `BGT-${Date.now().toString().slice(-6)}`,
        category: newPlan.category,
        total_budget: Number(newPlan.total_budget),
        personnel_costs: Number(newPlan.personnel_costs),
        equipment_costs: Number(newPlan.equipment_costs),
        consumables_materials_costs: Number(newPlan.consumables_materials_costs),
        travel_fieldwork_costs: Number(newPlan.travel_fieldwork_costs),
        external_services_costs: Number(newPlan.external_services_costs),
        institutional_overheads: Number(newPlan.institutional_overheads),
        contingency_costs: Number(newPlan.contingency_costs),
      });
      setSuccessMsg("Itemized budget allocation registered.");
      setShowCreateModal(false);
      await loadProjectBudgets(selectedProjectId);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create budget plan.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRevisePlan(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPlan) return;

    try {
      setSubmitting(true);
      setErrorMsg(null);
      // Call backend revision endpoint
      const res = await fetch(`http://localhost:8000/api/v1/research/budgets/${selectedPlan.id}/revise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          revised_allocated_amount: Number(revisionData.revised_amount),
          revision_reason: revisionData.revision_reason,
        }),
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || "Revision failed");
      }
      setSuccessMsg("Budget revision audited and version updated.");
      setShowReviseModal(false);
      if (selectedProjectId) {
        await loadProjectBudgets(selectedProjectId);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record revision.");
    } finally {
      setSubmitting(false);
    }
  }

  const selectedProj = projects.find((p) => p.id === selectedProjectId);

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
              <DollarSign className="h-6 w-6 text-emerald-400" />
              Research Budgets & Finance Ledger Reconciliation
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Multi-category cost allocation, committed vs. actual spend, audited budget revisions, and ledger sync.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              className="h-9 px-3 rounded-md bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
            >
              <option value="">All Institutional Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.project_code} — {p.title.slice(0, 36)}...
                </option>
              ))}
            </select>
            <Button
              onClick={() => setShowCreateModal(true)}
              className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 shadow-sm text-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              New Budget Allocation
            </Button>
          </div>
        </div>

        {/* Finance Safeguard Guarantee Notice */}
        <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 flex items-start gap-3">
          <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-200">Finance Module Authoritative Source of Truth: </span>
            Actual expenditures and committed purchase orders are reconciled against the central general ledger. Research screens coordinate project budgets without creating parallel accounting ledgers or fabricating mock transaction records.
          </div>
        </div>

        {/* Reconciled Financial Summary Cards */}
        {financialSummary && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4 bg-slate-900/60 border-slate-800">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Approved Budget</span>
              <div className="text-2xl font-bold text-white mt-1">
                ${Number(financialSummary.approved_budget).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Awarded: ${Number(financialSummary.awarded_grant_total).toLocaleString()}
              </p>
            </Card>

            <Card className="p-4 bg-slate-900/60 border-slate-800">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Actual Expenditure</span>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                ${Number(financialSummary.actual_expenditure).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Committed POs: ${Number(financialSummary.committed_expenditure).toLocaleString()}
              </p>
            </Card>

            <Card className="p-4 bg-slate-900/60 border-slate-800">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Remaining Unspent Balance</span>
              <div className="text-2xl font-bold text-sky-400 mt-1">
                ${Number(financialSummary.remaining_balance).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <p className="text-xs text-slate-500 mt-1">Available for project burn</p>
            </Card>

            <Card className="p-4 bg-slate-900/60 border-slate-800">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Budget Burn Rate</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-2xl font-bold text-amber-400">
                  {financialSummary.burn_rate_percentage.toFixed(1)}%
                </span>
                {financialSummary.burn_rate_percentage > 90 && (
                  <Badge className="bg-rose-500/10 text-rose-400 border-rose-500/20 text-[10px]">
                    Near Limit
                  </Badge>
                )}
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                <div
                  className={`h-full ${
                    financialSummary.burn_rate_percentage > 90
                      ? "bg-rose-500"
                      : financialSummary.burn_rate_percentage > 70
                      ? "bg-amber-500"
                      : "bg-emerald-500"
                  }`}
                  style={{ width: `${Math.min(100, financialSummary.burn_rate_percentage)}%` }}
                />
              </div>
            </Card>
          </div>
        )}

        {/* Itemized Budget Allocation Table */}
        <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white">
                Itemized Cost Allocations {selectedProj ? `— ${selectedProj.project_code}` : ""}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Personnel, equipment, materials, external subcontracts, and institutional overhead allowances.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => (selectedProjectId ? loadProjectBudgets(selectedProjectId) : loadAllBudgets())}
              className="h-8 border-slate-700 bg-slate-800 text-slate-300 text-xs gap-1.5"
            >
              <RefreshCw className="h-3 w-3" />
              Sync Ledger
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/60 text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Plan Code / Version</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Total Allocation</th>
                  <th className="py-3 px-4">Direct Costs (Personnel + Equip)</th>
                  <th className="py-3 px-4">Consumables & Travel</th>
                  <th className="py-3 px-4">Overheads & Contingency</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-slate-400" />
                      Loading allocations...
                    </td>
                  </tr>
                ) : budgetPlans.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      No budget plans registered for this scope. Click &quot;New Budget Allocation&quot; to define cost categories.
                    </td>
                  </tr>
                ) : (
                  budgetPlans.map((plan) => {
                    const direct = Number(plan.personnel_costs || 0) + Number(plan.equipment_costs || 0);
                    const supplies = Number(plan.consumables_materials_costs || 0) + Number(plan.travel_fieldwork_costs || 0);
                    const overheads = Number(plan.institutional_overheads || 0) + Number(plan.contingency_costs || 0);

                    return (
                      <tr key={plan.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4">
                          <span className="font-semibold text-white block">{plan.plan_code}</span>
                          <span className="text-[11px] text-slate-400 flex items-center gap-1">
                            <History className="h-3 w-3" />
                            Version {plan.version_number}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <Badge className="bg-slate-800 text-slate-300 border-slate-700">
                            {plan.category}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-white font-bold">
                            ${Number(plan.total_budget).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-300">
                          <div>Personnel: ${Number(plan.personnel_costs || 0).toLocaleString()}</div>
                          <div className="text-slate-500">Equipment: ${Number(plan.equipment_costs || 0).toLocaleString()}</div>
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-300">
                          <div>Supplies: ${Number(plan.consumables_materials_costs || 0).toLocaleString()}</div>
                          <div className="text-slate-500">Travel: ${Number(plan.travel_fieldwork_costs || 0).toLocaleString()}</div>
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-300">
                          <div>Overheads: ${Number(plan.institutional_overheads || 0).toLocaleString()}</div>
                          <div className="text-slate-500">Contingency: ${Number(plan.contingency_costs || 0).toLocaleString()}</div>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedPlan(plan);
                              setRevisionData({
                                revised_amount: Number(plan.total_budget),
                                revision_reason: "",
                              });
                              setShowReviseModal(true);
                            }}
                            className="h-8 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs"
                          >
                            <FileEdit className="h-3.5 w-3.5 mr-1" />
                            Revise
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Modal: New Budget Allocation */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-2xl bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <DollarSign className="h-5 w-5 text-emerald-400" />
                Define Itemized Cost Allocation
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleCreateAllocation} className="space-y-4 pt-2">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-400">Budget Plan Code</Label>
                  <Input
                    placeholder="e.g. BGT-2026-Y1"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newPlan.plan_code}
                    onChange={(e) => setNewPlan({ ...newPlan, plan_code: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Total Approved Allocation ($) *</Label>
                  <Input
                    type="number"
                    required
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newPlan.total_budget}
                    onChange={(e) => setNewPlan({ ...newPlan, total_budget: Number(e.target.value) })}
                  />
                </div>
              </div>

              <div className="p-4 bg-slate-950/70 rounded-lg border border-slate-800 space-y-3">
                <span className="text-xs font-semibold text-emerald-400 block">Category Allocations</span>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-[11px] text-slate-400">Personnel & Staff ($)</Label>
                    <Input
                      type="number"
                      className="bg-slate-900 border-slate-800 mt-1 text-xs"
                      value={newPlan.personnel_costs}
                      onChange={(e) => setNewPlan({ ...newPlan, personnel_costs: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <Label className="text-[11px] text-slate-400">Capital Equipment ($)</Label>
                    <Input
                      type="number"
                      className="bg-slate-900 border-slate-800 mt-1 text-xs"
                      value={newPlan.equipment_costs}
                      onChange={(e) => setNewPlan({ ...newPlan, equipment_costs: Number(e.target.value) })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-[11px] text-slate-400">Consumables & Materials ($)</Label>
                    <Input
                      type="number"
                      className="bg-slate-900 border-slate-800 mt-1 text-xs"
                      value={newPlan.consumables_materials_costs}
                      onChange={(e) => setNewPlan({ ...newPlan, consumables_materials_costs: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <Label className="text-[11px] text-slate-400">Travel & Fieldwork ($)</Label>
                    <Input
                      type="number"
                      className="bg-slate-900 border-slate-800 mt-1 text-xs"
                      value={newPlan.travel_fieldwork_costs}
                      onChange={(e) => setNewPlan({ ...newPlan, travel_fieldwork_costs: Number(e.target.value) })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-[11px] text-slate-400">Institutional Overheads ($)</Label>
                    <Input
                      type="number"
                      className="bg-slate-900 border-slate-800 mt-1 text-xs"
                      value={newPlan.institutional_overheads}
                      onChange={(e) => setNewPlan({ ...newPlan, institutional_overheads: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <Label className="text-[11px] text-slate-400">Contingency Reserves ($)</Label>
                    <Input
                      type="number"
                      className="bg-slate-900 border-slate-800 mt-1 text-xs"
                      value={newPlan.contingency_costs}
                      onChange={(e) => setNewPlan({ ...newPlan, contingency_costs: Number(e.target.value) })}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  {submitting ? "Allocating..." : "Save Cost Allocation"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Modal: Revise Budget Plan */}
        <Dialog open={showReviseModal} onOpenChange={setShowReviseModal}>
          <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <FileEdit className="h-5 w-5 text-indigo-400" />
                Audited Budget Revision: {selectedPlan?.plan_code}
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleRevisePlan} className="space-y-4 pt-2">
              <div>
                <Label className="text-xs text-slate-400">Revised Total Allocation ($) *</Label>
                <Input
                  type="number"
                  required
                  className="bg-slate-950 border-slate-800 mt-1"
                  value={revisionData.revised_amount}
                  onChange={(e) => setRevisionData({ ...revisionData, revised_amount: Number(e.target.value) })}
                />
              </div>

              <div>
                <Label className="text-xs text-slate-400">Audit Justification & Reason *</Label>
                <Textarea
                  required
                  placeholder="Explain justification for budget re-allocation or scope modification..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={3}
                  value={revisionData.revision_reason}
                  onChange={(e) => setRevisionData({ ...revisionData, revision_reason: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowReviseModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-500 text-white">
                  {submitting ? "Revising..." : "Commit Audited Revision"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}

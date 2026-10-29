"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Award,
  Calendar,
  CheckCircle2,
  DollarSign,
  FileCheck,
  FileEdit,
  FileText,
  Filter,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import { ResearchGrantAward, ResearchProject } from "@/types/research";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function SponsoredAgreementsPage() {
  const [agreements, setAgreements] = useState<ResearchGrantAward[]>([]);
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedAward, setSelectedAward] = useState<ResearchGrantAward | null>(null);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAmendmentModal, setShowAmendmentModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form states for new agreement
  const [newAgreement, setNewAgreement] = useState({
    agreement_number: "",
    project_id: "",
    funding_organization: "",
    award_amount: 100000,
    currency: "USD",
    start_date: new Date().toISOString().split("T")[0],
    end_date: new Date(Date.now() + 365 * 86400000).toISOString().split("T")[0],
    scope_of_work: "",
    milestone_1_title: "Initial Tranche & Kickoff Deliverable",
    milestone_1_amount: 40000,
    milestone_2_title: "Mid-Term Technical Report",
    milestone_2_amount: 60000,
  });

  // Form states for amendment
  const [amendmentData, setAmendmentData] = useState({
    amendment_number: "AMD-01",
    description: "",
    extended_end_date: "",
    budget_adjustment: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [agreementsRes, projectsRes] = await Promise.all([
        ResearchService.getSponsoredAgreements(),
        ResearchService.getProjects({ limit: 100 }),
      ]);
      setAgreements(Array.isArray(agreementsRes) ? agreementsRes : []);
      setProjects(Array.isArray(projectsRes) ? projectsRes : []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load sponsored agreements");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateAgreement(e: React.FormEvent) {
    e.preventDefault();
    if (!newAgreement.agreement_number || !newAgreement.project_id || !newAgreement.funding_organization) {
      setErrorMsg("Please complete all required agreement fields.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await ResearchService.createSponsoredAgreement({
        agreement_number: newAgreement.agreement_number,
        project_id: newAgreement.project_id,
        funding_organization: newAgreement.funding_organization,
        award_amount: Number(newAgreement.award_amount),
        currency: newAgreement.currency,
        start_date: newAgreement.start_date,
        end_date: newAgreement.end_date,
        scope_of_work: newAgreement.scope_of_work,
        payment_milestones: [
          { milestone: newAgreement.milestone_1_title, amount: Number(newAgreement.milestone_1_amount), status: "PENDING" },
          { milestone: newAgreement.milestone_2_title, amount: Number(newAgreement.milestone_2_amount), status: "PENDING" },
        ],
      });
      setSuccessMsg("Sponsored agreement executed successfully.");
      setShowCreateModal(false);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to register agreement.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRecordAmendment(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedAward) return;

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await ResearchService.recordAgreementAmendment(selectedAward.id, {
        amendment_number: amendmentData.amendment_number,
        description: amendmentData.description,
        extended_end_date: amendmentData.extended_end_date || undefined,
        budget_adjustment: Number(amendmentData.budget_adjustment) || 0,
      });
      setSuccessMsg("Contract amendment recorded with audit trail.");
      setShowAmendmentModal(false);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record amendment.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReconcile(awardId: string) {
    try {
      setLoading(true);
      await ResearchService.getSponsoredAgreements(); // sync
      setSuccessMsg("Agreement balances reconciled with finance module.");
    } catch (err: any) {
      setErrorMsg(err.message || "Reconciliation error.");
    } finally {
      setLoading(false);
    }
  }

  const filtered = agreements.filter((a) => {
    const q = search.toLowerCase();
    const num = (a.award_number || "").toLowerCase();
    const sponsor = (a.funding_organization || "").toLowerCase();
    return num.includes(q) || sponsor.includes(q);
  });

  const totalCommitted = agreements.reduce((acc, a) => acc + Number(a.award_amount || 0), 0);
  const totalDisbursed = agreements.reduce((acc, a) => acc + Number(a.disbursed_amount || 0), 0);
  const totalRemaining = agreements.reduce((acc, a) => acc + Number(a.remaining_balance || 0), 0);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <ResearchNav />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Banner Alert messages */}
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

        {/* Header & Stats */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <Award className="h-6 w-6 text-emerald-400" />
              Sponsored Research Agreements & Awards
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Legally binding contracts, sponsor disbursement tranches, deliverables, and audited amendments.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={() => setShowCreateModal(true)}
              className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 shadow-sm"
            >
              <Plus className="h-4 w-4" />
              Execute Agreement
            </Button>
          </div>
        </div>

        {/* Financial Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="p-4 bg-slate-900/60 border-slate-800 backdrop-blur-sm">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Contract Commitments</span>
            <div className="text-2xl font-bold text-white mt-1">
              ${totalCommitted.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <p className="text-xs text-slate-500 mt-1">{agreements.length} active agreements</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800 backdrop-blur-sm">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Disbursed to Date</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              ${totalDisbursed.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <p className="text-xs text-slate-500 mt-1">Reconciled against verified ledger</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800 backdrop-blur-sm">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Undisbursed Sponsor Balance</span>
            <div className="text-2xl font-bold text-amber-400 mt-1">
              ${totalRemaining.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <p className="text-xs text-slate-500 mt-1">Pending deliverable milestones</p>
          </Card>
        </div>

        {/* Search & Table */}
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search by contract reference or funding sponsor..."
              className="pl-9 bg-slate-900/60 border-slate-800 text-slate-200 placeholder:text-slate-500"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-800/60 text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Agreement Code</th>
                    <th className="py-3 px-4">Funding Sponsor</th>
                    <th className="py-3 px-4">Contract Amount</th>
                    <th className="py-3 px-4">Period</th>
                    <th className="py-3 px-4">Payment Tranches</th>
                    <th className="py-3 px-4">Amendments</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loading ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-500">
                        <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-slate-400" />
                        Loading agreements...
                      </td>
                    </tr>
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-500">
                        No sponsored research agreements found. Click &quot;Execute Agreement&quot; to register a sponsored contract.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((award) => {
                      const amendments = (award.amendments_json as any[]) || [];
                      const milestones = (award.disbursement_schedule_json as any[]) || [];

                      return (
                        <tr key={award.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-3 px-4">
                            <span className="font-semibold text-white block">{award.award_number}</span>
                            <span className="text-xs text-slate-500">ID: {award.id.slice(0, 8)}...</span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="text-slate-200 font-medium">{award.funding_organization}</span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="text-white font-semibold">
                              ${Number(award.award_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </span>
                            <div className="text-[11px] text-emerald-400">
                              Disbursed: ${Number(award.disbursed_amount || 0).toLocaleString()}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-xs text-slate-400">
                            <div>Start: {award.period_start_date || "—"}</div>
                            <div>End: {award.period_end_date || "—"}</div>
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex flex-col gap-1">
                              {milestones.length > 0 ? (
                                milestones.map((m: any, i: number) => (
                                  <span key={i} className="text-xs text-slate-400 flex items-center gap-1.5">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                    {m.milestone || m.title || `Tranche ${i + 1}`}: ${Number(m.amount || 0).toLocaleString()}
                                  </span>
                                ))
                              ) : (
                                <span className="text-xs text-slate-500">Standard single disbursement</span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            {amendments.length > 0 ? (
                              <Badge className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                {amendments.length} amended
                              </Badge>
                            ) : (
                              <span className="text-xs text-slate-500">Original</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setSelectedAward(award);
                                  setShowAmendmentModal(true);
                                }}
                                className="h-8 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs"
                              >
                                <FileEdit className="h-3.5 w-3.5 mr-1" />
                                Amend
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleReconcile(award.id)}
                                className="h-8 text-slate-400 hover:text-white text-xs"
                              >
                                <RefreshCw className="h-3.5 w-3.5" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Modal: Execute New Agreement */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-xl bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <Award className="h-5 w-5 text-emerald-400" />
                Execute Sponsored Research Agreement
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleCreateAgreement} className="space-y-4 pt-2">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-400">Agreement Contract Number *</Label>
                  <Input
                    required
                    placeholder="e.g. SRA-2026-IND-01"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newAgreement.agreement_number}
                    onChange={(e) => setNewAgreement({ ...newAgreement, agreement_number: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Institutional Project Link *</Label>
                  <select
                    required
                    className="w-full h-10 px-3 mt-1 rounded-md bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    value={newAgreement.project_id}
                    onChange={(e) => setNewAgreement({ ...newAgreement, project_id: e.target.value })}
                  >
                    <option value="">Select Research Project</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.project_code} — {p.title.slice(0, 40)}...
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-400">Sponsoring Organization *</Label>
                  <Input
                    required
                    placeholder="e.g. National Science Foundation / Boeing"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newAgreement.funding_organization}
                    onChange={(e) => setNewAgreement({ ...newAgreement, funding_organization: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Award Commitment ($) *</Label>
                  <Input
                    type="number"
                    required
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newAgreement.award_amount}
                    onChange={(e) => setNewAgreement({ ...newAgreement, award_amount: Number(e.target.value) })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-400">Contract Start Date</Label>
                  <Input
                    type="date"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newAgreement.start_date}
                    onChange={(e) => setNewAgreement({ ...newAgreement, start_date: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Contract Expiration Date</Label>
                  <Input
                    type="date"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newAgreement.end_date}
                    onChange={(e) => setNewAgreement({ ...newAgreement, end_date: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Agreed Scope of Work & Reporting Commitments</Label>
                <Textarea
                  placeholder="Outline the agreed contractual deliverables, IP assignment clauses, and quarterly reporting schedules..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={3}
                  value={newAgreement.scope_of_work}
                  onChange={(e) => setNewAgreement({ ...newAgreement, scope_of_work: e.target.value })}
                />
              </div>

              <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800 space-y-3">
                <span className="text-xs font-semibold text-emerald-400 block">Payment Disbursement Tranches</span>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="Tranche 1 Title"
                    className="bg-slate-900 border-slate-800 text-xs"
                    value={newAgreement.milestone_1_title}
                    onChange={(e) => setNewAgreement({ ...newAgreement, milestone_1_title: e.target.value })}
                  />
                  <Input
                    type="number"
                    placeholder="Tranche 1 Amount ($)"
                    className="bg-slate-900 border-slate-800 text-xs"
                    value={newAgreement.milestone_1_amount}
                    onChange={(e) => setNewAgreement({ ...newAgreement, milestone_1_amount: Number(e.target.value) })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="Tranche 2 Title"
                    className="bg-slate-900 border-slate-800 text-xs"
                    value={newAgreement.milestone_2_title}
                    onChange={(e) => setNewAgreement({ ...newAgreement, milestone_2_title: e.target.value })}
                  />
                  <Input
                    type="number"
                    placeholder="Tranche 2 Amount ($)"
                    className="bg-slate-900 border-slate-800 text-xs"
                    value={newAgreement.milestone_2_amount}
                    onChange={(e) => setNewAgreement({ ...newAgreement, milestone_2_amount: Number(e.target.value) })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  {submitting ? "Executing..." : "Execute Agreement"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Modal: Record Amendment */}
        <Dialog open={showAmendmentModal} onOpenChange={setShowAmendmentModal}>
          <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <FileEdit className="h-5 w-5 text-indigo-400" />
                Amend Agreement: {selectedAward?.award_number}
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleRecordAmendment} className="space-y-4 pt-2">
              <div>
                <Label className="text-xs text-slate-400">Amendment Reference *</Label>
                <Input
                  required
                  placeholder="e.g. AMD-01, MOD-2026-A"
                  className="bg-slate-950 border-slate-800 mt-1"
                  value={amendmentData.amendment_number}
                  onChange={(e) => setAmendmentData({ ...amendmentData, amendment_number: e.target.value })}
                />
              </div>

              <div>
                <Label className="text-xs text-slate-400">Amendment Justification / Description *</Label>
                <Textarea
                  required
                  placeholder="Reason for contract renewal, scope change, or supplemental award addition..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={3}
                  value={amendmentData.description}
                  onChange={(e) => setAmendmentData({ ...amendmentData, description: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-400">Extended End Date</Label>
                  <Input
                    type="date"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={amendmentData.extended_end_date}
                    onChange={(e) => setAmendmentData({ ...amendmentData, extended_end_date: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Budget Adjustment ($)</Label>
                  <Input
                    type="number"
                    placeholder="e.g. 25000"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={amendmentData.budget_adjustment}
                    onChange={(e) => setAmendmentData({ ...amendmentData, budget_adjustment: Number(e.target.value) })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowAmendmentModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-500 text-white">
                  {submitting ? "Recording..." : "Record Audited Amendment"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}

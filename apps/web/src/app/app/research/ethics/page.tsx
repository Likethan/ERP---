"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  FileCheck,
  FileText,
  Filter,
  Lock,
  Plus,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import { ResearchEthicsApproval, ResearchProject } from "@/types/research";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function ResearchEthicsPage() {
  const [approvals, setApprovals] = useState<ResearchEthicsApproval[]>([]);
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDecideModal, setShowDecideModal] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState<ResearchEthicsApproval | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form states
  const [newApproval, setNewApproval] = useState({
    approval_code: "",
    approval_type: "HUMAN_SUBJECTS_IRB",
    governing_policy_reference: "45-CFR-46-COMMON-RULE",
    review_committee_name: "Institutional Review Board (IRB)",
    conditions_and_restrictions: "",
  });

  const [decisionData, setDecisionData] = useState({
    decision: "APPROVED",
    decision_rationale: "",
    conditions_and_restrictions: "",
    expiry_date: new Date(Date.now() + 365 * 86400000).toISOString().split("T")[0],
  });

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    loadEthicsApprovals();
  }, [selectedProjectId]);

  async function loadProjects() {
    try {
      const res = await ResearchService.getProjects({ limit: 100 });
      setProjects(Array.isArray(res) ? res : []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load projects");
    }
  }

  async function loadEthicsApprovals() {
    try {
      setLoading(true);
      const res = await ResearchService.getEthicsApprovals(selectedProjectId || undefined);
      setApprovals(Array.isArray(res) ? res : []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load ethics protocols");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateApproval(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProjectId) {
      setErrorMsg("Please select a research project for this compliance protocol.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await ResearchService.createEthicsApproval({
        project_id: selectedProjectId,
        approval_code: newApproval.approval_code || `IRB-${Date.now().toString().slice(-6)}`,
        approval_type: newApproval.approval_type,
        governing_policy_reference: newApproval.governing_policy_reference,
        review_committee_name: newApproval.review_committee_name,
        conditions_and_restrictions: newApproval.conditions_and_restrictions || undefined,
      });
      setSuccessMsg("Ethics protocol registered with committee review queue.");
      setShowCreateModal(false);
      await loadEthicsApprovals();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to register ethics protocol.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRecordDecision(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedApproval) return;

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await ResearchService.recordEthicsDecision(selectedApproval.id, {
        decision: decisionData.decision,
        decision_rationale: decisionData.decision_rationale,
        conditions_and_restrictions: decisionData.conditions_and_restrictions || undefined,
        expiry_date: decisionData.expiry_date || undefined,
      });
      setSuccessMsg(`Official committee decision recorded: ${decisionData.decision}.`);
      setShowDecideModal(false);
      await loadEthicsApprovals();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to record committee decision.");
    } finally {
      setSubmitting(false);
    }
  }

  const filtered = approvals.filter((a) => {
    const q = search.toLowerCase();
    const code = (a.approval_code || "").toLowerCase();
    const committee = (a.review_committee_name || "").toLowerCase();
    return code.includes(q) || committee.includes(q);
  });

  const total = approvals.length;
  const approved = approvals.filter((a) => a.status === "APPROVED").length;
  const underReview = approvals.filter((a) => a.status === "UNDER_REVIEW" || a.status === "SUBMITTED").length;
  const expiringSoon = approvals.filter((a) => {
    if (!a.expiry_date) return false;
    const diffDays = (new Date(a.expiry_date).getTime() - Date.now()) / (1000 * 3600 * 24);
    return diffDays > 0 && diffDays <= 60;
  }).length;

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
              <ShieldCheck className="h-6 w-6 text-emerald-400" />
              Research Ethics & Institutional Compliance Registry
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              IRB, IACUC, and Biosafety committee oversight, protocol expiration monitoring, and compliance verification.
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
              Register Protocol
            </Button>
          </div>
        </div>

        {/* Statutory Compliance Notice */}
        <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 flex items-start gap-3">
          <Shield className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-200">Independent Institutional Oversight: </span>
            Ethics, biosafety, and animal welfare determinations are rendered solely by designated institutional review committees (IRB / IACUC / IBC). The system enforces safety locks preventing project activities when required clearances expire, without making automated legal or ethical determinations.
          </div>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Protocols</span>
            <div className="text-2xl font-bold text-white mt-1">{total}</div>
            <p className="text-xs text-slate-500 mt-1">Under committee registry</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Approved & Active</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{approved}</div>
            <p className="text-xs text-slate-500 mt-1">Valid institutional approval</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Under Committee Review</span>
            <div className="text-2xl font-bold text-amber-400 mt-1">{underReview}</div>
            <p className="text-xs text-slate-500 mt-1">Pending committee verdict</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Expiring Within 60 Days</span>
            <div className="text-2xl font-bold text-rose-400 mt-1">{expiringSoon}</div>
            <p className="text-xs text-slate-500 mt-1">Renewal required</p>
          </Card>
        </div>

        {/* Search & Table */}
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search by protocol code or review committee..."
              className="pl-9 bg-slate-900/60 border-slate-800 text-slate-200 placeholder:text-slate-500 text-xs"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-800/60 text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Protocol Reference</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Review Committee</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Expiry Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-slate-400" />
                        Loading compliance protocols...
                      </td>
                    </tr>
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        No ethics protocols registered. Click &quot;Register Protocol&quot; to submit a new compliance dossier.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((a) => {
                      const isApproved = a.status === "APPROVED";
                      const isExpired = a.expiry_date && new Date(a.expiry_date) < new Date();

                      return (
                        <tr key={a.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-3 px-4">
                            <span className="font-semibold text-white block">{a.approval_code}</span>
                            <span className="text-xs text-slate-400">Ref: {a.governing_policy_reference}</span>
                          </td>
                          <td className="py-3 px-4">
                            <Badge className="bg-slate-800 text-slate-300 border-slate-700 text-xs">
                              {a.approval_type}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-slate-300 font-medium">
                            {a.review_committee_name}
                          </td>
                          <td className="py-3 px-4">
                            <Badge
                              className={
                                isExpired
                                  ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                                  : isApproved
                                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                  : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                              }
                            >
                              {isExpired ? "EXPIRED" : a.status}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-xs">
                            {a.expiry_date ? (
                              <div className={isExpired ? "text-rose-400 font-semibold" : "text-slate-300"}>
                                {a.expiry_date}
                              </div>
                            ) : (
                              <span className="text-slate-500">No expiration set</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedApproval(a);
                                setDecisionData({
                                  decision: a.status === "APPROVED" ? "APPROVED" : "APPROVED",
                                  decision_rationale: a.decision_rationale || "",
                                  conditions_and_restrictions: a.conditions_and_restrictions || "",
                                  expiry_date: a.expiry_date || new Date(Date.now() + 365 * 86400000).toISOString().split("T")[0],
                                });
                                setShowDecideModal(true);
                              }}
                              className="h-8 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs"
                            >
                              <UserCheck className="h-3.5 w-3.5 mr-1" />
                              Record Decision
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
        </div>

        {/* Modal: Register Protocol */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-lg bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                Register Compliance Protocol
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleCreateApproval} className="space-y-4 pt-2">
              <div>
                <Label className="text-xs text-slate-400">Target Project *</Label>
                <select
                  required
                  className="w-full h-10 px-3 mt-1 rounded-md bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                >
                  <option value="">Select Research Project</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.project_code} — {p.title.slice(0, 40)}...
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-400">Protocol Code</Label>
                  <Input
                    placeholder="e.g. IRB-2026-088"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newApproval.approval_code}
                    onChange={(e) => setNewApproval({ ...newApproval, approval_code: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Compliance Category *</Label>
                  <select
                    className="w-full h-10 px-3 mt-1 rounded-md bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    value={newApproval.approval_type}
                    onChange={(e) => setNewApproval({ ...newApproval, approval_type: e.target.value })}
                  >
                    <option value="HUMAN_SUBJECTS_IRB">Human Subjects (IRB)</option>
                    <option value="ANIMAL_CARE_IACUC">Vertebrate Animals (IACUC)</option>
                    <option value="BIOSAFETY_IBC">Recombinant DNA / Biosafety (IBC)</option>
                    <option value="RADIATION_SAFETY">Radiation & Laser Safety</option>
                    <option value="EXPORT_CONTROL">Export Control & Security</option>
                  </select>
                </div>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Review Committee Name *</Label>
                <Input
                  required
                  className="bg-slate-950 border-slate-800 mt-1"
                  value={newApproval.review_committee_name}
                  onChange={(e) => setNewApproval({ ...newApproval, review_committee_name: e.target.value })}
                />
              </div>

              <div>
                <Label className="text-xs text-slate-400">Governing Policy Reference</Label>
                <Input
                  className="bg-slate-950 border-slate-800 mt-1"
                  value={newApproval.governing_policy_reference}
                  onChange={(e) => setNewApproval({ ...newApproval, governing_policy_reference: e.target.value })}
                />
              </div>

              <div>
                <Label className="text-xs text-slate-400">Special Protocol Conditions / Restrictions</Label>
                <Textarea
                  placeholder="Outline any special handling protocols, participant consent safeguards, or mandatory data isolation restrictions..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={3}
                  value={newApproval.conditions_and_restrictions}
                  onChange={(e) => setNewApproval({ ...newApproval, conditions_and_restrictions: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  {submitting ? "Registering..." : "Submit to Committee"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Modal: Committee Decision */}
        <Dialog open={showDecideModal} onOpenChange={setShowDecideModal}>
          <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <UserCheck className="h-5 w-5 text-emerald-400" />
                Record Official Committee Decision
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleRecordDecision} className="space-y-4 pt-2">
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 text-xs">
                <div className="font-semibold text-white">{selectedApproval?.approval_code}</div>
                <div className="text-slate-400 mt-1">Committee: {selectedApproval?.review_committee_name}</div>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Committee Decision *</Label>
                <select
                  required
                  className="w-full h-10 px-3 mt-1 rounded-md bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  value={decisionData.decision}
                  onChange={(e) => setDecisionData({ ...decisionData, decision: e.target.value })}
                >
                  <option value="APPROVED">APPROVED — Unconditional Full Clearance</option>
                  <option value="CONDITIONAL_APPROVAL">CONDITIONAL_APPROVAL — Specific Revisions Required</option>
                  <option value="CHANGES_REQUIRED">CHANGES_REQUIRED — Major Revisions Needed</option>
                  <option value="REJECTED">REJECTED — Protocol Denied</option>
                </select>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Protocol Expiration Date</Label>
                <Input
                  type="date"
                  className="bg-slate-950 border-slate-800 mt-1"
                  value={decisionData.expiry_date}
                  onChange={(e) => setDecisionData({ ...decisionData, expiry_date: e.target.value })}
                />
              </div>

              <div>
                <Label className="text-xs text-slate-400">Official Committee Rationale *</Label>
                <Textarea
                  required
                  placeholder="Record formal findings and minutes from the committee convened session..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={3}
                  value={decisionData.decision_rationale}
                  onChange={(e) => setDecisionData({ ...decisionData, decision_rationale: e.target.value })}
                />
              </div>

              <div>
                <Label className="text-xs text-slate-400">Stipulated Conditions & Reporting Requirements</Label>
                <Textarea
                  placeholder="Conditions of approval (e.g. Adverse event notification within 48h, annual continuing review)..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={2}
                  value={decisionData.conditions_and_restrictions}
                  onChange={(e) => setDecisionData({ ...decisionData, conditions_and_restrictions: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowDecideModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  {submitting ? "Recording..." : "Record Official Decision"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}

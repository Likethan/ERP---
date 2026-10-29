"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  FileCheck2,
  FileEdit,
  FileText,
  Filter,
  Lock,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import { ResearchMilestone, ResearchProject } from "@/types/research";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function ResearchMilestonesPage() {
  const [milestones, setMilestones] = useState<ResearchMilestone[]>([]);
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [selectedMilestone, setSelectedMilestone] = useState<ResearchMilestone | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form states
  const [newMilestone, setNewMilestone] = useState({
    milestone_code: "",
    title: "",
    description: "",
    planned_completion_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
    acceptance_criteria: "",
    is_mandatory_for_closure: true,
    deliverable_reference: "",
  });

  const [verifyData, setVerifyData] = useState({
    decision: "ACCEPTED",
    verification_notes: "",
  });

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    loadMilestones();
  }, [selectedProjectId]);

  async function loadProjects() {
    try {
      const res = await ResearchService.getProjects({ limit: 100 });
      setProjects(Array.isArray(res) ? res : []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load projects");
    }
  }

  async function loadMilestones() {
    try {
      setLoading(true);
      const res = await ResearchService.getMilestones(selectedProjectId || undefined);
      setMilestones(Array.isArray(res) ? res : []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load milestones");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateMilestone(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProjectId) {
      setErrorMsg("Please select a project to attach this milestone to.");
      return;
    }
    if (!newMilestone.title) {
      setErrorMsg("Milestone title is required.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await ResearchService.createMilestone({
        project_id: selectedProjectId,
        milestone_code: newMilestone.milestone_code || `MS-${Date.now().toString().slice(-6)}`,
        title: newMilestone.title,
        description: newMilestone.description,
        planned_completion_date: newMilestone.planned_completion_date,
        acceptance_criteria: newMilestone.acceptance_criteria || "Independent verification required",
        is_mandatory_for_closure: newMilestone.is_mandatory_for_closure,
        deliverable_reference: newMilestone.deliverable_reference,
      });
      setSuccessMsg("Milestone created successfully.");
      setShowCreateModal(false);
      await loadMilestones();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create milestone.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerifyMilestone(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedMilestone) return;

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await ResearchService.verifyMilestone(
        selectedMilestone.id,
        verifyData.decision,
        verifyData.verification_notes || `Milestone reviewed and marked ${verifyData.decision}`
      );
      setSuccessMsg(`Milestone verified with decision: ${verifyData.decision}.`);
      setShowVerifyModal(false);
      await loadMilestones();
    } catch (err: any) {
      setErrorMsg(err.message || "Verification failed.");
    } finally {
      setSubmitting(false);
    }
  }

  const filtered = milestones.filter((m) => {
    const q = search.toLowerCase();
    const matchSearch = (m.title || "").toLowerCase().includes(q) || (m.milestone_code || "").toLowerCase().includes(q);
    const matchStatus = statusFilter === "ALL" || m.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const total = milestones.length;
  const verified = milestones.filter((m) => m.status === "ACCEPTED" || m.status === "VERIFIED").length;
  const pendingReview = milestones.filter((m) => m.status === "UNDER_REVIEW").length;
  const mandatoryUnverified = milestones.filter((m) => m.is_mandatory_for_closure && m.status !== "ACCEPTED" && m.status !== "VERIFIED").length;

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
              <FileCheck2 className="h-6 w-6 text-emerald-400" />
              Milestones, Deliverables & Acceptance Queue
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Project execution tracking, independent verification reviews, and closure blocking enforcement.
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
              New Milestone
            </Button>
          </div>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Milestones</span>
            <div className="text-2xl font-bold text-white mt-1">{total}</div>
            <p className="text-xs text-slate-500 mt-1">Tracked across scope</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Verified / Accepted</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{verified}</div>
            <p className="text-xs text-slate-500 mt-1">Approved by reviewers</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Under Review</span>
            <div className="text-2xl font-bold text-amber-400 mt-1">{pendingReview}</div>
            <p className="text-xs text-slate-500 mt-1">Awaiting independent review</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Closure Blockers</span>
            <div className="text-2xl font-bold text-rose-400 mt-1">{mandatoryUnverified}</div>
            <p className="text-xs text-slate-500 mt-1">Mandatory unverified</p>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search by title or milestone code..."
              className="pl-9 bg-slate-900/60 border-slate-800 text-slate-200 placeholder:text-slate-500 text-xs"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            {["ALL", "PLANNED", "UNDER_REVIEW", "ACCEPTED", "REJECTED"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  statusFilter === st
                    ? "bg-emerald-600 text-white"
                    : "bg-slate-900 text-slate-400 hover:bg-slate-800 border border-slate-800"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {/* Milestone Table */}
        <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/60 text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Milestone</th>
                  <th className="py-3 px-4">Planned Date</th>
                  <th className="py-3 px-4">Completion</th>
                  <th className="py-3 px-4">Closure Status</th>
                  <th className="py-3 px-4">Review Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-slate-400" />
                      Loading milestones...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      No milestones matching criteria.
                    </td>
                  </tr>
                ) : (
                  filtered.map((m) => {
                    const isAccepted = m.status === "ACCEPTED" || m.status === "VERIFIED";
                    const isReview = m.status === "UNDER_REVIEW";

                    return (
                      <tr key={m.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4">
                          <div className="font-semibold text-white">{m.title}</div>
                          <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                            <span className="font-mono text-emerald-400">{m.milestone_code}</span>
                            {m.deliverable_reference && (
                              <span className="text-slate-500">• Ref: {m.deliverable_reference}</span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-300">
                          <div className="flex items-center gap-1.5">
                            <Calendar className="h-3.5 w-3.5 text-slate-500" />
                            {m.planned_completion_date}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium text-slate-300 w-9">
                              {Math.round(m.completion_percentage || 0)}%
                            </span>
                            <div className="w-20 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-emerald-500 h-full"
                                style={{ width: `${Math.min(100, m.completion_percentage || 0)}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          {m.is_mandatory_for_closure ? (
                            <Badge className="bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[10px] flex items-center gap-1 w-fit">
                              <Lock className="h-2.5 w-2.5" />
                              Closure Blocker
                            </Badge>
                          ) : (
                            <span className="text-xs text-slate-500">Optional</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <Badge
                            className={
                              isAccepted
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : isReview
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                : "bg-slate-800 text-slate-400 border-slate-700"
                            }
                          >
                            {m.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedMilestone(m);
                              setVerifyData({
                                decision: "ACCEPTED",
                                verification_notes: m.verification_notes || "",
                              });
                              setShowVerifyModal(true);
                            }}
                            className="h-8 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs"
                          >
                            <UserCheck className="h-3.5 w-3.5 mr-1" />
                            Verify
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

        {/* Modal: New Milestone */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="max-w-lg bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <FileCheck2 className="h-5 w-5 text-emerald-400" />
                Register Research Milestone
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleCreateMilestone} className="space-y-4 pt-2">
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
                  <Label className="text-xs text-slate-400">Milestone Code</Label>
                  <Input
                    placeholder="e.g. MS-DEL-01"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newMilestone.milestone_code}
                    onChange={(e) => setNewMilestone({ ...newMilestone, milestone_code: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Planned Completion Date *</Label>
                  <Input
                    type="date"
                    required
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newMilestone.planned_completion_date}
                    onChange={(e) => setNewMilestone({ ...newMilestone, planned_completion_date: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Milestone Title *</Label>
                <Input
                  required
                  placeholder="e.g. Prototype Benchtop Testing & Sensor Calibration"
                  className="bg-slate-950 border-slate-800 mt-1"
                  value={newMilestone.title}
                  onChange={(e) => setNewMilestone({ ...newMilestone, title: e.target.value })}
                />
              </div>

              <div>
                <Label className="text-xs text-slate-400">Deliverable Reference & Acceptance Criteria</Label>
                <Textarea
                  placeholder="Define verifiable acceptance metrics (e.g. Peer-reviewed report submitted, 95% sensor accuracy demonstrated)..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={3}
                  value={newMilestone.acceptance_criteria}
                  onChange={(e) => setNewMilestone({ ...newMilestone, acceptance_criteria: e.target.value })}
                />
              </div>

              <div className="flex items-center gap-2 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <input
                  type="checkbox"
                  id="mandatoryCheck"
                  checked={newMilestone.is_mandatory_for_closure}
                  onChange={(e) => setNewMilestone({ ...newMilestone, is_mandatory_for_closure: e.target.checked })}
                  className="rounded border-slate-700 text-emerald-600 focus:ring-emerald-500"
                />
                <Label htmlFor="mandatoryCheck" className="text-xs text-slate-300 font-medium cursor-pointer">
                  Mandatory for Project Closure (Project cannot transition to CLOSED until verified)
                </Label>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  {submitting ? "Registering..." : "Save Milestone"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Modal: Verify Milestone */}
        <Dialog open={showVerifyModal} onOpenChange={setShowVerifyModal}>
          <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <UserCheck className="h-5 w-5 text-emerald-400" />
                Independent Milestone Acceptance Review
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleVerifyMilestone} className="space-y-4 pt-2">
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 text-xs">
                <div className="font-semibold text-white">{selectedMilestone?.title}</div>
                <div className="text-slate-400 mt-1">Code: {selectedMilestone?.milestone_code}</div>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Review Decision *</Label>
                <select
                  required
                  className="w-full h-10 px-3 mt-1 rounded-md bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  value={verifyData.decision}
                  onChange={(e) => setVerifyData({ ...verifyData, decision: e.target.value })}
                >
                  <option value="ACCEPTED">ACCEPTED — Deliverable Criteria Satisfied</option>
                  <option value="REJECTED">REJECTED — Resubmission Required</option>
                  <option value="UNDER_REVIEW">UNDER_REVIEW — Additional Evidence Requested</option>
                </select>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Reviewer Verification Notes *</Label>
                <Textarea
                  required
                  placeholder="Record formal assessment of evidence, artifacts, and criteria satisfaction..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={3}
                  value={verifyData.verification_notes}
                  onChange={(e) => setVerifyData({ ...verifyData, verification_notes: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowVerifyModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  {submitting ? "Submitting..." : "Commit Formal Decision"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}
